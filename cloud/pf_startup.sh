#!/bin/bash
# Startup script for the pseudoforest Theorem B audit worker (n=17 slices).
# Modeled on the odd-squares cert pilot: metadata-driven, SHA-verified
# package, results to GCS, self-shutdown. Idempotent slice queue: a slice
# is done iff its log object exists under $BUCKET/pf-audit/theoremB/.
set -Eeuo pipefail
exec > >(tee -a /var/log/pf-audit.log) 2>&1

metadata() {
  curl -fsS -H 'Metadata-Flavor: Google' \
    "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"
}

BUCKET="$(metadata artifact-bucket)"
PACKAGE_OBJECT="$(metadata package-object)"
PACKAGE_SHA256="$(metadata package-sha256)"
WORKERS="$(metadata workers)"
MOD="$(metadata slices-mod)"
RUN_ID="$(curl -fsS -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/name)"

WORK=/var/lib/pf-audit
REPO="$WORK/pf"
DONE_PREFIX="$BUCKET/pf-audit/theoremB"

mkdir -p "$WORK"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  build-essential ca-certificates curl python3 python3-venv python3-pip

if ! command -v gcloud >/dev/null 2>&1; then
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo 'deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main' \
    > /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get update
  apt-get install -y --no-install-recommends google-cloud-cli
fi

if [ ! -f "$WORK/package.ok" ]; then
  gcloud storage cp "$BUCKET/$PACKAGE_OBJECT" "$WORK/package.tar.gz"
  echo "$PACKAGE_SHA256  $WORK/package.tar.gz" | sha256sum --check --strict
  rm -rf "$REPO"
  tar -xzf "$WORK/package.tar.gz" -C "$WORK"
  touch "$WORK/package.ok"
fi

# plantri from the pinned source tarball inside the package
if [ ! -x "$WORK/plantri55/plantri" ]; then
  tar -xzf "$REPO/cloud/plantri55.tar.gz" -C "$WORK"
  make -C "$WORK/plantri55" plantri
fi
export PLANTRI="$WORK/plantri55/plantri"

if [ ! -d "$WORK/venv" ]; then
  python3 -m venv "$WORK/venv"
  "$WORK/venv/bin/pip" install --no-cache-dir networkx python-sat
fi
PY="$WORK/venv/bin/python"

{
  echo "run: $RUN_ID  started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host: $(uname -a)"
  echo "cpus: $(nproc)  workers: $WORKERS  slices-mod: $MOD"
  echo "python: $($PY --version 2>&1)"
  echo "networkx: $($PY -c 'import networkx;print(networkx.__version__)')"
  echo "pysat: $($PY -c "import pysat;print(getattr(pysat,'__version__','?'))")"
  echo "plantri sha256(src): $(sha256sum "$REPO/cloud/plantri55.tar.gz" | cut -d' ' -f1)"
} > "$WORK/env_run.txt"
gcloud storage cp "$WORK/env_run.txt" "$DONE_PREFIX/ENVIRONMENT_RUN_${RUN_ID}.txt" || true

# pending slices = 0..MOD-1 minus those whose log already sits in GCS
DONE_LIST="$WORK/done.txt"
gcloud storage ls "$DONE_PREFIX/" 2>/dev/null | sed 's|.*/||' > "$DONE_LIST" || true
PENDING=()
for r in $(seq 0 $((MOD - 1))); do
  grep -qx "n17_s${r}of${MOD}.log" "$DONE_LIST" || PENDING+=("$r")
done
echo "PF-AUDIT pending slices: ${#PENDING[@]} of $MOD"

run_slice() {
  r="$1"
  echo "[slice $r] start $(date -u +%H:%M:%SZ)"
  cd "$REPO"
  if PYTHONIOENCODING=utf-8 "$PY" scripts/theoremB_audit.py 17 "$r/$MOD"; then
    gcloud storage cp "verification/theoremB/n17_s${r}of${MOD}.log" \
      "$DONE_PREFIX/n17_s${r}of${MOD}.log"
    echo "[slice $r] done $(date -u +%H:%M:%SZ)"
  else
    echo "[slice $r] FAILED rc=$?"
    return 1
  fi
}
export -f run_slice
export PY REPO DONE_PREFIX MOD

RC=0
if [ "${#PENDING[@]}" -gt 0 ]; then
  set +e
  printf '%s\n' "${PENDING[@]}" | xargs -P "$WORKERS" -I{} bash -c 'run_slice {}'
  RC=$?
  set -e
fi

gcloud storage ls "$DONE_PREFIX/" 2>/dev/null | sed 's|.*/||' > "$DONE_LIST" || true
LEFT=0
for r in $(seq 0 $((MOD - 1))); do
  grep -qx "n17_s${r}of${MOD}.log" "$DONE_LIST" || LEFT=$((LEFT + 1))
done
echo "PF-AUDIT COMPLETE-CHECK remaining=$LEFT rc=$RC"
gcloud storage cp /var/log/pf-audit.log "$BUCKET/runs/$RUN_ID/pf-audit.log" || true
echo "$RC" > "$WORK/rc.txt"
gcloud storage cp "$WORK/rc.txt" "$BUCKET/runs/$RUN_ID/runner-returncode.txt" || true

shutdown -h now
