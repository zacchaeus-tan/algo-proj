"""Collect every results/<policy>/<day>/metrics.json into results/summary.csv
and print each policy's average for every metric.

Usage: python3 summarise.py
"""

import csv
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
SUMMARY = RESULTS / "summary.csv"


def main() -> int:
    rows = []
    for metrics_path in sorted(RESULTS.glob("*/day_*/metrics.json")):
        row = {"policy": metrics_path.parent.parent.name, "day": metrics_path.parent.name}
        row.update(json.loads(metrics_path.read_text(encoding="utf-8")))
        rows.append(row)
    if not rows:
        print(f"No metrics.json files found under {RESULTS}")
        return 1

    # Column order: policy, day, then metrics in the order they first appear.
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with SUMMARY.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {SUMMARY.relative_to(RESULTS.parent)}\n")

    by_policy = {}
    for row in rows:
        by_policy.setdefault(row["policy"], []).append(row)
    metrics = [column for column in columns[2:]
               if all(isinstance(row.get(column), (int, float)) for row in rows)]

    width = max(len(name) for name in metrics)
    for policy, policy_rows in by_policy.items():
        print(f"{policy} ({len(policy_rows)} days)")
        for name in metrics:
            values = [row[name] for row in policy_rows if name in row]
            print(f"  {name:<{width}}  {sum(values) / len(values):.4f}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
