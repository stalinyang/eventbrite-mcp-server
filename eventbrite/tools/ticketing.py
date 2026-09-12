"""
Ticket Classes, Inventory Tiers, Ticket Groups, and Checkout Settings tools.
"""

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_ticket_class, clean_paginated_response

def register_ticketing_tools(mcp: FastMCP):

    # --- TICKET CLASSES ---

    @mcp.tool()
    async def list_ticket_classes(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List all ticket classes (admissions, VIP, booth packages) for an event."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/events/{event_id}/ticket_classes/", params=params)
        return clean_paginated_response(resp, "ticket_classes", filter_ticket_class)

    @mcp.tool()
    async def list_ticket_classes_for_sale(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List currently on-sale ticket classes for an event."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/events/{event_id}/ticket_classes_for_sale/", params=params)
        return clean_paginated_response(resp, "ticket_classes", filter_ticket_class)

    @mcp.tool()
    async def get_ticket_class(event_id: str, ticket_class_id: str) -> Dict[str, Any]:
        """Get details of a specific ticket class."""
        resp = await make_request("GET", f"/events/{event_id}/ticket_classes/{ticket_class_id}/")
        return filter_ticket_class(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def create_ticket_class(
        event_id: str,
        name: str,
        quantity_total: int,
        free: bool = True,
        cost_in_cents: int = 0,
        currency: str = "USD",
        description: Optional[str] = None,
        minimum_quantity: int = 1,
        maximum_quantity: int = 10
    ) -> Dict[str, Any]:
        """Create a ticket class for an event (free admission or paid tier)."""
        ticket_data: Dict[str, Any] = {
            "name": name,
            "quantity_total": quantity_total,
            "free": free,
            "minimum_quantity": minimum_quantity,
            "maximum_quantity": maximum_quantity
        }
        if not free and cost_in_cents > 0:
            ticket_data["cost"] = f"{currency},{cost_in_cents}"
        if description:
            ticket_data["description"] = description

        resp = await make_request("POST", f"/events/{event_id}/ticket_classes/", json_data={"ticket_class": ticket_data})
        return filter_ticket_class(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def update_ticket_class(
        event_id: str,
        ticket_class_id: str,
        name: Optional[str] = None,
        quantity_total: Optional[int] = None,
        cost_in_cents: Optional[int] = None,
        currency: str = "USD",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing ticket class."""
        ticket_data: Dict[str, Any] = {}
        if name:
            ticket_data["name"] = name
        if quantity_total is not None:
            ticket_data["quantity_total"] = quantity_total
        if cost_in_cents is not None:
            ticket_data["cost"] = f"{currency},{cost_in_cents}"
        if description:
            ticket_data["description"] = description

        resp = await make_request("POST", f"/events/{event_id}/ticket_classes/{ticket_class_id}/", json_data={"ticket_class": ticket_data})
        return filter_ticket_class(resp) if not resp.get("error") else resp

    # --- INVENTORY TIERS ---

    @mcp.tool()
    async def list_event_inventory_tiers(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List inventory tiers configured for an event."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/events/{event_id}/inventory_tiers/", params=params)

    @mcp.tool()
    async def get_event_inventory_tier(event_id: str, inventory_tier_id: str) -> Dict[str, Any]:
        """Get details of a specific inventory tier."""
        return await make_request("GET", f"/events/{event_id}/inventory_tiers/{inventory_tier_id}/")

    @mcp.tool()
    async def create_event_inventory_tier(
        event_id: str,
        name: str,
        quantity_total: int,
        count_against_event_capacity: bool = True
    ) -> Dict[str, Any]:
        """Create a new inventory tier for an event."""
        payload = {
            "inventory_tier": {
                "name": name,
                "quantity_total": quantity_total,
                "count_against_event_capacity": count_against_event_capacity
            }
        }
        return await make_request("POST", f"/events/{event_id}/inventory_tiers/", json_data=payload)

    @mcp.tool()
    async def update_event_inventory_tier(
        event_id: str,
        inventory_tier_id: str,
        name: Optional[str] = None,
        quantity_total: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing inventory tier."""
        tier_data: Dict[str, Any] = {}
        if name:
            tier_data["name"] = name
        if quantity_total is not None:
            tier_data["quantity_total"] = quantity_total
        return await make_request("POST", f"/events/{event_id}/inventory_tiers/{inventory_tier_id}/", json_data={"inventory_tier": tier_data})

    @mcp.tool()
    async def delete_event_inventory_tier(event_id: str, inventory_tier_id: str) -> Dict[str, Any]:
        """Delete an inventory tier from an event."""
        return await make_request("DELETE", f"/events/{event_id}/inventory_tiers/{inventory_tier_id}/")

    # --- TICKET GROUPS ---

    @mcp.tool()
    async def list_organization_ticket_groups(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List ticket groups configured under an organization."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/organizations/{organization_id}/ticket_groups/", params=params)

    @mcp.tool()
    async def get_ticket_group(ticket_group_id: str) -> Dict[str, Any]:
        """Retrieve details of a ticket group."""
        return await make_request("GET", f"/ticket_groups/{ticket_group_id}/")

    @mcp.tool()
    async def create_organization_ticket_group(
        organization_id: str,
        name: str,
        status: str = "live",
        ticket_class_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a ticket group under an organization."""
        payload: Dict[str, Any] = {
            "ticket_group": {
                "name": name,
                "status": status
            }
        }
        if ticket_class_ids:
            payload["ticket_group"]["ticket_class_ids"] = ticket_class_ids
        return await make_request("POST", f"/organizations/{organization_id}/ticket_groups/", json_data=payload)

    @mcp.tool()
    async def update_ticket_group(ticket_group_id: str, name: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Update a ticket group."""
        group_data: Dict[str, Any] = {}
        if name:
            group_data["name"] = name
        if status:
            group_data["status"] = status
        return await make_request("POST", f"/ticket_groups/{ticket_group_id}/", json_data={"ticket_group": group_data})

    @mcp.tool()
    async def delete_ticket_group(ticket_group_id: str) -> Dict[str, Any]:
        """Delete a ticket group."""
        return await make_request("DELETE", f"/ticket_groups/{ticket_group_id}/")

    # --- CHECKOUT BUYER SETTINGS ---

    @mcp.tool()
    async def get_ticket_buyer_settings(event_id: str) -> Dict[str, Any]:
        """Get ticket checkout buyer settings for an event."""
        return await make_request("GET", f"/events/{event_id}/ticket_buyer_settings/")

    @mcp.tool()
    async def update_ticket_buyer_settings(
        event_id: str,
        refund_policy: Optional[str] = None,
        checkout_time_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update checkout settings (refund policy, checkout time limit) for an event."""
        payload: Dict[str, Any] = {}
        if refund_policy:
            payload["refund_policy"] = refund_policy
        if checkout_time_limit is not None:
            payload["checkout_time_limit"] = checkout_time_limit
        return await make_request("POST", f"/events/{event_id}/ticket_buyer_settings/", json_data={"ticket_buyer_settings": payload})
