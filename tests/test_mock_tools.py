"""
Mock tests for tool execution with HTTP mocked clients.
"""

import unittest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eventbrite.server import mcp

class TestMockTools(unittest.TestCase):
    def setUp(self):
        os.environ["EVENTBRITE_PRIVATE_TOKEN"] = "test-token"
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_mock_attendee_checkin(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertIn("/events/e100/attendees/att1/checkin/", str(request.url))
            self.assertEqual(request.method, "POST")
            return httpx.Response(200, json={"ans": {"checked_in": True}})

        async def run_checkin():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client
                    tool = mcp._tool_manager.get_tool("checkin_attendee")
                    res = await tool.run({"event_id": "e100", "attendee_id": "att1"})
                    self.assertTrue(res.get("ans", {}).get("checked_in"))

        self.loop.run_until_complete(run_checkin())

    def test_mock_create_event_payload_structure(self):
        def handler(request: httpx.Request) -> httpx.Response:
            import json
            self.assertIn("/organizations/org123/events/", str(request.url))
            self.assertEqual(request.method, "POST")
            body = json.loads(request.content)
            self.assertIn("event", body)
            self.assertEqual(body["event"]["name"]["html"], "National Job Fair")
            self.assertEqual(body["event"]["currency"], "USD")
            return httpx.Response(200, json={"id": "new_ev_123", "name": {"text": "National Job Fair"}})

        async def run_create():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client
                    tool = mcp._tool_manager.get_tool("create_event")
                    res = await tool.run({
                        "organization_id": "org123",
                        "name": "National Job Fair",
                        "start_utc": "2026-10-01T14:00:00Z",
                        "end_utc": "2026-10-01T18:00:00Z"
                    })
                    self.assertEqual(res["id"], "new_ev_123")
                    self.assertEqual(res["name"], "National Job Fair")

        self.loop.run_until_complete(run_create())

    def test_mock_create_ticket_class(self):
        def handler(request: httpx.Request) -> httpx.Response:
            import json
            self.assertIn("/events/ev1/ticket_classes/", str(request.url))
            body = json.loads(request.content)
            self.assertEqual(body["ticket_class"]["name"], "VIP Employer Booth")
            self.assertEqual(body["ticket_class"]["cost"], "USD,150000")
            return httpx.Response(200, json={
                "id": "tc_vip",
                "name": "VIP Employer Booth",
                "cost": {"display": "$1,500.00"},
                "free": False
            })

        async def run_tc():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client
                    tool = mcp._tool_manager.get_tool("create_ticket_class")
                    res = await tool.run({
                        "event_id": "ev1",
                        "name": "VIP Employer Booth",
                        "quantity_total": 20,
                        "free": False,
                        "cost_in_cents": 150000
                    })
                    self.assertEqual(res["id"], "tc_vip")
                    self.assertEqual(res["cost"], "$1,500.00")

        self.loop.run_until_complete(run_tc())

    def test_mock_webhook_creation(self):
        def handler(request: httpx.Request) -> httpx.Response:
            import json
            self.assertIn("/organizations/org1/webhooks/", str(request.url))
            body = json.loads(request.content)
            self.assertEqual(body["endpoint_url"], "https://example.com/wh")
            self.assertEqual(body["actions"], "order.placed")
            return httpx.Response(200, json={
                "id": "wh_99",
                "endpoint_url": "https://example.com/wh",
                "actions": "order.placed"
            })

        async def run_wh():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client
                    tool = mcp._tool_manager.get_tool("create_organization_webhook")
                    res = await tool.run({
                        "organization_id": "org1",
                        "endpoint_url": "https://example.com/wh",
                        "actions": "order.placed"
                    })
                    self.assertEqual(res["id"], "wh_99")
                    self.assertEqual(res["endpoint_url"], "https://example.com/wh")

        self.loop.run_until_complete(run_wh())
