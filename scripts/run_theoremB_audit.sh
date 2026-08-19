#!/usr/bin/env bash
# Full audited sweep for Theorem B.
#
# Configuration (environment variables):
#   PLANTRI  path to the plantri binary (required unless the authors'
#            default Windows path exists)
#   SHARDS   number of parallel workers for large orders (default: nproc,
#            capped at 16; also used as the plantri res/mod modulus)
#   N_FROM   first order (default 4)
#   N_TO     last order (default 17)
#
# Small orders (n <= 13) run sequentially; larger orders run in SHARDS
# parallel plantri res/mod slices. Every worker fails (nonzero) on any
# infeasible instance, malformed plantri line, model-verification failure,
# or bad plantri exit code. This driver propagates every worker's exit
# status and finishes with an independent aggregation step asserting
# per-order totals against OEIS A000109.
set -euo pipefail
cd "$(dirname "$0")/.."

SHARDS="${SHARDS:-$( (command -v nproc >/dev/null && nproc) || echo 14 )}"
if [ "$SHARDS" -gt 16 ]; then SHARDS=16; fi
N_FROM="${N_FROM:-4}"
N_TO="${N_TO:-17}"
PY="${PY:-python3}"
command -v uv >/dev/null 2>&1 && PY="uv run python"

mkdir -p verification/theoremB
{
  echo "run started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host: $(uname -a 2>/dev/null || echo unknown)"
  echo "cpus: $( (command -v nproc >/dev/null && nproc) || echo unknown ), shards used: $SHARDS"
  echo "python: $($PY --version 2>&1)"
  echo "plantri: ${PLANTRI:-<default path>}"
  if [ -n "${PLANTRI:-}" ] && command -v sha256sum >/dev/null; then
    echo "plantri sha256: $(sha256sum "$PLANTRI" | cut -d' ' -f1)"
  fi
} > verification/theoremB/ENVIRONMENT_RUN.txt

for n in $(seq "$N_FROM" "$N_TO"); do
  if [ "$n" -le 13 ]; then
    PYTHONIOENCODING=utf-8 $PY scripts/theoremB_audit.py "$n"
  else
    pids=()
    for r in $(seq 0 $((SHARDS - 1))); do
      PYTHONIOENCODING=utf-8 $PY scripts/theoremB_audit.py "$n" "$r/$SHARDS" &
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
  fi
done

PYTHONIOENCODING=utf-8 $PY scripts/theoremB_aggregate.py
echo "SWEEP COMPLETE"
