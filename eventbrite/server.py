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

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("eventbrite-mcp")

mcp = FastMCP("eventbrite")

# Register all domain tools
register_user_org_tools(mcp)
register_events_tools(mcp)
register_ticketing_tools(mcp)
register_attendees_orders_tools(mcp)
register_discounts_webhooks_tools(mcp)
register_media_catalog_tools(mcp)
register_custom_tools(mcp)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
