"""
Attendees, Orders, Check-in, and Financials tools.
"""

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_attendee, filter_order, clean_paginated_response

def register_attendees_orders_tools(mcp: FastMCP):

    @mcp.tool()
    async def list_event_attendees(
        event_id: str,
        status: Optional[str] = "attending",
        changed_since: Optional[str] = None,
        continuation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List attendees registered for an event with profile, barcode, and answer fields.
        status options: 'attending', 'not_attending', 'unpaid'
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if changed_since:
            params["changed_since"] = changed_since
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/events/{event_id}/attendees/", params=params)
        return clean_paginated_response(resp, "attendees", filter_attendee)

    @mcp.tool()
    async def list_organization_attendees(
        organization_id: str,
        status: Optional[str] = "attending",
        changed_since: Optional[str] = None,
        continuation: Optional[str] = None
    ) -> Dict[str, Any]:
        """List attendees across all events in an organization."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if changed_since:
            params["changed_since"] = changed_since
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/organizations/{organization_id}/attendees/", params=params)
        return clean_paginated_response(resp, "attendees", filter_attendee)

    @mcp.tool()
    async def get_attendee_details(event_id: str, attendee_id: str) -> Dict[str, Any]:
        """Retrieve full attendee profile, barcode, and custom question answers."""
        resp = await make_request("GET", f"/events/{event_id}/attendees/{attendee_id}/")
        return filter_attendee(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def checkin_attendee(event_id: str, attendee_id: str) -> Dict[str, Any]:
        """Check in an attendee at the event."""
        return await make_request("POST", f"/events/{event_id}/attendees/{attendee_id}/checkin/")

    # --- ORDERS ---

    @mcp.tool()
    async def get_order(order_id: str) -> Dict[str, Any]:
        """Retrieve details of an order including purchaser info, status, and financial totals."""
        resp = await make_request("GET", f"/orders/{order_id}/")
        return filter_order(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_event_orders(
        event_id: str,
        status: Optional[str] = None,
        changed_since: Optional[str] = None,
        continuation: Optional[str] = None
    ) -> Dict[str, Any]:
        """List ticket orders and buyer profiles for a specific event."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if changed_since:
            params["changed_since"] = changed_since
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/events/{event_id}/orders/", params=params)
        return clean_paginated_response(resp, "orders", filter_order)

    @mcp.tool()
    async def list_organization_orders(
        organization_id: str,
        status: Optional[str] = None,
        changed_since: Optional[str] = None,
        continuation: Optional[str] = None
    ) -> Dict[str, Any]:
        """List orders across all events in an organization."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if changed_since:
            params["changed_since"] = changed_since
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/organizations/{organization_id}/orders/", params=params)
        return clean_paginated_response(resp, "orders", filter_order)

    @mcp.tool()
    async def list_user_orders(user_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List ticket purchase orders made by a specific user account."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/users/{user_id}/orders/", params=params)
        return clean_paginated_response(resp, "orders", filter_order)

    # --- FINANCIALS & PAYOUTS ---

    @mcp.tool()
    async def list_organization_payouts(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List financial payouts and bank transfers for an organization."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/organizations/{organization_id}/payouts/", params=params)
