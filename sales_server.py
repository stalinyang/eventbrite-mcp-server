"""
Eventbrite Sales MCP Server for sales-amy.
Strictly limits exposed capabilities to a single read-only search tool:
- search_organization_events_by_date
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP
from eventbrite.custom.tools import register_custom_tools

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("eventbrite-sales-mcp")

mcp = FastMCP("eventbrite")

# Register custom date-search tool, then filter to only search_organization_events_by_date
register_custom_tools(mcp)

# Keep only search_organization_events_by_date
tools_to_remove = [name for name in mcp._tool_manager._tools.keys() if name != "search_organization_events_by_date"]
for name in tools_to_remove:
    del mcp._tool_manager._tools[name]

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
