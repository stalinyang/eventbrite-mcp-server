"""
Tests for custom local event cache, SQLite sync, and date-range queries.
"""

import unittest
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eventbrite.server import mcp
from eventbrite.custom.db import init_db, get_connection
from eventbrite.custom.sync import sync_events_for_organization, get_last_sync_utc

class TestCustomEventCache(unittest.TestCase):
    def setUp(self):
        os.environ["EVENTBRITE_PRIVATE_TOKEN"] = "test-token"
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = Path(self.tmp_dir.name) / "test_cache.db"
        init_db(self.test_db_path)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        self.tmp_dir.cleanup()

    def test_sync_and_date_search(self):
        events_page = [
            {
                "id": "ev_2025_01",
                "name": {"text": "Dallas Career Fair 2025"},
                "summary": "Join top employers in Dallas",
                "status": "live",
                "start": {"utc": "2025-03-15T14:00:00Z", "timezone": "America/Chicago"},
                "end": {"utc": "2025-03-15T18:00:00Z", "timezone": "America/Chicago"},
                "changed": "2025-01-10T10:00:00Z",
                "venue": {
                    "id": "v_dallas",
                    "name": "Dallas Convention Center",
                    "address": {"city": "Dallas"}
                }
            },
            {
                "id": "ev_2026_01",
                "name": {"text": "Houston Job Fair 2026"},
                "summary": "Top tech and healthcare careers",
                "status": "live",
                "start": {"utc": "2026-05-20T14:00:00Z", "timezone": "America/Chicago"},
                "end": {"utc": "2026-05-20T18:00:00Z", "timezone": "America/Chicago"},
                "changed": "2026-01-15T12:00:00Z",
                "venue": {
                    "id": "v_houston",
                    "name": "Houston Center",
                    "address": {"city": "Houston"}
                }
            },
            {
                "id": "ev_2024_01",
                "name": {"text": "Austin Job Fair 2024"},
                "summary": "2024 hiring expo",
                "status": "ended",
                "start": {"utc": "2024-06-10T14:00:00Z", "timezone": "America/Chicago"},
                "end": {"utc": "2024-06-10T18:00:00Z", "timezone": "America/Chicago"},
                "changed": "2024-06-11T12:00:00Z",
                "venue": {
                    "id": "v_austin",
                    "name": "Austin Expo",
                    "address": {"city": "Austin"}
                }
            }
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "events": events_page,
                "pagination": {"has_more_items": False}
            })

        async def run_test():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client
                    with patch("eventbrite.custom.tools.get_connection", lambda: get_connection(self.test_db_path)):
                        with patch("eventbrite.custom.tools.init_db", lambda: init_db(self.test_db_path)):
                            with patch("eventbrite.custom.tools.get_last_sync_utc", lambda org_id: get_last_sync_utc(org_id, self.test_db_path)):
                                with patch("eventbrite.custom.tools.sync_events_for_organization", lambda org_id, force_full_resync=False: sync_events_for_organization(org_id, force_full_resync=force_full_resync, db_file=self.test_db_path)):
                                    
                                    # 1. First search triggers auto-sync
                                    search_tool = mcp._tool_manager.get_tool("search_organization_events_by_date")
                                    res = await search_tool.run({
                                        "organization_id": "org_choice",
                                        "start_date_utc": "2025-01-01T00:00:00Z",
                                        "end_date_utc": "2026-12-31T23:59:59Z"
                                    })
                                    
                                    self.assertEqual(res["pagination"]["total"], 2)
                                    event_ids = [e["id"] for e in res["events"]]
                                    self.assertIn("ev_2025_01", event_ids)
                                    self.assertIn("ev_2026_01", event_ids)
                                    self.assertNotIn("ev_2024_01", event_ids)

                                    # 2. Filter by city
                                    dallas_res = await search_tool.run({
                                        "organization_id": "org_choice",
                                        "start_date_utc": "2025-01-01T00:00:00Z",
                                        "end_date_utc": "2026-12-31T23:59:59Z",
                                        "city": "Dallas"
                                    })
                                    self.assertEqual(dallas_res["pagination"]["total"], 1)
                                    self.assertEqual(dallas_res["events"][0]["id"], "ev_2025_01")

                                    # 3. Statistics tool
                                    stats_tool = mcp._tool_manager.get_tool("get_cached_event_statistics")
                                    stats = await stats_tool.run({
                                        "organization_id": "org_choice"
                                    })
                                    self.assertEqual(stats["total_events"], 3)
                                    self.assertEqual(stats["by_status"]["live"], 2)
                                    self.assertEqual(stats["by_status"]["ended"], 1)
                                    self.assertIn("Dallas", stats["top_cities"])

        self.loop.run_until_complete(run_test())

if __name__ == "__main__":
    unittest.main()
