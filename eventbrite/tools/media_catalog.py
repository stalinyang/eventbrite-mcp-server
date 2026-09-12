"""
Media, Taxonomies, Categories, Formats, and Reports tools.
"""

from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_category, filter_format, clean_paginated_response

def register_media_catalog_tools(mcp: FastMCP):

    # --- CATEGORIES & FORMATS ---

    @mcp.tool()
    async def list_categories(continuation: Optional[str] = None) -> Dict[str, Any]:
        """List standard Eventbrite event categories."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", "/categories/", params=params)
        return clean_paginated_response(resp, "categories", filter_category)

    @mcp.tool()
    async def get_category(category_id: str) -> Dict[str, Any]:
        """Get details and subcategories for a specific category ID."""
        resp = await make_request("GET", f"/categories/{category_id}/")
        return filter_category(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_subcategories(continuation: Optional[str] = None) -> Dict[str, Any]:
        """List Eventbrite subcategories."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", "/subcategories/", params=params)
        return clean_paginated_response(resp, "subcategories", filter_category)

    @mcp.tool()
    async def get_subcategory(subcategory_id: str) -> Dict[str, Any]:
        """Get details for a specific subcategory."""
        resp = await make_request("GET", f"/subcategories/{subcategory_id}/")
        return filter_category(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_formats() -> Dict[str, Any]:
        """List event format types (e.g., Conference, Expo, Seminar, Networking)."""
        resp = await make_request("GET", "/formats/")
        return clean_paginated_response(resp, "formats", filter_format)

    @mcp.tool()
    async def get_format(format_id: str) -> Dict[str, Any]:
        """Get details of a specific event format."""
        resp = await make_request("GET", f"/formats/{format_id}/")
        return filter_format(resp) if not resp.get("error") else resp

    # --- MEDIA ---

    @mcp.tool()
    async def get_media(media_id: str) -> Dict[str, Any]:
        """Retrieve details and download URLs of uploaded media (images, banners)."""
        return await make_request("GET", f"/media/{media_id}/")

    @mcp.tool()
    async def get_media_upload_instructions(type: str = "image-event-logo") -> Dict[str, Any]:
        """
        Get an upload token and S3 post parameters for uploading an image to Eventbrite.
        type: 'image-event-logo', 'image-event-description'
        """
        return await make_request("GET", "/media/upload/", params={"type": type})

    # --- REPORTS & PRICING ---

    @mcp.tool()
    async def get_sales_report(event_ids: str, filter_by: str = "event") -> Dict[str, Any]:
        """
        Retrieve sales report summary for one or more event IDs (comma-separated).
        filter_by: 'event' or 'date'
        """
        return await make_request("GET", "/reports/sales/", params={"event_ids": event_ids, "filter_by": filter_by})

    @mcp.tool()
    async def get_attendees_report(event_ids: str, filter_by: str = "event") -> Dict[str, Any]:
        """Retrieve attendee summary report for one or more event IDs (comma-separated)."""
        return await make_request("GET", "/reports/attendees/", params={"event_ids": event_ids, "filter_by": filter_by})

    @mcp.tool()
    async def get_event_display_settings(event_id: str) -> Dict[str, Any]:
        """Get display settings for an event page (show start/end time, show organizer info, etc.)."""
        return await make_request("GET", f"/events/{event_id}/display_settings/")

    @mcp.tool()
    async def update_event_display_settings(event_id: str, show_start_time: Optional[bool] = None, show_end_time: Optional[bool] = None) -> Dict[str, Any]:
        """Update display settings for an event page."""
        payload: Dict[str, Any] = {}
        if show_start_time is not None:
            payload["show_start_time"] = show_start_time
        if show_end_time is not None:
            payload["show_end_time"] = show_end_time
        return await make_request("POST", f"/events/{event_id}/display_settings/", json_data=payload)

    @mcp.tool()
    async def get_fee_rates(country: str = "US", currency: str = "USD") -> Dict[str, Any]:
        """Get current Eventbrite fee rates and calculation rules for a country and currency."""
        return await make_request("GET", "/pricing/fee_rates", params={"country": country, "currency": currency})
