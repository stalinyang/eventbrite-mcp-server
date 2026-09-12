"""
Coverage test suite testing mock responses for every tool domain in the Eventbrite MCP server.
"""

import unittest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eventbrite.server import mcp

class TestAllToolsCoverage(unittest.TestCase):
    def setUp(self):
        os.environ["EVENTBRITE_PRIVATE_TOKEN"] = "test-token"
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_all_domains_mock_dispatch(self):
        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            # Default payload
            data = {"id": "test_id", "name": "Test Item", "success": True, "address": {"city": "Dallas"}}
            if request.method == "POST" and "/organizations/org1/venues/" in url:
                data = {"id": "test_id", "name": "New Venue", "address": {"city": "Dallas"}}
            elif "/users/me/organizations/" in url:
                data = {"organizations": [{"id": "org1", "name": "Choice Ops", "vertical": "default"}]}
            elif "/users/me/" in url:
                data = {"id": "usr1", "name": "Choice Recruiter", "email": "ops@choice.com"}
            elif "/users/usr1/" in url:
                data = {"id": "usr1", "name": "Choice Recruiter"}
            elif "/organizations/org1/venues/" in url:
                data = {"venues": [{"id": "v1", "name": "Dallas Center", "address": {"city": "Dallas"}}]}
            elif "/venues/v1/" in url:
                data = {"id": "v1", "name": "Dallas Center", "address": {"city": "Dallas"}}
            elif "/events/search/" in url:
                data = {"events": [{"id": "e1", "name": {"text": "Fair"}}]}
            elif "/organizations/org1/events/" in url:
                data = {"events": [{"id": "e1", "name": {"text": "Fair"}}]}
            elif "/events/e1/ticket_classes/" in url:
                data = {"ticket_classes": [{"id": "tc1", "name": "Free Ticket", "free": True}]}
            elif "/events/e1/attendees/" in url:
                data = {"attendees": [{"id": "a1", "profile": {"name": "Attendee 1"}}]}
            elif "/orders/ord1/" in url:
                data = {"id": "ord1", "name": "Order 1"}
            elif "/events/e1/orders/" in url:
                data = {"orders": [{"id": "ord1", "name": "Order 1"}]}
            elif "/categories/" in url:
                data = {"categories": [{"id": "101", "name": "Business & Professional"}]}
            elif "/formats/" in url:
                data = {"formats": [{"id": "1", "name": "Conference"}]}
            elif "/organizations/org1/webhooks/" in url:
                data = {"webhooks": [{"id": "wh1", "endpoint_url": "https://example.com/webhook"}]}
            elif "/pricing/fee_rates" in url:
                data = {"currency": "USD", "fee_percentage": 3.5}
            elif "/reports/sales/" in url:
                data = {"sales": {"gross": 5000}}
            return httpx.Response(200, json=data, request=request)

        async def run_all():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                with patch("eventbrite.client.httpx.AsyncClient") as mock_client_cls:
                    mock_client_cls.return_value.__aenter__.return_value = mock_client

                    async def call_tool(tool_name: str, **kwargs):
                        tool = mcp._tool_manager.get_tool(tool_name)
                        self.assertIsNotNone(tool, f"Tool {tool_name} not found")
                        return await tool.run(kwargs)

                    # Users & Orgs
                    u = await call_tool("get_current_user")
                    self.assertEqual(u["id"], "usr1")
                    ud = await call_tool("get_user_by_id", user_id="usr1")
                    self.assertEqual(ud["id"], "usr1")
                    orgs = await call_tool("list_user_organizations")
                    self.assertEqual(len(orgs["organizations"]), 1)

                    # Venues
                    venues = await call_tool("list_organization_venues", organization_id="org1")
                    self.assertEqual(len(venues["venues"]), 1)
                    v = await call_tool("get_venue", venue_id="v1")
                    self.assertEqual(v["name"], "Dallas Center")
                    new_v = await call_tool("create_venue", organization_id="org1", name="New Venue", address_1="123 Main", city="Dallas", region="TX", postal_code="75001")
                    self.assertEqual(new_v["id"], "test_id")

                    # Events
                    searched = await call_tool("search_events", q="career")
                    self.assertEqual(len(searched["events"]), 1)
                    org_evs = await call_tool("list_organization_events", organization_id="org1")
                    self.assertEqual(len(org_evs["events"]), 1)
                    ev_det = await call_tool("get_event", event_id="e1")
                    self.assertEqual(ev_det["id"], "e1")

                    # Ticketing
                    tcs = await call_tool("list_ticket_classes", event_id="e1")
                    self.assertEqual(len(tcs["ticket_classes"]), 1)
                    tgroups = await call_tool("list_organization_ticket_groups", organization_id="org1")
                    self.assertEqual(tgroups["id"], "test_id")

                    # Attendees & Orders
                    atts = await call_tool("list_event_attendees", event_id="e1")
                    self.assertEqual(len(atts["attendees"]), 1)
                    ord1 = await call_tool("get_order", order_id="ord1")
                    self.assertEqual(ord1["id"], "ord1")
                    ords = await call_tool("list_event_orders", event_id="e1")
                    self.assertEqual(len(ords["orders"]), 1)

                    # Categories & Formats
                    cats = await call_tool("list_categories")
                    self.assertEqual(len(cats["categories"]), 1)
                    fmts = await call_tool("list_formats")
                    self.assertEqual(len(fmts["formats"]), 1)

                    # Webhooks & Reports
                    whs = await call_tool("list_organization_webhooks", organization_id="org1")
                    self.assertEqual(len(whs["webhooks"]), 1)
                    sales = await call_tool("get_sales_report", event_ids="e1")
                    self.assertEqual(sales["sales"]["gross"], 5000)
                    fees = await call_tool("get_fee_rates", country="US", currency="USD")
                    self.assertEqual(fees["currency"], "USD")

        self.loop.run_until_complete(run_all())
