#!/usr/bin/env bash
# Run one policy on day_001-day_020, then score each day's log.
# Usage: bash run_all.sh <policy>    e.g. bash run_all.sh baseline
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "usage: bash run_all.sh <policy>" >&2
    exit 1
fi

policy="$1"
cd "$(dirname "$0")"

if [ ! -f "solution/policies/$policy.py" ]; then
    echo "error: solution/policies/$policy.py not found" >&2
    exit 1
fi

for i in $(seq -w 1 20); do
    day="day_0$i"
    out="results/$policy/$day"
    echo "== $policy $day =="
    python3 -m simulator --policy "solution.policies.$policy" \
        --data data --day "$day" --output "$out"
    python3 -m solution.performance_monitor \
        --data data --day "$day" --log "$out/log.txt"
done

echo "Done: results/$policy/day_001 ... day_020"
