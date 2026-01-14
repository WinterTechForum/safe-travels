Safe Travels
============

An MCP (Model Context Protocol) server that assesses weather-related danger for driving routes. Use it with Claude Code, Claude Desktop, or any MCP-compatible client.

Tools
-----

### assess_route_danger
Combined tool that handles the full workflow in a single call:
- Takes origin, destination, and optional departure/arrival time
- Derives the route and gets waypoints via Google Maps API
- Fetches forecast weather for each waypoint at its expected arrival time via Open-Meteo API
- Computes danger scores for each point
- Returns overall assessment with status (SAFE, MODERATE, HAZARDOUS, EXTREME)

Example: "Compute the danger of traveling from Grayson, GA to Dahlonega, GA on January 23, 2026, leaving at 07:00 AM"

### derive_route
Takes origin/destination cities and optional departure/arrival times. Returns a list of (lat, long) waypoints along the route.

Requirements
------------

* Python 3.12+
* Google Maps API key (for geocoding and routing)

Set the API key in your environment:
```bash
export GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

You'll need to enable these APIs in Google Cloud Console:
- Geocoding API
- Routes API

Installation
------------

```bash
# Install dependencies with uv
uv sync

# Install dev dependencies (for testing)
uv sync --extra dev
```

Testing
-------

```bash
uv run pytest
```

Usage with Claude Desktop
-------------------------

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

Then restart Claude Desktop and ask questions like:
- "What's the danger level for driving from Denver to Boulder tomorrow morning?"
- "Assess the route from Atlanta to Savannah"
