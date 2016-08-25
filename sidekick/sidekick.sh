#!/bin/bash

# # (old) This is a workaround until Rancher natively supports container exit codes

# This is an early alpha version of the Tangerine agent, it collects the metrics, log and status of a task
# *Mount the shared logs folder
# *Mount the pgpass
#
# This script is intended to run as a sidekick for containers started by Tangerine
#   mount the docker socket and script
#   set the entrypoint to /sidekick.sh, or where ever the script is mounted
#   set the environment variables
#
# Environment variables:
#   CONTAINER_NAME: The name of the parent container as Rancher would know it. Stack_Service_#
#   RUN_ID: The id of the run in Tangerine
#   PGHOST, PGUSER, PGPORT, PGDATABASE, PGPASS
#   !!! Mount the .pgpass file if not setting PGPASS !!!
#

function convert_to_bytes() {
    # Arguments: $1=BASE $2=UNIT
    if [ -z "$1" ] || [ -z "$2" ]; then echo 0; fi
    
    if [ "$2" == "GB" ]; then
        echo $(echo "scale=0; $1*1000*1000*1000/1" | bc -l)
    elif [ "$2" == "MB" ]; then
        echo $(echo "scale=0; $1*1000*1000/1" | bc -l)
    elif [ "$2" == "KB" ] || [ "$2" == "kB" ]; then
        echo $(echo "scale=0; $1*1000/1" | bc -l)
    else
        echo $(echo "scale=0; $1/1" | bc -l)
    fi
} 

# Get the ID known to the docker daemon
until [ "$CONTAINER_ID" != "" ]; do
  CONTAINER_ID=$(docker ps -a -q --filter "label=tangerine.task.container.name=$CONTAINER_NAME" | head -n 1)
  echo "looking for parent container"
  sleep 3
done

echo "CONTAINER_ID=$CONTAINER_ID"

if [ ! -s /root/.pgpass ]; then
    echo "$PGHOST:$PGPORT:*:$PGUSER:$PGPASS" > /root/.pgpass
    chmod 0600 /root/.pgpass
fi

docker logs $CONTAINER_ID &> "/logs/$RUN_ID"_"$CONTAINER_NAME.log" &
psql -h $PGHOST -U $PGUSER -p $PGPORT -d $PGDATABASE -c "BEGIN;
  UPDATE task_history SET log = '/logs/$RUN_ID"_"$CONTAINER_NAME.log' WHERE run_id=$RUN_ID;
  COMMIT;"

# wait until the container is finished, keep a record of docker stats
until [ "$(docker inspect $CONTAINER_ID | jq '.[] | .State.Status')" != '"running"' ]; do
  if STATS=$(docker stats --no-stream $CONTAINER_ID | grep $CONTAINER_ID); then
      TIME=$(date +%s)
      
      CPU=$(echo $STATS | awk '{print $2}')
      CPU=${CPU//%}
      
      MEM=$(convert_to_bytes $(echo $STATS | awk '{print $3,$4}'))
      NET_IN=$(convert_to_bytes $(echo $STATS | awk '{print $9,$10}'))
      NET_OUT=$(convert_to_bytes $(echo $STATS | awk '{print $12,$13}'))
      BLK_IN=$(convert_to_bytes $(echo $STATS | awk '{print $14,$15}'))
      BLK_OUT=$(convert_to_bytes $(echo $STATS | awk '{print $17,$18}'))
      
      psql -h $PGHOST -U $PGUSER -p $PGPORT -d $PGDATABASE -c "BEGIN;
          UPDATE task_history SET  + \
              time_scale = time_scale || '{$TIME}' WHERE run_id=$RUN_ID,
              cpu_history = cpu_history || '{$CPU}' WHERE run_id=$RUN_ID,
              memory_history = memory_history || '{$MEM}' WHERE run_id=$RUN_ID,
              network_in_history = network_in_history || '{$NET_IN}' WHERE run_id=$RUN_ID,
              network_out_history = network_out_history || '{$NET_OUT}' WHERE run_id=$RUN_ID,
              disk_in_history = disk_in_history || '{$BLK_IN}' WHERE run_id=$RUN_ID,
              disk_out_history = disk_out_history || '{$BLK_OUT}' WHERE run_id=$RUN_ID,
              WHERE run_id=$RUN_ID;
          COMMIT;"
  fi
  
  echo "waiting for parent container to finish"
  sleep 3
done

# Get the Exit code
EXIT_CODE=$(docker inspect $CONTAINER_ID | jq '.[] | .State.ExitCode')
if [ "$EXIT_CODE" = "" ]; then
    EXIT_CODE=1
fi

echo "exit code is $EXIT_CODE"

psql -h $PGHOST -U $PGUSER -p $PGPORT -d $PGDATABASE -c "BEGIN;
  UPDATE task_history SET result_exitcode = $EXIT_CODE WHERE run_id=$RUN_ID;
  COMMIT;"