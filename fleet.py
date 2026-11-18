"""Shared fleet helpers for a FICTIONAL scooter fleet.

Used by the agent (p2_agent.py) and the MCP server (p3_mcp_server.py),
so both "talk" to exactly the same data and rules.
"""

import csv
import uuid
from datetime import datetime
from pathlib import Path

# Paths are built from this file's location, so the code works
# no matter which folder you start it from.
DATA_DIR = Path(__file__).parent / "data"
FLEET_FILE = DATA_DIR / "fleet.csv"
TASKS_FILE = DATA_DIR / "tasks.csv"

STATUSES = ["available", "low_battery", "damaged", "in_warehouse"]
TASK_TYPES = ["charge", "repair", "relocate", "inspect"]
PRIORITIES = ["P1", "P2", "P3"]


def load_fleet() -> list[dict]:
    """Read data/fleet.csv into a list of dicts (one dict per vehicle)."""
    with FLEET_FILE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["battery_pct"] = int(row["battery_pct"])  # CSV gives text, we want a number
    return rows


def list_vehicles(
    zone: str | None = None,
    status: str | None = None,
    max_battery: int | None = None,
) -> list[dict]:
    """Return vehicles, optionally filtered by zone, status and maximum battery level."""
    rows = load_fleet()
    if zone:
        rows = [r for r in rows if r["zone"].lower() == zone.lower()]
    if status:
        rows = [r for r in rows if r["status"] == status]
    if max_battery is not None:
        rows = [r for r in rows if r["battery_pct"] <= max_battery]
    return rows


def get_vehicle(vehicle_id: str) -> dict | None:
    """Return one vehicle by ID, or None if it doesn't exist."""
    for row in load_fleet():
        if row["vehicle_id"].upper() == vehicle_id.upper():
            return row
    return None


def create_task(vehicle_id: str, task_type: str, priority: str, note: str) -> dict:
    """Validate the input, then append a task to data/tasks.csv.

    The checks matter: the model can make mistakes, so our code decides
    what is allowed, not the model.
    """
    if get_vehicle(vehicle_id) is None:
        raise ValueError(f"Vehicle {vehicle_id} does not exist")
    if task_type not in TASK_TYPES:
        raise ValueError(f"task_type must be one of {TASK_TYPES}")
    if priority not in PRIORITIES:
        raise ValueError(f"priority must be one of {PRIORITIES}")

    is_new_file = not TASKS_FILE.exists()
    task = {
        "task_id": f"T-{uuid.uuid4().hex[:6].upper()}",
        "created_at": f"{datetime.now():%Y-%m-%d %H:%M}",
        "vehicle_id": vehicle_id.upper(),
        "task_type": task_type,
        "priority": priority,
        "note": note,
    }
    with TASKS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(task.keys()))
        if is_new_file:
            writer.writeheader()
        writer.writerow(task)
    return task


def fleet_summary() -> dict:
    """Counts per status and per zone, plus average battery."""
    rows = load_fleet()
    by_status = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    by_zone: dict[str, int] = {}
    for r in rows:
        by_zone[r["zone"]] = by_zone.get(r["zone"], 0) + 1
    avg_battery = round(sum(r["battery_pct"] for r in rows) / len(rows), 1)
    return {
        "vehicles_total": len(rows),
        "by_status": by_status,
        "by_zone": by_zone,
        "avg_battery_pct": avg_battery,
    }