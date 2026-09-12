# Eventbrite Model Context Protocol (MCP) Server

A Model Context Protocol (MCP) server providing integration with the Eventbrite API v3 for managing events, organizations, venues, ticket classes, attendees, and orders.

## Features

- **User & Organization**: Retrieve account info, list organizations, configure and create venues.
- **Event Management**: List organization events, inspect details, create draft events, publish/unpublish events.
- **Ticketing & Inventory**: Manage ticket classes (free/paid packages), monitor real-time capacity and sold ticket counts.
- **Attendees & Orders**: Search attendee registrations, view question responses/barcodes, check in attendees at venues, review orders.
- **Financials**: Query organization payouts and transfers.

## Installation

```bash
# Clone the repository
git clone https://github.com/stalinyang/eventbrite-mcp-server.git
cd eventbrite-mcp-server

# Install dependencies using uv or pip
pip install -e .
```

## Configuration

Set the Eventbrite API token via environment variable:

```bash
export EVENTBRITE_PRIVATE_TOKEN="your_eventbrite_private_token"
```

## Running the Server

Start via FastMCP standard I/O transport:

```bash
python server.py
```

Or run via MCP runner:

```bash
mcp run server.py
```
