# Theorem B audit — Linux run-book (cloud-agnostic)

For whoever operates the compute box. The workload is CPU-only, embarrassingly
parallel, restartable per (order, shard), and needs ~1 GB RAM per worker.
On 32 modern vCPUs the whole n = 4..17 sweep takes roughly 1-2 hours
(n = 17 alone is 129.7M instances and dominates).

## One-time setup (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y git build-essential python3-venv python3-pip
git clone https://github.com/lshhhhhhh/pseudoforest-counterexample.git
cd pseudoforest-counterexample
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# plantri 5.5 (build from the official source; no patch needed on Linux)
curl -O https://users.cecs.anu.edu.au/~bdm/plantri/plantri55.tar.gz
tar xzf plantri55.tar.gz && (cd plantri55 && make plantri)
export PLANTRI="$PWD/plantri55/plantri"
```

## Run

```bash
export SHARDS=$(nproc)          # capped at 16 by the driver; edit if desired
bash scripts/run_theoremB_audit.sh
```

The driver writes per-order/per-shard logs plus an environment stamp to
`verification/theoremB/`, fails fast on any anomaly, and ends by running
`scripts/theoremB_aggregate.py`, which asserts per order: complete shard
set, sum(total) == A000109, feasible == model_verified == total. Success
looks like:

```
AGGREGATION OK: 149960273 instances, all orders complete and verified.
SWEEP COMPLETE
```

Partial reruns: `N_FROM=16 N_TO=17 bash scripts/run_theoremB_audit.sh`
(existing logs for other orders are left in place; the aggregator checks
the union).

## Hand back

Return the directory `verification/theoremB/` (logs + SUMMARY.md +
ENVIRONMENT_RUN.txt). Committing to the repository is handled on the
maintainer side.
