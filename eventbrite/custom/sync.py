"""
Sync engine for Eventbrite organization events:
Supports initial backfill and fast incremental delta sync via order_by='changed_desc'.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from eventbrite.client import make_request
from eventbrite.custom.db import get_connection, init_db

logger = logging.getLogger("eventbrite-sync")

def parse_event_record(ev: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
    name_text = ev.get("name", {}).get("text") if isinstance(ev.get("name"), dict) else str(ev.get("name") or "")
    summary_text = ev.get("summary") or ""
    start_utc = ev.get("start", {}).get("utc") if isinstance(ev.get("start"), dict) else (ev.get("start") or "")
    end_utc = ev.get("end", {}).get("utc") if isinstance(ev.get("end"), dict) else (ev.get("end") or "")
    timezone_str = ev.get("start", {}).get("timezone") if isinstance(ev.get("start"), dict) else (ev.get("timezone") or "")
    changed_utc = ev.get("changed") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    venue_id = ev.get("venue_id")
    venue_name = None
    venue_city = None
    if isinstance(ev.get("venue"), dict):
        venue_name = ev["venue"].get("name")
        if isinstance(ev["venue"].get("address"), dict):
            venue_city = ev["venue"]["address"].get("city")

    return {
        "id": ev["id"],
        "organization_id": organization_id,
        "name": name_text,
        "summary": summary_text,
        "status": ev.get("status", "unknown"),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "timezone": timezone_str,
        "currency": ev.get("currency", "USD"),
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_city": venue_city,
        "capacity": ev.get("capacity"),
        "url": ev.get("url"),
        "changed_utc": changed_utc,
        "raw_json": json.dumps(ev)
    }

def upsert_events(records: List[Dict[str, Any]], db_file: Optional[Path] = None) -> int:
    if not records:
        return 0
    conn = get_connection(db_file)
    with conn:
        conn.executemany("""
        INSERT INTO events (
            id, organization_id, name, summary, status, start_utc, end_utc,
            timezone, currency, venue_id, venue_name, venue_city, capacity,
            url, changed_utc, raw_json
        ) VALUES (
            :id, :organization_id, :name, :summary, :status, :start_utc, :end_utc,
            :timezone, :currency, :venue_id, :venue_name, :venue_city, :capacity,
            :url, :changed_utc, :raw_json
        )
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            summary=excluded.summary,
            status=excluded.status,
            start_utc=excluded.start_utc,
            end_utc=excluded.end_utc,
            timezone=excluded.timezone,
            currency=excluded.currency,
            venue_id=excluded.venue_id,
            venue_name=coalesce(excluded.venue_name, events.venue_name),
            venue_city=coalesce(excluded.venue_city, events.venue_city),
            capacity=excluded.capacity,
            url=excluded.url,
            changed_utc=excluded.changed_utc,
            raw_json=excluded.raw_json
        """, records)
    conn.close()
    return len(records)

def get_last_sync_utc(organization_id: str, db_file: Optional[Path] = None) -> Optional[str]:
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT last_sync_utc FROM sync_metadata WHERE organization_id = ?", (organization_id,))
    row = cursor.fetchone()
    conn.close()
    return row["last_sync_utc"] if row else None

def record_sync_success(organization_id: str, count: int, sync_time: str, db_file: Optional[Path] = None) -> None:
    conn = get_connection(db_file)
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) as total FROM events WHERE organization_id = ?", (organization_id,))
        total_events = cursor.fetchone()["total"]
        conn.execute("""
        INSERT INTO sync_metadata (organization_id, last_sync_utc, total_events_synced)
        VALUES (?, ?, ?)
        ON CONFLICT(organization_id) DO UPDATE SET
            last_sync_utc=excluded.last_sync_utc,
            total_events_synced=excluded.total_events_synced
        """, (organization_id, sync_time, total_events))
    conn.close()

async def sync_events_for_organization(
    organization_id: str,
    force_full_resync: bool = False,
    db_file: Optional[Path] = None
) -> Dict[str, Any]:
    init_db(db_file)
    last_sync = None if force_full_resync else get_last_sync_utc(organization_id, db_file)
    sync_start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    continuation = None
    total_synced = 0
    is_delta = last_sync is not None

    while True:
        params: Dict[str, Any] = {
            "order_by": "changed_desc" if is_delta else "start_desc",
            "expand": "venue"
        }
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/organizations/{organization_id}/events/", params=params)
        if resp.get("error"):
            return {
                "error": True,
                "message": f"Failed fetching events for organization {organization_id}: {resp.get('error_description') or resp.get('message')}"
            }

        events_data = resp.get("events", [])
        if not events_data:
            break

        records_to_upsert = []
        stop_paging = False

        for ev in events_data:
            rec = parse_event_record(ev, organization_id)
            # If doing delta sync, stop when we encounter an event modified before last_sync
            if is_delta and rec["changed_utc"] < last_sync:
                stop_paging = True
                break
            records_to_upsert.append(rec)

        if records_to_upsert:
            upsert_events(records_to_upsert, db_file)
            total_synced += len(records_to_upsert)

        if stop_paging:
            break

        pagination = resp.get("pagination", {})
        if pagination.get("has_more_items") and pagination.get("continuation"):
            continuation = pagination["continuation"]
        else:
            break

    record_sync_success(organization_id, total_synced, sync_start_time, db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as count FROM events WHERE organization_id = ?", (organization_id,))
    total_in_db = cursor.fetchone()["count"]
    conn.close()

    return {
        "success": True,
        "organization_id": organization_id,
        "sync_type": "delta" if is_delta else "full",
        "events_updated": total_synced,
        "total_cached_events": total_in_db,
        "synced_at_utc": sync_start_time
    }
