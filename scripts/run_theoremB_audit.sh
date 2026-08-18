#!/usr/bin/env bash
# Full audited sweep for Theorem B, n=4..17; shards n>=14 across 14 workers.
# Each worker fails (nonzero) on any infeasible instance, malformed plantri
# line, model-verification failure, or bad plantri exit code. This driver
# propagates every worker's exit status and finishes with an independent
# aggregation step asserting per-order totals against OEIS A000109.
set -euo pipefail
cd "$(dirname "$0")/.."

for n in 4 5 6 7 8 9 10 11 12 13; do
  PYTHONIOENCODING=utf-8 uv run python scripts/theoremB_audit.py "$n"
done

for n in 14 15 16 17; do
  pids=()
  for r in $(seq 0 13); do
    PYTHONIOENCODING=utf-8 uv run python scripts/theoremB_audit.py "$n" "$r/14" &
    pids+=($!)
  done
  fail=0
  for pid in "${pids[@]}"; do
    wait "$pid" || fail=1
  done
  if [ "$fail" -ne 0 ]; then
    echo "SWEEP FAILED at n=$n" >&2
    exit 1
  fi
done

PYTHONIOENCODING=utf-8 uv run python scripts/theoremB_aggregate.py
echo "SWEEP COMPLETE"
