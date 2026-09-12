"""
Tests for FastMCP Eventbrite server.
"""

import unittest
import asyncio
import os
import sys
from pathlib import Path

# Ensure eventbrite package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eventbrite.server import mcp
from eventbrite.client import get_auth_token, get_headers

class TestEventbriteServerStructure(unittest.TestCase):
    def setUp(self):
        os.environ["EVENTBRITE_PRIVATE_TOKEN"] = "test_token_123"

    def test_auth_token_reading(self):
        token = get_auth_token()
        self.assertEqual(token, "test_token_123")
        headers = get_headers()
        self.assertEqual(headers["Authorization"], "Bearer test_token_123")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_tool_count_and_registration(self):
        """Ensure all 84 domain tools are registered on FastMCP."""
        tools = mcp._tool_manager.list_tools()
        self.assertGreaterEqual(len(tools), 80, f"Expected at least 80 tools, found {len(tools)}")
        tool_names = {t.name for t in tools}

        expected_sample_tools = [
            # users_orgs
            "get_current_user", "get_user_by_id", "list_user_organizations",
            "list_organization_members", "list_organization_roles", "create_venue", "update_venue",
            # events
            "get_event", "list_organization_events", "search_events", "create_event", "publish_event",
            "unpublish_event", "cancel_event", "copy_event", "delete_event", "get_event_series",
            # ticketing
            "list_ticket_classes", "list_ticket_classes_for_sale", "create_ticket_class",
            "list_event_inventory_tiers", "list_organization_ticket_groups", "get_ticket_buyer_settings",
            # attendees_orders
            "list_event_attendees", "get_attendee_details", "checkin_attendee",
            "get_order", "list_event_orders", "list_organization_payouts",
            # discounts_webhooks
            "get_discount", "list_organization_discounts", "create_organization_discount",
            "list_organization_webhooks", "create_organization_webhook", "list_event_questions",
            # media_catalog
            "list_categories", "list_formats", "get_media_upload_instructions",
            "get_sales_report", "get_fee_rates", "get_event_display_settings"
        ]

        for exp in expected_sample_tools:
            self.assertIn(exp, tool_names, f"Missing tool: {exp}")

    def test_tool_parameters_exist(self):
        """Check parameter signatures on key tools."""
        create_ev = mcp._tool_manager.get_tool("create_event")
        self.assertIsNotNone(create_ev)
        params = create_ev.parameters.get("properties", {})
        self.assertIn("organization_id", params)
        self.assertIn("name", params)
        self.assertIn("start_utc", params)
        self.assertIn("end_utc", params)

        checkin = mcp._tool_manager.get_tool("checkin_attendee")
        self.assertIsNotNone(checkin)
        params = checkin.parameters.get("properties", {})
        self.assertIn("event_id", params)
        self.assertIn("attendee_id", params)

        create_disc = mcp._tool_manager.get_tool("create_organization_discount")
        self.assertIsNotNone(create_disc)
        params = create_disc.parameters.get("properties", {})
        self.assertIn("code", params)
        self.assertIn("type", params)

if __name__ == "__main__":
    unittest.main()
