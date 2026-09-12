import os
import sys
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger("eventbrite-client")

BASE_URL = "https://www.eventbriteapi.com/v3"

def get_auth_token() -> str:
    token = os.environ.get("EVENTBRITE_PRIVATE_TOKEN") or os.environ.get("EVENTBRITE_API_KEY")
    if not token:
        raise ValueError("EVENTBRITE_PRIVATE_TOKEN or EVENTBRITE_API_KEY environment variable is not set.")
    return token.strip()

def get_headers(extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers

async def make_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = get_headers()
    
    # Filter out None values in params
    clean_params = None
    if params:
        clean_params = {k: v for k, v in params.items() if v is not None}
        
    try:
        if client:
            resp = await client.request(method, url, headers=headers, params=clean_params, json=json_data)
        else:
            async with httpx.AsyncClient(timeout=30.0) as local_client:
                resp = await local_client.request(method, url, headers=headers, params=clean_params, json=json_data)
        
        if resp.status_code >= 400:
            try:
                err_json = resp.json()
                return {
                    "error": True,
                    "status_code": resp.status_code,
                    "error_code": err_json.get("error", "UNKNOWN_ERROR"),
                    "error_description": err_json.get("error_description", resp.text)
                }
            except Exception:
                return {
                    "error": True,
                    "status_code": resp.status_code,
                    "message": resp.text
                }
        
        if resp.status_code == 204 or not resp.content:
            return {"success": True, "status_code": resp.status_code}
            
        return resp.json()
    except httpx.HTTPError as exc:
        return {
            "error": True,
            "message": f"HTTP Exception: {str(exc)}"
        }
