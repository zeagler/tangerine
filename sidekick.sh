#!/bin/bash

# This is a workaround until Rancher natively supports container exit codes
#
# This script is intended to run as a sidekick for containers started by the task scheduler
# It will update the host label when the task has completed, adding the exit code to the host
# For convience this will work with the rancher/agent image
#   mount the docker socket and script
#   set the entrypoint to /sidekick.sh, or where ever the script is mounted
#   set the environment variables
#
# Environment variables:
#   CONTAINER_NAME: The name of the parent container as Rancher would know it. Stack_Service_#
#   CATTLE_URL, CATTLE_ACCESS_KEY, CATTLE_SECRET_KEY: Cattle API variables
#   HOST_ID: The id of the host in Rancher
#

# Get the ID known to the docker daemon
until [ "$CONTAINER_ID" != "" ]; do
  CONTAINER_ID=$(docker ps -a -q --filter "label=io.rancher.container.name=$CONTAINER_NAME" | head -n 1)
  echo "looking for parent container"
  sleep 3
done

echo "CONTAINER_ID=$CONTAINER_ID"

# wait until the container is finished
until [ "$(docker inspect $CONTAINER_ID | jq '.[] | .State.Status')" != '"running"' ]; do
  echo "waiting for parent container to finish"
  sleep 3
done

# Get the Exit code
EXIT_CODE=$(docker inspect $CONTAINER_ID | jq '.[] | .State.ExitCode')
if [ "$EXIT_CODE" = "" ]; then EXIT_CODE=1; fi
echo "exit code is $EXIT_CODE"

# Create a python program to update the container label
cat << EOF > updateHost.py
import cattle
import os

client = cattle.Client(url=os.environ['CATTLE_URL'],
                       access_key=os.environ['CATTLE_ACCESS_KEY'],
                       secret_key=os.environ['CATTLE_SECRET_KEY'])

host = client.by_id_host("$HOST_ID")
host.labels['exitCode'] = "$EXIT_CODE"
client.update(host, labels=host.labels)
EOF
python updateHost.py