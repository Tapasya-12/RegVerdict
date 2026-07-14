#!/bin/bash
source ../venv/Scripts/activate
attempt=0
max_attempts=10
wait_seconds=1200   # 20 min between attempts
while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt+1))
    echo "=== Attempt $attempt at $(date -u) ===" >> regression_run_output.log
    python run_regression.py >> regression_run_output.log 2>&1
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "=== SUCCESS on attempt $attempt at $(date -u) ===" >> regression_run_output.log
        exit 0
    fi
    echo "=== Attempt $attempt failed (exit $exit_code), sleeping ${wait_seconds}s ===" >> regression_run_output.log
    sleep $wait_seconds
done
echo "=== Exhausted $max_attempts attempts, giving up ===" >> regression_run_output.log
exit 1
