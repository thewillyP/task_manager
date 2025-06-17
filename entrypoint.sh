#!/bin/bash

# Check for critical Jenkins environment variables
required_vars=("JENKINS_URL" "JENKINS_JOB" "JENKINS_USER" "JENKINS_API_TOKEN" "JENKINS_BUILD_TOKEN")
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done
if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "Error: Missing required environment variables: ${missing_vars[*]}"
    exit 1
fi

# Start Python server with Jenkins environment variables
JENKINS_URL="$JENKINS_URL" JENKINS_JOB="$JENKINS_JOB" JENKINS_USER="$JENKINS_USER" JENKINS_API_TOKEN="$JENKINS_API_TOKEN" JENKINS_BUILD_TOKEN="$JENKINS_BUILD_TOKEN" python /workspace/backend/app.py &

# Copy frontend files and start npm
cp -a /workspace/frontend/. ./frontend/ && cd ./frontend && npm start &

### SSH Server
# ASSUMPTION: The user's .ssh folder is overlaid into the container at ~/.ssh.
# If not present, SSH setup will fail. Ensure the .ssh folder is correctly mounted.
if [ ! -d ~/.ssh ]; then
    echo "Error: ~/.ssh directory not found. Ensure the .ssh folder is overlaid into the container."
    exit 1
fi

# 1. Add machine's preexisting key to its own authorized_keys for no-password access
# Idempotent: Only append if not already present
if ! grep -qxFf ~/.ssh/id_rsa.pub ~/.ssh/authorized_keys 2>/dev/null; then
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
fi

# 2. Dynamically generate sshd keys for the SSH server
mkdir -p ~/hostkeys
ssh-keygen -q -N "" -t rsa -b 4096 -f ~/hostkeys/ssh_host_rsa_key <<< y

exec /usr/sbin/sshd -D -p 2222 -o UsePAM=no -h ~/hostkeys/ssh_host_rsa_key