"""
Custom FastMCP tools for local SQLite date-range event queries and cache synchronization.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from mcp.server.fastmcp import FastMCP

from eventbrite.custom.db import get_connection, init_db
from eventbrite.custom.sync import sync_events_for_organization, get_last_sync_utc

def register_custom_tools(mcp: FastMCP):

    @mcp.tool()
    async def sync_organization_events(
        organization_id: str,
        force_full_resync: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize events from Eventbrite API into the local SQLite database.
        Runs full backfill if new, or fast incremental delta sync via 'changed_desc'.
        """
        return await sync_events_for_organization(organization_id, force_full_resync=force_full_resync)

    @mcp.tool()
    async def search_organization_events_by_date(
        organization_id: str,
        start_date_utc: str,
        end_date_utc: str,
        city: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
        auto_sync_if_stale_minutes: int = 15,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search organization events within an exact UTC date range (e.g. 2025-01-01T00:00:00Z to 2026-12-31T23:59:59Z).
        Uses local SQLite index with automatic delta sync if cache is older than auto_sync_if_stale_minutes.
        """
        init_db()
        last_sync = get_last_sync_utc(organization_id)

        # Auto-sync if never synced or stale
        needs_sync = False
        if not last_sync:
            needs_sync = True
        elif auto_sync_if_stale_minutes > 0:
            try:
                last_dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - last_dt > timedelta(minutes=auto_sync_if_stale_minutes):
                    needs_sync = True
            except Exception:
                needs_sync = True

        if needs_sync:
            await sync_events_for_organization(organization_id, force_full_resync=(last_sync is None))

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT id, name, summary, status, start_utc, end_utc, timezone, currency,
               venue_id, venue_name, venue_city, capacity, url, changed_utc
        FROM events
        WHERE organization_id = ?
          AND start_utc >= ?
          AND start_utc <= ?
        """
        params: List[Any] = [organization_id, start_date_utc, end_date_utc]

        if city:
            sql += " AND (venue_city LIKE ? OR name LIKE ?)"
            params.extend([f"%{city}%", f"%{city}%"])

        if status and status != "all":
            sql += " AND status = ?"
            params.append(status)

        if query:
            sql += " AND (name LIKE ? OR summary LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        # Count total matches
        count_sql = f"SELECT count(*) as total FROM ({sql})"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()["total"]

        sql += " ORDER BY start_utc ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        events = [dict(row) for row in rows]

        return {
            "organization_id": organization_id,
            "filter": {
                "start_date_utc": start_date_utc,
                "end_date_utc": end_date_utc,
                "city": city,
                "status": status,
                "query": query
            },
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(events)) < total_count
            },
            "events": events
        }

    @mcp.tool()
    async def get_cached_event_statistics(
        organization_id: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve aggregate event statistics (events count by status, by year, and by top cities) from local SQLite cache.
        """
        init_db()
        conn = get_connection()
        cursor = conn.cursor()

        base_filter = "WHERE organization_id = ?"
        params = [organization_id]
        if year:
            base_filter += " AND strftime('%Y', start_utc) = ?"
            params.append(str(year))

        # Total events
        cursor.execute(f"SELECT count(*) as total FROM events {base_filter}", params)
        total = cursor.fetchone()["total"]

        # By status
        cursor.execute(f"SELECT status, count(*) as count FROM events {base_filter} GROUP BY status", params)
        by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

        # By city
        cursor.execute(f"""
            SELECT coalesce(venue_city, 'Unspecified') as city, count(*) as count
            FROM events {base_filter}
            GROUP BY city
            ORDER BY count DESC
            LIMIT 10
        """, params)
        top_cities = {row["city"]: row["count"] for row in cursor.fetchall()}

        # By year
        cursor.execute("""
            SELECT strftime('%Y', start_utc) as y, count(*) as count
            FROM events
            WHERE organization_id = ?
            GROUP BY y
            ORDER BY y DESC
        """, (organization_id,))
        by_year = {row["y"]: row["count"] for row in cursor.fetchall() if row["y"]}

        last_sync = get_last_sync_utc(organization_id)
        conn.close()

        return {
            "organization_id": organization_id,
            "last_synced_utc": last_sync,
            "total_events": total,
            "by_status": by_status,
            "top_cities": top_cities,
            "by_year": by_year
        }
