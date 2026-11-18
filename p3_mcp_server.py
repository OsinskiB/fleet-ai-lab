"""Project 3: the same fleet tools, served over MCP (Model Context Protocol).

Any MCP app (Claude Desktop, Claude Code, Cursor...) can now use them,
without our own agent loop from p2. The app runs the loop.

Claude Desktop starts this file itself. You don't run it by hand,
except to test it with:  uv run mcp dev p3_mcp_server.py
"""

import logging

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import fleet

# stdio servers talk to the app through stdout, so never use print() here.
# logging writes to stderr, which is safe.
logging.basicConfig(level=logging.INFO)

mcp = MCPServer("fleet")


@mcp.tool()
def list_vehicles(zone: str | None = None, status: str | None = None, max_battery: int | None = None) -> list[dict]:
    """List fleet vehicles. Optional filters: zone (e.g. Schwabing),
    status (available, low_battery, damaged, in_warehouse), max_battery (0-100)."""
    return fleet.list_vehicles(zone, status, max_battery)


@mcp.tool()
def get_vehicle(vehicle_id: str) -> dict:
    """Get one vehicle by its ID, e.g. SC-1003."""
    return fleet.get_vehicle(vehicle_id) or {"error": "vehicle not found"}


@mcp.tool()
def create_task(vehicle_id: str, task_type: str, priority: str, note: str) -> dict:
    """Create a work task for one vehicle.
    task_type: charge, repair, relocate or inspect. priority: P1 (safety), P2, P3."""
    logging.info("create_task %s %s %s", vehicle_id, task_type, priority)
    try:
        return fleet.create_task(vehicle_id, task_type, priority, note)
    except ValueError as e:
        # ToolError passes our message to the model, so it can fix its request.
        # Other errors are hidden from the model and only logged here.
        raise ToolError(str(e)) from e


@mcp.tool()
def fleet_summary() -> dict:
    """Fleet totals: vehicles per status and per zone, average battery %."""
    return fleet.fleet_summary()


if __name__ == "__main__":
    mcp.run()  # stdio by default: the app starts this process and talks to it