"""
Database connection and schema initialization for custom Eventbrite event caching.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Persist cache db inside project directory /root/mcp-servers/eventbrite/data/cache.db
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cache.db"

def get_db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH

def get_connection(db_file: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_file or get_db_path()
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file: Optional[Path] = None) -> None:
    conn = get_connection(db_file)
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            name TEXT NOT NULL,
            summary TEXT,
            status TEXT NOT NULL,
            start_utc TEXT NOT NULL,
            end_utc TEXT NOT NULL,
            timezone TEXT,
            currency TEXT,
            venue_id TEXT,
            venue_name TEXT,
            venue_city TEXT,
            capacity INTEGER,
            url TEXT,
            changed_utc TEXT NOT NULL,
            raw_json TEXT
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_org_start ON events(organization_id, start_utc);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_changed ON events(changed_utc);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_org_city ON events(organization_id, venue_city);")

        conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_metadata (
            organization_id TEXT PRIMARY KEY,
            last_sync_utc TEXT NOT NULL,
            total_events_synced INTEGER DEFAULT 0
        );
        """)
    conn.close()
