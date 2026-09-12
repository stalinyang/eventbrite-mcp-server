# Eventbrite Model Context Protocol (MCP) Server

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![MCP Spec](https://img.shields.io/badge/MCP-1.0.0%2B-brightgreen.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-18%20passed-success.svg)](tests/)

A production-ready Model Context Protocol (MCP) server providing deep, token-optimized integration with the **Eventbrite API v3**. Designed specifically for LLM agents, workflow orchestrators, and automated career fair / event management pipelines.

---

## Visual Anchor & Overview

The server bridges LLMs directly to Eventbrite via FastMCP standard I/O transport, providing 84 fine-grained tools covering the complete event lifecycle. Responses are automatically filtered and pruned through token-efficient payload sanitizers to minimize LLM context window bloat while preserving essential IDs, timestamps, pricing objects, and attendee metadata.

```
┌─────────────────────────┐         StdIO (JSON-RPC)         ┌──────────────────────────────────────┐
│  AI Agent / Claude /    │ ◄──────────────────────────────► │    Eventbrite MCP Server             │
│  Hermes / MCP Client    │                                  │   (FastMCP Fast Tool Registry)       │
└─────────────────────────┘                                  └──────────────────┬───────────────────┘
                                                                                │ HTTPS
                                                                                ▼
                                                             ┌──────────────────────────────────────┐
                                                             │     Eventbrite API v3 (REST)         │
                                                             │  /users, /events, /attendees, etc.   │
                                                             └──────────────────────────────────────┘
```

---

## Features

- **87 Comprehensive MCP Tools**: Full API v3 coverage across organizations, venues, draft/live events, ticket tiers, orders, check-ins, promo codes, reports, plus SQLite-backed custom date-range query extensions.
- **Custom Local Date-Range Search Engine**: Fills Eventbrite API's gap by caching organization events in a local SQLite database with delta sync (`order_by=changed_desc`) to execute lightning-fast date-range queries (`2025 to 2026`).
- **Modular Domain Architecture**: Isolated tool modules (`users_orgs`, `events`, `ticketing`, `attendees_orders`, `discounts_webhooks`, `media_catalog`, `custom`) for maintainability.
- **Token-Efficient Payload Pruning**: Strips bloated repetitive fields and normalizes paginated responses so LLMs receive dense, context-optimized JSON.
- **Live Venue Check-In & Attendee Tracking**: Real-time barcode inspection, custom survey question retrieval, and venue attendee check-ins.
- **Full Ticketing & Capacity Controls**: Manage free/paid admission packages, inventory tiers, ticket groups, and buyer checkout policies.
- **Robust Async Client**: Built on `httpx.AsyncClient` with centralized Bearer token management, standard timeout configurations, and informative error handling.

---

## Tech Stack

- **Language & Runtime**: Python 3.11+
- **Protocol Framework**: FastMCP (`mcp>=1.0.0,<2`)
- **HTTP Client**: `httpx>=0.27.0`
- **Data Validation & Schemas**: `pydantic>=2.0.0`
- **Build Backend**: `hatchling`

---

## Tool Catalog Summary (84 Tools)

| Domain | Count | Key Capabilities |
|---|---|---|
| **Users, Organizations & Venues** | 10 | Profile inspection, organization listing, team member roles, and full venue CRUD operations (`create_venue`, `update_venue`, `get_venue`). |
| **Event Lifecycle & Scheduling** | 21 | Event search, create draft, publish/unpublish, cancel, clone, delete, series/schedules, and group registration teams. |
| **Ticketing, Inventory & Settings** | 17 | Free & paid ticket classes, on-sale filters, inventory tiers, ticket groups, capacity tiers, and buyer checkout settings. |
| **Attendees, Orders & Check-ins** | 9 | Attendee registration lookups, barcode details, live check-ins (`checkin_attendee`), order histories, and organization payouts. |
| **Promotions, Questions & Webhooks** | 14 | Access/discount code management, custom & canned survey questions, and organization/user webhook subscription lifecycle. |
| **Media, Taxonomy & Reports** | 13 | Category/subcategory taxonomies, format types, S3 media upload tokens, sales reports, attendee reports, and event display settings. |
| **Custom Local Date Queries & Sync** | 3 | High-speed local SQLite cache, `order_by=changed_desc` delta sync, and indexed date-range queries (`search_organization_events_by_date`, `sync_organization_events`, `get_cached_event_statistics`). |

---

## Getting Started

### Prerequisites

- **Python**: `3.11` or higher
- **Eventbrite Account & Private Token**: Generate an API token from your [Eventbrite Developer Account](https://www.eventbrite.com/platform/api-keys).

### Installation

Clone the repository and install dependencies in editable mode:

```bash
git clone https://github.com/stalinyang/eventbrite-mcp-server.git
cd eventbrite-mcp-server

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package dependencies
pip install -e .
```

### Environment Variables

Configure your credentials via environment variables or a `.env` file:

| Variable | Required | Description |
|---|---|---|
| `EVENTBRITE_PRIVATE_TOKEN` | **Yes** | Eventbrite API v3 OAuth private token. |
| `EVENTBRITE_API_KEY` | Optional | Fallback alternative if `EVENTBRITE_PRIVATE_TOKEN` is not set. |

```bash
export EVENTBRITE_PRIVATE_TOKEN="your_eventbrite_private_token"
```

---

## Usage / Quickstart

### 1. Direct Stdio Execution

Run the server directly via standard I/O:

```bash
python -m eventbrite.server
# or use the registered console entrypoint
eventbrite-mcp
```

### 2. Using the MCP CLI Runner

```bash
mcp run eventbrite/server.py
```

### 3. Integrating with Hermes Agent or Claude Desktop

Add the server definition to your MCP client configuration (e.g., `~/.hermes/config.yaml` or Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "eventbrite": {
      "command": "/path/to/eventbrite-mcp-server/.venv/bin/python",
      "args": ["-m", "eventbrite.server"],
      "env": {
        "EVENTBRITE_PRIVATE_TOKEN": "YOUR_PRIVATE_TOKEN"
      }
    }
  }
}
```

---

## Development & Testing

The repository includes a comprehensive unit test suite verifying tool registrations, parameter schemas, mock HTTP transports, and error handling.

Run all tests via Python's standard unittest runner:

```bash
python -m unittest discover tests
```

To run individual test modules:

```bash
python -m unittest tests/test_coverage.py
python -m unittest tests/test_server.py
python -m unittest tests/test_mock_tools.py
```

---

## Project Structure

```
eventbrite-mcp-server/
├── eventbrite/
│   ├── __init__.py               # Package exports (mcp, main)
│   ├── client.py                 # Async httpx client & error handling
│   ├── server.py                 # FastMCP application setup & registry
│   ├── utils.py                  # Token-saving payload pruning & sanitizers
│   └── tools/
│       ├── attendees_orders.py   # Attendees, check-ins, orders & payouts
│       ├── discounts_webhooks.py # Promo codes, custom questions & webhooks
│       ├── events.py             # Event lifecycle, recurring schedules & teams
│       ├── media_catalog.py      # Categories, formats, upload tokens & reports
│       ├── ticketing.py          # Ticket classes, inventory tiers & checkout settings
│       └── users_orgs.py         # Profiles, organizations & venues
├── tests/
│   ├── test_coverage.py          # Domain-wide dispatch tests
│   ├── test_mock_tools.py        # Individual tool mock execution
│   └── test_server.py            # FastMCP endpoint tests
├── .env.example                  # Sample environment variable template
├── pyproject.toml                # Project packaging & script definitions
└── README.md                     # Documentation
```

---

## Contributing & License

Contributions, issue reports, and pull requests are welcome. Please ensure all unit tests pass prior to submitting PRs.

This project is licensed under the [MIT License](LICENSE).
