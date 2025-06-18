#!/bin/bash
set -e
SSH_USER=$1
jobid=$(squeue -u "$SSH_USER" -n task_manager -h -o "%i" | head -n1)
if [ -n "$jobid" ]; then
    scontrol show job "$jobid" | awk '/NodeList=/ {for(i=1;i<=NF;i++) if($i ~ /^NodeList=/) {split($i,a,"="); print a[2]}}' | head -n1
else
    echo "NO_TASK_MANAGER"
fi