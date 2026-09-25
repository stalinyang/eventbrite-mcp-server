"""
Eventbrite API v3 Model Context Protocol (MCP) Server.
Comprehensive, token-efficient, fast implementation covering all major Eventbrite API v3 resources.
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP

from eventbrite.tools.users_orgs import register_user_org_tools
from eventbrite.tools.events import register_events_tools
from eventbrite.tools.ticketing import register_ticketing_tools
from eventbrite.tools.attendees_orders import register_attendees_orders_tools
from eventbrite.tools.discounts_webhooks import register_discounts_webhooks_tools
from eventbrite.tools.media_catalog import register_media_catalog_tools
from eventbrite.custom.tools import register_custom_tools
import os
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("eventbrite-mcp")

mcp = FastMCP("eventbrite")

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "eventbrite-mcp"})

@mcp.custom_route("/ping", methods=["GET"])
async def ping(request: Request) -> PlainTextResponse:
    return PlainTextResponse("pong")

# Register all domain tools
register_user_org_tools(mcp)
register_events_tools(mcp)
register_ticketing_tools(mcp)
register_attendees_orders_tools(mcp)
register_discounts_webhooks_tools(mcp)
register_media_catalog_tools(mcp)
register_custom_tools(mcp)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Eventbrite MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--host", default=None)
    args, unknown = parser.parse_known_args()

    transport = args.transport or os.environ.get("MCP_TRANSPORT", "stdio")
    port = args.port or int(os.environ.get("PORT", os.environ.get("MCP_PORT", "8003")))
    host = args.host or os.environ.get("MCP_HOST", "127.0.0.1")

    if transport != "stdio":
        mcp.settings.port = port
        mcp.settings.host = host
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
