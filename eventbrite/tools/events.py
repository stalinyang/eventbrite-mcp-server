"""
Event Management, Publishing, Schedules, Series, and Teams tools.
"""

from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_event, clean_paginated_response

def register_events_tools(mcp: FastMCP):

    @mcp.tool()
    async def get_event(event_id: str) -> Dict[str, Any]:
        """Get details for a specific event including status, schedule, venue, and capacity."""
        resp = await make_request("GET", f"/events/{event_id}/")
        return filter_event(resp) if not resp.get("error") else resp

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
        params: Dict[str, Any] = {"order_by": order_by}
        if status and status != "all":
            params["status"] = status
        if continuation:
            params["continuation"] = continuation
        resp = await make_request("GET", f"/organizations/{organization_id}/events/", params=params)
        return clean_paginated_response(resp, "events", filter_event)

    @mcp.tool()
    async def list_venue_events(venue_id: str, status: Optional[str] = "live", continuation: Optional[str] = None) -> Dict[str, Any]:
        """List events scheduled at a specific venue."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if continuation:
            params["continuation"] = continuation
        resp = await make_request("GET", f"/venues/{venue_id}/events/", params=params)
        return clean_paginated_response(resp, "events", filter_event)

    @mcp.tool()
    async def search_events(q: Optional[str] = None, location_address: Optional[str] = None, location_within: Optional[str] = "50mi", continuation: Optional[str] = None) -> Dict[str, Any]:
        """Search public events by keyword, location, or distance."""
        params: Dict[str, Any] = {}
        if q:
            params["q"] = q
        if location_address:
            params["location.address"] = location_address
            params["location.within"] = location_within
        if continuation:
            params["continuation"] = continuation
        resp = await make_request("GET", "/events/search/", params=params)
        return clean_paginated_response(resp, "events", filter_event)

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
        capacity: Optional[int] = None,
        online_event: bool = False,
        listed: bool = True,
        shareable: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new draft event under an organization.
        Timestamps must be UTC strings in format: YYYY-MM-DDTHH:MM:SSZ
        """
        event_payload: Dict[str, Any] = {
            "name": {"html": name},
            "start": {"utc": start_utc, "timezone": timezone},
            "end": {"utc": end_utc, "timezone": timezone},
            "currency": currency,
            "online_event": online_event,
            "listed": listed,
            "shareable": shareable
        }
        if summary:
            event_payload["summary"] = summary
        if venue_id:
            event_payload["venue_id"] = venue_id
        if capacity:
            event_payload["capacity"] = capacity

        resp = await make_request("POST", f"/organizations/{organization_id}/events/", json_data={"event": event_payload})
        return filter_event(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def update_event(
        event_id: str,
        name: Optional[str] = None,
        start_utc: Optional[str] = None,
        end_utc: Optional[str] = None,
        timezone: Optional[str] = None,
        summary: Optional[str] = None,
        venue_id: Optional[str] = None,
        capacity: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing event's details."""
        event_payload: Dict[str, Any] = {}
        if name:
            event_payload["name"] = {"html": name}
        if start_utc and timezone:
            event_payload["start"] = {"utc": start_utc, "timezone": timezone}
        if end_utc and timezone:
            event_payload["end"] = {"utc": end_utc, "timezone": timezone}
        if summary:
            event_payload["summary"] = summary
        if venue_id:
            event_payload["venue_id"] = venue_id
        if capacity:
            event_payload["capacity"] = capacity

        resp = await make_request("POST", f"/events/{event_id}/", json_data={"event": event_payload})
        return filter_event(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def publish_event(event_id: str) -> Dict[str, Any]:
        """Publish a draft event, making it live for attendee registrations."""
        return await make_request("POST", f"/events/{event_id}/publish/")

    @mcp.tool()
    async def unpublish_event(event_id: str) -> Dict[str, Any]:
        """Unpublish a live event, taking it offline."""
        return await make_request("POST", f"/events/{event_id}/unpublish/")

    @mcp.tool()
    async def cancel_event(event_id: str) -> Dict[str, Any]:
        """Cancel an event on Eventbrite."""
        return await make_request("POST", f"/events/{event_id}/cancel/")

    @mcp.tool()
    async def copy_event(event_id: str) -> Dict[str, Any]:
        """Clone/copy an existing event into a new draft event."""
        resp = await make_request("POST", f"/events/{event_id}/copy/")
        return filter_event(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def delete_event(event_id: str) -> Dict[str, Any]:
        """Delete an event by ID."""
        return await make_request("DELETE", f"/events/{event_id}/")

    @mcp.tool()
    async def get_event_description(event_id: str) -> Dict[str, Any]:
        """Get the full description HTML and text for an event."""
        return await make_request("GET", f"/events/{event_id}/description/")

    @mcp.tool()
    async def get_event_capacity_tier(event_id: str) -> Dict[str, Any]:
        """Get capacity configuration and tier count for an event."""
        return await make_request("GET", f"/events/{event_id}/capacity_tier/")

    @mcp.tool()
    async def update_event_capacity_tier(event_id: str, capacity_total: int) -> Dict[str, Any]:
        """Update total capacity limit for an event."""
        return await make_request("POST", f"/events/{event_id}/capacity_tier/", json_data={"capacity_tier": {"capacity_total": capacity_total}})

    # --- SERIES & RECURRENCE ---

    @mcp.tool()
    async def get_event_series(event_series_id: str) -> Dict[str, Any]:
        """Get information about an event series."""
        return await make_request("GET", f"/series/{event_series_id}/")

    @mcp.tool()
    async def list_series_events(event_series_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List individual event occurrences belonging to an event series."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/series/{event_series_id}/events/", params=params)
        return clean_paginated_response(resp, "events", filter_event)

    @mcp.tool()
    async def create_event_schedule(
        event_series_id: str,
        occurrence_duration_seconds: int,
        recurrence_rule: str
    ) -> Dict[str, Any]:
        """
        Create a recurring event schedule.
        recurrence_rule: iCalendar RRULE format (e.g. 'FREQ=WEEKLY;COUNT=10')
        """
        payload = {
            "schedule": {
                "occurrence_duration": occurrence_duration_seconds,
                "recurrence_rule": recurrence_rule
            }
        }
        return await make_request("POST", f"/series/{event_series_id}/schedules/", json_data=payload)

    # --- TEAMS ---

    @mcp.tool()
    async def list_event_teams(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List group registration teams for an event."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/events/{event_id}/teams/", params=params)

    @mcp.tool()
    async def get_event_team(event_id: str, team_id: str) -> Dict[str, Any]:
        """Retrieve details of a specific team in an event."""
        return await make_request("GET", f"/events/{event_id}/teams/{team_id}/")

    @mcp.tool()
    async def list_event_team_attendees(event_id: str, team_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List attendees who belong to a specific team."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/events/{event_id}/teams/{team_id}/attendees/", params=params)

    @mcp.tool()
    async def create_event_team(event_id: str, name: str) -> Dict[str, Any]:
        """Create a new team for an event."""
        return await make_request("POST", f"/events/{event_id}/teams/", json_data={"team": {"name": name}})
