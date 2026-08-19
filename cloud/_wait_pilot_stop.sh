#!/usr/bin/env bash
G="E:\math\.tools\gcloud\google-cloud-sdk\bin\gcloud.cmd"
for i in $(seq 1 30); do
  S=$("$G" compute instances describe q7-cert-pilot-1 --project=odd-squares-cert-20260818 --zone=us-west1-b --format='value(status)' 2>/dev/null)
  echo "$(date +%H:%M:%S) pilot=$S"
  if [ "$S" != "RUNNING" ]; then echo "PILOT_STOPPED status=$S"; exit 0; fi
  sleep 300
done
echo "TIMEOUT still running"
exit 1
