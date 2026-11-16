"""Project 1: one API call.

Turns a messy damage report from the street team (PL / DE / EN)
into structured JSON: vehicle, category, priority, next action.

Run:  uv run p1_classify.py "SC-1003 hamulec tylny prawie nie działa"
"""

import json
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()          # reads ANTHROPIC_API_KEY from the .env file
client = Anthropic()   # finds the key in the environment by itself

MODEL = "claude-haiku-5-5"  # small, fast, cheap: good for classification

# Price per million tokens (USD) for prompts under 100k tokens.
# Check https://platform.claude.com/docs/en/about-claude/pricing before quoting it.
PRICE_IN, PRICE_OUT = 0.10, 0.50

SYSTEM_PROMPT = """You triage damage reports from a scooter street team.
Reports can be in Polish, German or English and are often short and messy.
Write the summary in English, max 15 words.

Priority rules:
- P1: safety risk (brakes, steering, handlebar, broken frame, damaged or hot battery)
- P2: vehicle cannot be rented (display, lock, no connection, flat tyre)
- P3: cosmetic or minor (scratches, dirty, missing sticker)

Action rules:
- P1 -> pull_from_street
- P2 -> repair_on_street if a street mechanic can fix it, else pull_from_street
- P3 -> next_scheduled_visit

If the report has no vehicle ID, use "unknown"."""

# The JSON shape we want back. The API forces the answer to match it.
SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_id": {"type": "string"},
        "category": {
            "type": "string",
            "enum": ["brakes", "battery", "electronics", "frame", "lock", "tyre", "cosmetic", "other"],
        },
        "priority": {"type": "string", "enum": ["P1", "P2", "P3"]},
        "action": {
            "type": "string",
            "enum": ["pull_from_street", "repair_on_street", "next_scheduled_visit"],
        },
        "summary": {"type": "string"},
    },
    "required": ["vehicle_id", "category", "priority", "action", "summary"],
    "additionalProperties": False,
}


def classify(report: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,  # upper limit for the answer (thinking counts too)
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": report}],
        output_config={
            "effort": "low",  # simple task: think less, answer faster and cheaper
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
    )

    # The answer is a list of blocks. It can start with a "thinking" block,
    # so we keep only the text blocks instead of reading content[0].
    text = "".join(block.text for block in response.content if block.type == "text")

    usage = response.usage
    cost = usage.input_tokens / 1e6 * PRICE_IN + usage.output_tokens / 1e6 * PRICE_OUT
    # Diagnostics go to stderr so they don't mix with the JSON result.
    print(
        f"[{MODEL}] tokens in={usage.input_tokens} out={usage.output_tokens} "
        f"~${cost:.5f} stop={response.stop_reason}",
        file=sys.stderr,
    )
    return json.loads(text)


if __name__ == "__main__":
    report = " ".join(sys.argv[1:]) or "SC-1003 hamulec tylny prawie nie działa, klient zgłosił w apce"
    result = classify(report)
    print(json.dumps(result, indent=2, ensure_ascii=False))