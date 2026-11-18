"""Project 2: an agent = a model + tools + a loop.

Claude decides which fleet tools to call. Our code runs them and sends
the results back. This repeats until Claude has enough to answer.

Run:  uv run p2_agent.py "Plan the morning shift for Schwabing"
"""

import json
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

import fleet

load_dotenv()
client = Anthropic()

MODEL = "claude-haiku-5-5"  # try "claude-sonnet-5-5" and compare
MAX_STEPS = 10              # safety brake: an agent must never loop forever

SYSTEM_PROMPT = """You are a dispatcher assistant for a scooter fleet operations team.
Always check the data with the tools before you answer. Never invent vehicle IDs or numbers.
Rules for tasks:
- battery under 20% -> task_type "charge", priority P2
- status "damaged" with brakes, handlebar, steering or frame -> "repair", P1
- any other "damaged" -> "repair", P2 (cosmetic only: P3)
Create each task once. Finish with a short shift plan: tasks created, why, and what to do first."""

# Tool descriptions for the model: name, what it does, which inputs it takes.
# The model never runs code. It only asks us to run a tool.
TOOLS = [
    {
        "name": "list_vehicles",
        "description": "List fleet vehicles. All filters are optional. Returns a JSON list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {"type": "string", "description": "District, e.g. Schwabing"},
                "status": {"type": "string", "enum": fleet.STATUSES},
                "max_battery": {"type": "integer", "description": "Only vehicles at or below this battery %"},
            },
        },
    },
    {
        "name": "get_vehicle",
        "description": "Get one vehicle by its ID, e.g. SC-1003.",
        "input_schema": {
            "type": "object",
            "properties": {"vehicle_id": {"type": "string"}},
            "required": ["vehicle_id"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a work task for one vehicle. Only for vehicles you have checked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"},
                "task_type": {"type": "string", "enum": fleet.TASK_TYPES},
                "priority": {"type": "string", "enum": fleet.PRIORITIES},
                "note": {"type": "string", "description": "One short sentence for the street team"},
            },
            "required": ["vehicle_id", "task_type", "priority", "note"],
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    """Run the tool the model asked for and return the result as JSON text."""
    try:
        if name == "list_vehicles":
            result = fleet.list_vehicles(**args)
        elif name == "get_vehicle":
            result = fleet.get_vehicle(**args) or {"error": "vehicle not found"}
        elif name == "create_task":
            result = fleet.create_task(**args)
        else:
            result = {"error": f"unknown tool: {name}"}
    except Exception as e:  # errors go back to the model, so it can correct itself
        result = {"error": str(e)}
    return json.dumps(result, ensure_ascii=False)


def run_agent(goal: str) -> str:
    messages = [{"role": "user", "content": goal}]

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        # Keep the model's whole answer (including thinking and tool requests) in the history.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # No more tool requests: this is the final answer.
            return "".join(b.text for b in response.content if b.type == "text")

        # The model asked for one or more tools. Run each and collect the results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[step {step}] {block.name} {json.dumps(block.input, ensure_ascii=False)}", file=sys.stderr)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,  # tells the model which request this answers
                        "content": run_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return f"Stopped after {MAX_STEPS} steps without a final answer."


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "Plan the morning shift for Schwabing: what needs charging and what needs repair?"
    print(run_agent(goal))