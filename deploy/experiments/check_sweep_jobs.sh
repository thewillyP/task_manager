#!/bin/bash
set -e
SSH_USER=$1
server_job=$(squeue -u "$SSH_USER" -n sweep_server -h -o "%i")
db_job=$(squeue -u "$SSH_USER" -n sweep_db -h -o "%i")
if [ -n "$server_job" ] && [ -n "$db_job" ]; then
    scontrol show job "$server_job" | awk '/NodeList=/ {for(i=1;i<=NF;i++) if($i ~ /^NodeList=/) {split($i,a,"="); print a[2]}}'
else
    echo "MISSING_JOBS"
fi