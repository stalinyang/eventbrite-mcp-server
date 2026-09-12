"""
Eventbrite API v3 Model Context Protocol (MCP) Server.
Provides complete integration for Organizations, Venues, Events, Ticket Classes, Attendees, Orders, and Payouts.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("eventbrite-mcp")

mcp = FastMCP("eventbrite")

BASE_URL = "https://www.eventbriteapi.com/v3"

def get_headers() -> Dict[str, str]:
    token = os.environ.get("EVENTBRITE_PRIVATE_TOKEN") or os.environ.get("EVENTBRITE_API_KEY")
    if not token:
        raise ValueError("EVENTBRITE_PRIVATE_TOKEN environment variable is not set.")
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def make_request(method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = get_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(method, url, headers=headers, params=params, json=json_data)
            if resp.status_code >= 400:
                return {
                    "error": True,
                    "status_code": resp.status_code,
                    "response": resp.text
                }
            return resp.json()
        except httpx.HTTPError as exc:
            return {
                "error": True,
                "message": f"HTTP Exception: {str(exc)}"
            }

# --- 1. USER & ORGANIZATION TOOLS ---

@mcp.tool()
async def get_current_user() -> Dict[str, Any]:
    """Retrieve details of the authenticated Eventbrite user account."""
    return await make_request("GET", "/users/me/")

@mcp.tool()
async def list_user_organizations() -> Dict[str, Any]:
    """List all organizations that the authenticated user belongs to or manages."""
    return await make_request("GET", "/users/me/organizations/")

@mcp.tool()
async def get_organization_venues(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
    """List all venues configured under a specific organization."""
    params = {}
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/organizations/{organization_id}/venues/", params=params)

@mcp.tool()
async def create_venue(organization_id: str, name: str, address_1: str, city: str, region: str, postal_code: str, country: str = "US") -> Dict[str, Any]:
    """Create a new venue (hotel, convention center) under an organization."""
    payload = {
        "venue": {
            "name": name,
            "address": {
                "address_1": address_1,
                "city": city,
                "region": region,
                "postal_code": postal_code,
                "country": country
            }
        }
    }
    return await make_request("POST", f"/organizations/{organization_id}/venues/", json_data=payload)

# --- 2. EVENT MANAGEMENT TOOLS ---

@mcp.tool()
async def list_organization_events(
    organization_id: str,
    status: Optional[str] = "live",
    order_by: str = "start_desc",
    continuation: Optional[str] = None
) -> Dict[str, Any]:
    """
    List events for an organization.
    status options: 'live', 'draft', 'canceled', 'ended', 'all'
    """
    params = {"order_by": order_by}
    if status and status != "all":
        params["status"] = status
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/organizations/{organization_id}/events/", params=params)

@mcp.tool()
async def get_event_details(event_id: str) -> Dict[str, Any]:
    """Get full details for a specific event including venue, ticket availability, and status."""
    return await make_request("GET", f"/events/{event_id}/")

@mcp.tool()
async def create_event(
    organization_id: str,
    name: str,
    start_utc: str,
    end_utc: str,
    timezone: str = "America/Chicago",
    currency: str = "USD",
    summary: Optional[str] = None,
    venue_id: Optional[str] = None,
    capacity: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a draft career fair or event under an organization.
    Timestamps must be ISO 8601 UTC strings: YYYY-MM-DDTHH:MM:SSZ.
    """
    event_data: Dict[str, Any] = {
        "name": {"html": name},
        "start": {"utc": start_utc, "timezone": timezone},
        "end": {"utc": end_utc, "timezone": timezone},
        "currency": currency,
        "listed": True,
        "shareable": True
    }
    if summary:
        event_data["summary"] = summary
    if venue_id:
        event_data["venue_id"] = venue_id
    if capacity:
        event_data["capacity"] = capacity

    return await make_request("POST", f"/organizations/{organization_id}/events/", json_data={"event": event_data})

@mcp.tool()
async def publish_event(event_id: str) -> Dict[str, Any]:
    """Publish a draft event, making it live for registration on Eventbrite."""
    return await make_request("POST", f"/events/{event_id}/publish/")

@mcp.tool()
async def unpublish_event(event_id: str) -> Dict[str, Any]:
    """Unpublish a live event, taking it offline."""
    return await make_request("POST", f"/events/{event_id}/unpublish/")

# --- 3. TICKETING & INVENTORY TOOLS ---

@mcp.tool()
async def list_ticket_classes(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
    """List ticket classes (e.g., Job Seeker Free Admission, VIP Early Access, Employer Booth) for an event."""
    params = {}
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/events/{event_id}/ticket_classes/", params=params)

@mcp.tool()
async def create_ticket_class(
    event_id: str,
    name: str,
    quantity_total: int,
    free: bool = True,
    cost_in_cents: int = 0,
    currency: str = "USD",
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a ticket class for an event (free ticket or paid package)."""
    ticket_data: Dict[str, Any] = {
        "name": name,
        "quantity_total": quantity_total,
        "free": free
    }
    if not free and cost_in_cents > 0:
        ticket_data["cost"] = f"{currency},{cost_in_cents}"
    if description:
        ticket_data["description"] = description

    return await make_request("POST", f"/events/{event_id}/ticket_classes/", json_data={"ticket_class": ticket_data})

@mcp.tool()
async def get_ticket_inventory_summary(event_id: str) -> Dict[str, Any]:
    """Retrieve real-time capacity, tickets sold, and inventory counts for an event."""
    return await make_request("GET", f"/events/{event_id}/capacity_tier/")

# --- 4. ATTENDEES & ORDERS TOOLS ---

@mcp.tool()
async def list_event_attendees(
    event_id: str,
    status: str = "attending",
    changed_since: Optional[str] = None,
    continuation: Optional[str] = None
) -> Dict[str, Any]:
    """
    List attendees registered for an event with profile information and survey answers.
    status: 'attending', 'not_attending', 'unpaid'
    """
    params = {"status": status}
    if changed_since:
        params["changed_since"] = changed_since
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/events/{event_id}/attendees/", params=params)

@mcp.tool()
async def get_attendee_details(event_id: str, attendee_id: str) -> Dict[str, Any]:
    """Retrieve detailed attendee profile, custom question responses, and barcode."""
    return await make_request("GET", f"/events/{event_id}/attendees/{attendee_id}/")

@mcp.tool()
async def checkin_attendee(event_id: str, attendee_id: str) -> Dict[str, Any]:
    """Check in an attendee at the career fair venue."""
    return await make_request("POST", f"/events/{event_id}/attendees/{attendee_id}/checkin/")

@mcp.tool()
async def list_event_orders(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve ticket orders and financial summaries for an event."""
    params = {}
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/events/{event_id}/orders/", params=params)

# --- 5. FINANCIALS & PAYOUTS ---

@mcp.tool()
async def list_organization_payouts(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
    """List financial payouts and transfers for an organization."""
    params = {}
    if continuation:
        params["continuation"] = continuation
    return await make_request("GET", f"/organizations/{organization_id}/payouts/", params=params)

if __name__ == "__main__":
    mcp.run(transport="stdio")
