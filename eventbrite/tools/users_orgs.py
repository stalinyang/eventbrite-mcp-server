"""
Users, Organizations, Venues, Roles, and Members tools.
"""

from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_user, filter_organization, filter_venue, clean_paginated_response

def register_user_org_tools(mcp: FastMCP):

    @mcp.tool()
    async def get_current_user() -> Dict[str, Any]:
        """Retrieve profile and email details of the authenticated Eventbrite user account."""
        resp = await make_request("GET", "/users/me/")
        return filter_user(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def get_user_by_id(user_id: str) -> Dict[str, Any]:
        """Retrieve public details of an Eventbrite user by user ID."""
        resp = await make_request("GET", f"/users/{user_id}/")
        return filter_user(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_user_organizations() -> Dict[str, Any]:
        """List all organizations that the authenticated user belongs to or manages."""
        resp = await make_request("GET", "/users/me/organizations/")
        return clean_paginated_response(resp, "organizations", filter_organization)

    @mcp.tool()
    async def list_organizations_for_user(user_id: str) -> Dict[str, Any]:
        """List organizations accessible by a specific user ID."""
        resp = await make_request("GET", f"/users/{user_id}/organizations/")
        return clean_paginated_response(resp, "organizations", filter_organization)

    @mcp.tool()
    async def list_organization_members(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List team members and staff associated with an organization."""
        params = {"continuation": continuation} if continuation else None
        return await make_request("GET", f"/organizations/{organization_id}/members/", params=params)

    @mcp.tool()
    async def list_organization_roles(organization_id: str) -> Dict[str, Any]:
        """List permission roles configured in an organization."""
        return await make_request("GET", f"/organizations/{organization_id}/roles/")

    # --- VENUES ---

    @mcp.tool()
    async def get_venue(venue_id: str) -> Dict[str, Any]:
        """Retrieve details of a venue by venue ID (address, capacity, coordinates)."""
        resp = await make_request("GET", f"/venues/{venue_id}/")
        return filter_venue(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_organization_venues(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List all venues configured under an organization."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/organizations/{organization_id}/venues/", params=params)
        return clean_paginated_response(resp, "venues", filter_venue)

    @mcp.tool()
    async def create_venue(
        organization_id: str,
        name: str,
        address_1: str,
        city: str,
        region: str,
        postal_code: str,
        country: str = "US",
        address_2: Optional[str] = None,
        capacity: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new venue (hotel, convention hall, office) under an organization."""
        address: Dict[str, Any] = {
            "address_1": address_1,
            "city": city,
            "region": region,
            "postal_code": postal_code,
            "country": country
        }
        if address_2:
            address["address_2"] = address_2

        payload: Dict[str, Any] = {
            "venue": {
                "name": name,
                "address": address
            }
        }
        if capacity:
            payload["venue"]["capacity"] = capacity

        resp = await make_request("POST", f"/organizations/{organization_id}/venues/", json_data=payload)
        return filter_venue(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def update_venue(
        venue_id: str,
        name: Optional[str] = None,
        address_1: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        capacity: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing venue's details."""
        venue_data: Dict[str, Any] = {}
        if name:
            venue_data["name"] = name
        if capacity:
            venue_data["capacity"] = capacity

        addr_fields = {}
        if address_1:
            addr_fields["address_1"] = address_1
        if city:
            addr_fields["city"] = city
        if region:
            addr_fields["region"] = region
        if postal_code:
            addr_fields["postal_code"] = postal_code
        if country:
            addr_fields["country"] = country

        if addr_fields:
            venue_data["address"] = addr_fields

        resp = await make_request("POST", f"/venues/{venue_id}/", json_data={"venue": venue_data})
        return filter_venue(resp) if not resp.get("error") else resp
