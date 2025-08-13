#!/usr/bin/env bash
set -uo pipefail

run_recommendation() {
  local retries=0
  local max_retries=10
  local backoff=2
  while true; do
    echo "[start.sh] starting recommendation on :8001"
    uvicorn recomendation.recomendation:app --host 0.0.0.0 --port 8001 --log-level info
    exit_code=$?
    echo "[start.sh] recommendation exited with code $exit_code"
    if (( retries >= max_retries )); then
      echo "[start.sh] recommendation reached max retries; sleeping indefinitely"
      sleep infinity
    fi
    retries=$((retries+1))
    sleep $backoff
  done
}

run_chatbot() {
  local retries=0
  local max_retries=10
  local backoff=2
  while true; do
    echo "[start.sh] starting chatbot on :8002"
    uvicorn recomendation.chatbot:app --host 0.0.0.0 --port 8002 --log-level info
    exit_code=$?
    echo "[start.sh] chatbot exited with code $exit_code"
    if (( retries >= max_retries )); then
      echo "[start.sh] chatbot reached max retries; sleeping indefinitely"
      sleep infinity
    fi
    retries=$((retries+1))
    sleep $backoff
  done
}

run_recommendation &
PID1=$!
run_chatbot &
PID2=$!

term() { kill -TERM "$PID1" "$PID2" 2>/dev/null || true; }
trap term SIGTERM SIGINT

wait
