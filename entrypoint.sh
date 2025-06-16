#!/bin/bash

# Ensure Jenkins environment variables are set, or provide a warning
if [ -z "$JENKINS_API_TOKEN" ]; then
    echo "Warning: JENKINS_API_TOKEN is not set. Python server may fail to authenticate with Jenkins."
fi
if [ -z "$JENKINS_URL" ]; then
    echo "Warning: JENKINS_URL is not set."
fi
if [ -z "$JENKINS_JOB" ]; then
    echo "Warning: JENKINS_JOB is not set."
fi
if [ -z "$JENKINS_USER" ]; then
    echo "Warning: JENKINS_USER is not set."
fi

# Start Python server with Jenkins environment variables
JENKINS_URL="$JENKINS_URL" JENKINS_JOB="$JENKINS_JOB" JENKINS_USER="$JENKINS_USER" JENKINS_API_TOKEN="$JENKINS_API_TOKEN" python /workspace/backend/app.py &

# Copy frontend files and start npm
cp -a /workspace/frontend/. ./frontend/ && cd ./frontend && npm start &

### SSH Server
# BIG: ASSUMES YOU OVERLAY THE $USER'S .ssh folder into the container. WILL NOT WORK IF YOU DON'T
# 1. Add machine's preexisting key to its own authorized, no-password access list
# Why: If I overlay my .ssh/, the container inherits the user's no-password access list, tricking sshd to not need password
# How: This only needs to be run once, but want idempotency so do if-else check
grep -qxFf ~/.ssh/id_rsa.pub ~/.ssh/authorized_keys || cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
# 2. Dynamically generate sshd keys for the ssh server
mkdir -p ~/hostkeys
ssh-keygen -q -N "" -t rsa -b 4096 -f ~/hostkeys/ssh_host_rsa_key <<< y

exec /usr/sbin/sshd -D -p 2222 -o UsePAM=no -h ~/hostkeys/ssh_host_rsa_key