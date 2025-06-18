#!/bin/bash
set -e
SWEEP_YML_URL=$1
SWEEP_HOST=$2
SWEEP_PORT=$3
curl -s "$SWEEP_YML_URL" | curl -s -X POST -F "file=@-" "http://${SWEEP_HOST}:${SWEEP_PORT}/upload_config"