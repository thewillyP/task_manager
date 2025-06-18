#!/bin/bash
set -e
SSH_USER=$1
MAX_JOBS=$2
SWEEP_HOST=$3
SWEEP_PORT=$4
SWEEP_ID=$5
TASK_MANAGER_HOST=$6
TASK_MANAGER_PORT=$7
TASK_INSTANCE_ID=$8

total_jobs=$(squeue -u "$SSH_USER" -h -t pending,running -r | wc -l)
jobs_available=$((MAX_JOBS - total_jobs))
sweep_count=$(curl -s "http://${SWEEP_HOST}:${SWEEP_PORT}/sweep_count/${SWEEP_ID}" | jq -r '.remaining_configs')

if [ "$jobs_available" -le 0 ]; then
    curl -s -X PUT -H "Content-Type: application/json" -d '{"state": "pending"}' "http://${TASK_MANAGER_HOST}:${TASK_MANAGER_PORT}/api/task_instances/${TASK_INSTANCE_ID}"
fi

if [ "$sweep_count" -gt "$jobs_available" ]; then
    curl -s -X PUT -H "Content-Type: application/json" -d '{"state": "pending"}' "http://${TASK_MANAGER_HOST}:${TASK_MANAGER_PORT}/api/task_instances/${TASK_INSTANCE_ID}"
fi

jq -n --arg tj "$total_jobs" --arg ja "$jobs_available" --arg sc "$sweep_count" \
    '{total_jobs: $tj, jobs_available: $ja, sweep_count: $sc}'