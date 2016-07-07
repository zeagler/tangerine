# Python Task Scheduler
For task/container scheduling in conjunction with Rancher. Full README coming later.

## Required
Python, version 2.7.6 is suggested  
The Rancher API python library: https://github.com/rancher/cattle-cli `pip install cattle`  
The psycopg2 library for postgres: `sudo apt-get install python-psycopg2` or `pip install psycopg2`  

Required environment variables: `CATTLE_URL` `CATTLE_ACCESS_KEY` `CATTLE_SECRET_KEY` `PGUSER` `PGHOST` `PGPORT`  
A valid pgpass must exist in the home directory

## Task Table
The task table will be created if it is not already present. To populate the task table you need to run an `INSERT` statement from another tool.

The default task table looks like:
```
CREATE TABLE tasks (
    name                     varchar(100)  PRIMARY KEY,
    state                    varchar(10)   NOT NULL DEFAULT 'queued',
    dependencies             integer[]     NOT NULL DEFAULT '{}',
    satisfied_dependencies   integer[]     NOT NULL DEFAULT '{}',
    command                  varchar[]     NOT NULL DEFAULT '{}',
    recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
    restartable              boolean       NOT NULL DEFAULT true,
    entrypoint               varchar[]     NOT NULL DEFAULT '{}',
    datavolumes              varchar[]     NOT NULL DEFAULT '{}',
    environment              varchar[][2]  NOT NULL DEFAULT '{}',
    imageuuid                varchar       NOT NULL,
    service_id               varchar(10)   NOT NULL DEFAULT '',
    failures                 integer       NOT NULL DEFAULT 0,
    cron                     varchar[]
);
```
Example Insert: `INSERT INTO tasks (name, command, datavolumes, environment, imageuuid) VALUES ('whoami', '{bash, -c, whoami}', '{/tmp:/tmp, /home:/home}', '{{var1, val1}, {var2, val2}}', 'docker:ubuntu:16.04');`

## What it can do now
Communicate with Rancher to find hosts with specific labels (ie: `status=idle`)  
Update host labels in Rancher, host labels are used to track host availability and task status  
Create a service with the information from a task and specify the host to run containers on  
The Service includes a sidekick container that updates a host label to indicate the exit code of the task
Monitor slaves via Rancher's API to ensure a host hasn't failed  
Maintain the task table to update rows when dependencies have been met, task have been started, or a task has failed  
Catchs success and errors of tasks, when a task errors it set to be rescheduled if the error code is not recoverable
Repeat tasks on a cron schedule
Remove inactive hosts from Rancher
Send messages to slack when events happen

## Still needs
Functions to autoscale a spotfleet if a large number of pending tasks are ready to be ran.  