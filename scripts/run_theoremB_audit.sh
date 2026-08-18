#!/usr/bin/env bash
# Full audited sweep, n=4..17; shards n>=14 across 14 workers.
set -e
cd "$(dirname "$0")/.."
for n in 4 5 6 7 8 9 10 11 12 13; do
  PYTHONIOENCODING=utf-8 uv run python scripts/theoremB_audit.py $n
done
for n in 14 15 16 17; do
  for r in $(seq 0 13); do
    PYTHONIOENCODING=utf-8 uv run python scripts/theoremB_audit.py $n "$r/14" &
  done
  wait
done
echo "SWEEP COMPLETE"
