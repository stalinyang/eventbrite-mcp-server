"""
Discounts, Webhooks, Questions, and Canned Questions tools.
"""

from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
from eventbrite.client import make_request
from eventbrite.utils import filter_discount, filter_webhook, filter_question, clean_paginated_response

def register_discounts_webhooks_tools(mcp: FastMCP):

    # --- DISCOUNTS & ACCESS CODES ---

    @mcp.tool()
    async def get_discount(discount_id: str) -> Dict[str, Any]:
        """Get details of a specific promotional discount or access code."""
        resp = await make_request("GET", f"/discounts/{discount_id}/")
        return filter_discount(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def list_organization_discounts(
        organization_id: str,
        scope: Optional[str] = "event",
        code: Optional[str] = None,
        continuation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List promotional discounts and access codes under an organization.
        scope: 'event' or 'organization'
        """
        params: Dict[str, Any] = {}
        if scope:
            params["scope"] = scope
        if code:
            params["code"] = code
        if continuation:
            params["continuation"] = continuation

        resp = await make_request("GET", f"/organizations/{organization_id}/discounts/", params=params)
        return clean_paginated_response(resp, "discounts", filter_discount)

    @mcp.tool()
    async def create_organization_discount(
        organization_id: str,
        code: str,
        type: str,
        value: Optional[float] = None,
        amount_off: Optional[str] = None,
        percent_off: Optional[str] = None,
        event_id: Optional[str] = None,
        ticket_class_ids: Optional[List[str]] = None,
        quantity_available: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a discount or access code for an organization or event.
        type: 'access', 'coded', 'hold', 'public'
        """
        discount_data: Dict[str, Any] = {
            "code": code,
            "type": type
        }
        if amount_off:
            discount_data["amount_off"] = amount_off
        elif percent_off:
            discount_data["percent_off"] = percent_off
        elif value is not None:
            discount_data["value"] = value

        if event_id:
            discount_data["event_id"] = event_id
        if ticket_class_ids:
            discount_data["ticket_class_ids"] = ticket_class_ids
        if quantity_available is not None:
            discount_data["quantity_available"] = quantity_available
        if start_date:
            discount_data["start_date"] = start_date
        if end_date:
            discount_data["end_date"] = end_date

        resp = await make_request("POST", f"/organizations/{organization_id}/discounts/", json_data={"discount": discount_data})
        return filter_discount(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def update_discount(
        discount_id: str,
        code: Optional[str] = None,
        amount_off: Optional[str] = None,
        percent_off: Optional[str] = None,
        quantity_available: Optional[int] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing discount or promotional code."""
        discount_data: Dict[str, Any] = {}
        if code:
            discount_data["code"] = code
        if amount_off:
            discount_data["amount_off"] = amount_off
        if percent_off:
            discount_data["percent_off"] = percent_off
        if quantity_available is not None:
            discount_data["quantity_available"] = quantity_available
        if end_date:
            discount_data["end_date"] = end_date

        resp = await make_request("POST", f"/discounts/{discount_id}/", json_data={"discount": discount_data})
        return filter_discount(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def delete_discount(discount_id: str) -> Dict[str, Any]:
        """Delete a discount code."""
        return await make_request("DELETE", f"/discounts/{discount_id}/")

    # --- WEBHOOKS ---

    @mcp.tool()
    async def list_organization_webhooks(organization_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List active webhooks configured for an organization."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/organizations/{organization_id}/webhooks/", params=params)
        return clean_paginated_response(resp, "webhooks", filter_webhook)

    @mcp.tool()
    async def list_user_webhooks(continuation: Optional[str] = None) -> Dict[str, Any]:
        """List webhooks configured on the current user account."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", "/webhooks/", params=params)
        return clean_paginated_response(resp, "webhooks", filter_webhook)

    @mcp.tool()
    async def create_organization_webhook(
        organization_id: str,
        endpoint_url: str,
        actions: str,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a webhook endpoint for an organization.
        actions: comma-separated list like 'order.placed,attendee.checked_in,event.published'
        """
        payload: Dict[str, Any] = {
            "endpoint_url": endpoint_url,
            "actions": actions
        }
        if event_id:
            payload["event_id"] = event_id
        resp = await make_request("POST", f"/organizations/{organization_id}/webhooks/", json_data=payload)
        return filter_webhook(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def delete_webhook(webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook by ID."""
        return await make_request("DELETE", f"/webhooks/{webhook_id}/")

    # --- QUESTIONS & SURVEYS ---

    @mcp.tool()
    async def list_event_questions(event_id: str, continuation: Optional[str] = None) -> Dict[str, Any]:
        """List custom registration questions configured for an event."""
        params = {"continuation": continuation} if continuation else None
        resp = await make_request("GET", f"/events/{event_id}/questions/", params=params)
        return clean_paginated_response(resp, "questions", filter_question)

    @mcp.tool()
    async def get_event_question(event_id: str, question_id: str) -> Dict[str, Any]:
        """Retrieve details of a registration question."""
        resp = await make_request("GET", f"/events/{event_id}/questions/{question_id}/")
        return filter_question(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def create_event_question(
        event_id: str,
        question_text: str,
        type: str,
        required: bool = False,
        choices: Optional[List[str]] = None,
        ticket_classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a registration question for an event.
        type: 'text', 'multichoice', 'checkbox', 'radio'
        """
        question_payload: Dict[str, Any] = {
            "question": {"html": question_text},
            "type": type,
            "required": required
        }
        if choices:
            question_payload["choices"] = [{"answer": {"html": c}} for c in choices]
        if ticket_classes:
            question_payload["ticket_classes"] = ticket_classes

        resp = await make_request("POST", f"/events/{event_id}/questions/", json_data={"question": question_payload})
        return filter_question(resp) if not resp.get("error") else resp

    @mcp.tool()
    async def delete_event_question(event_id: str, question_id: str) -> Dict[str, Any]:
        """Delete a custom registration question."""
        return await make_request("DELETE", f"/events/{event_id}/questions/{question_id}/")

    @mcp.tool()
    async def list_event_canned_questions(event_id: str) -> Dict[str, Any]:
        """List standard canned questions (Job Title, Company, Address, etc.) for an event."""
        return await make_request("GET", f"/events/{event_id}/canned_questions/")
