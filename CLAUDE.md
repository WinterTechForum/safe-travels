# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Safe Travels is an MCP (Model Context Protocol) server that exposes tools for deriving driving routes and assessing weather-related danger. It can be used with Claude Code, Claude Desktop, or any MCP-compatible client.

## Running the MCP Server

```bash
# Install dependencies
uv sync

# Run the server (for testing - normally launched by MCP client)
uv run python server.py
```

## Configuring as MCP Server

### Claude Code
Add to your MCP settings:
```json
{
  "mcpServers": {
    "safe-travels": {
      "command": "python",
      "args": ["/path/to/safe-travels/server.py"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "safe-travels": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/safe-travels", "python", "server.py"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Note:** Replace `/path/to/safe-travels` with the actual path to this project.

## Required Environment Variables

- `GOOGLE_MAPS_API_KEY` - Google Maps geocoding and routing API access

## Tools Exposed

### derive_route
Takes origin/destination cities and optional departure/arrival times. Returns a list of (lat, long) waypoints along the route.

### assess_route_danger
Combined tool that handles the full workflow in a single call:
- Takes origin, destination, and optional departure/arrival time
- Derives the route and gets waypoints
- Fetches forecast weather for each waypoint at its expected arrival time (via Open-Meteo API)
- Computes danger scores based on multiple factors:
  - Temperature extremes (cold/heat)
  - Wind speed and gusts
  - Weather conditions (rain, snow, fog, storms)
  - Precipitation intensity (rainfall mm/hr, snowfall cm/hr)
  - Visibility distance
  - Black ice risk (based on air temp, soil temp, and humidity)
- Returns overall assessment with status (SAFE, MODERATE, HAZARDOUS, EXTREME)

Example query: "Compute the danger of traveling from Grayson, GA to Dahlonega, GA on January 23, 2026, leaving at 07:00 AM"

## Architecture

- **`server.py`** - FastMCP server exposing the two tools, plus weather fetching logic
- **`routing.py`** - Google Maps API integration for geocoding and route computation
- **`danger_assessment.py`** - Weather severity scoring functions
