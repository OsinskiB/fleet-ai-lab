"""Eval: run every report from data/reports.txt and count correct priorities."""

from pathlib import Path

from p1_classify import classify

REPORTS_FILE = Path(__file__).parent / "data" / "reports.txt"
lines = REPORTS_FILE.read_text(encoding="utf-8").splitlines()

correct = 0
total = 0
total_cost = 0.0

for line in lines:
    if not line.strip():  # skip empty lines
        continue
    expected, report = line.split("|", 1)
    result, cost = classify(report)
    total += 1
    total_cost += cost
    ok = result["priority"] == expected
    if ok: correct += 1
    print(f"{'OK ' if ok else 'BAD'} expected={expected} got={result['priority']} | {report}")
print(f"Score: {correct}/{total} ({correct / total:.0%}), cost: ${total_cost:.5f}")
