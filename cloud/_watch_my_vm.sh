#!/usr/bin/env bash
G="E:\math\.tools\gcloud\google-cloud-sdk\bin\gcloud.cmd"
sleep 600
for i in $(seq 1 30); do
  S=$("$G" compute instances describe pf-audit-n17-1 --project=odd-squares-cert-20260818 --zone=us-west1-b --format='value(status)' 2>/dev/null)
  N=$("$G" storage ls gs://odd-squares-cert-20260818-artifacts/pf-audit/theoremB/ 2>/dev/null | grep -c "n17_s.*of64.log")
  echo "$(date +%H:%M:%S) vm=$S slices_done=$N/64"
  if [ "$S" != "RUNNING" ]; then echo "VM_STOPPED status=$S slices=$N"; exit 0; fi
  sleep 300
done
echo "WATCH_TIMEOUT"; exit 1
