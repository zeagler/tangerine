# Tangerine
Tangerine is a configurable task scheduler written in Python. It's purpose is to organize and oversee the execution of many tasks as Docker containers across a dynamic set of hosts. Tangerine supports task dependencies, cron restartablility, and error handling, among other features.  

## Features
#### Rancher 
Rancher is the default, and currently only, host discovery method. Tangerine uses the Rancher API to find hosts and create services that execute the task. Each service consists of the user-defined task and a sidekick container that monitors the status of the task and publishes the exit code as a host label. Tangerine uses Host labels to determine which hosts are eligible for a task. It also monitors the state of hosts and removes any unresponsive hosts from Rancher.

#### Amazon
Tangerine was first intended to run tasks across an Amazon Spot Fleet. To better utilize spot instances Tangerine can autoscale a Spot Fleet request based on the size of the task queue. This helps minimizes cloud costs and keep the computing needs of a dynamic workflow accommodated.  
Note: Spot Fleets Requests have a minimum of 1 host, so it will never be scaled to 0.

#### Flexible Scheduling and Error Handling
Due to the dynamic nature of Spot instances host availablility can fluctuate, sometimes terminating a task with little warning. Because there is no guarantee of host availablility Tangerine will continuously wait for hosts to execute tasks on. If a host fails or is shutdown while running a task, the task is put back in the queue if the task is marked as restartable. In the event of an execution error Tangerine can take action based on user-defined error-handling. At the moment the only option available for error handling is to provide a list of error codes that can be restarted.

#### Task Dependencies
If you have a task that requires other tasks to succeed prior to it's own execution you can define dependencies in the task. When you set dependencies a task will stay in the waiting queue until all required tasks reach a state of `success`. It will then be moved to the ready queue and be eligible for scheduling.

#### Cron Restartablility
Recurring tasks can be returned to the queue using Cron configurations. Tangerine can read standard cron format, and supports most notations. Integer, Lists, Ranges, Astricks are supported. Slashs are not yet supported.  
Examples:  
`0,30 * * * *` Repeat at 0 and 30 minutes of every hour  
`0 5 * * 0-4` Run at 5AM Sunday-Thursday  
`1-10 1,3,5 * 1-2,5,7-10, 1-5` Run Mon-Fri during specific months every minute for the first 10 minutes of 1AM, 3AM and 5AM  

#### Slack
Task completion, failures, and other Tangerine updates can be sent to Slack via a webhook. At the moment no messages are sent, the notifications will be added soon.

## How To Use
### PostgreSQL
You will need a postgreSQL database to hold the task table. The `tangerine` table is created at runtime if it does not already exist.

### Set up
##### Docker
I recommend running Tangerine from a docker container. The Dockerfile is supplied if you want to build it, or you can pull `zeagler/tangerine:0.1` from DockerHub. After you have the image available, create a Rancher stack with a service for the Tangerine container with a configuration similar to the Docker run command below. In this situation I'm also using a Postgres service and linking it to Tangerine.

`docker run -d --name postgres -e "POSTGRES_PASSWORD=mypassword" -v /home/ubuntu/shared/postgres:/var/lib/postgresql/data postgres`  
```
docker run -it \
  --name tangerine \
  -e "PGUSER=postgres"
  -e "PGHOST=postgres"
  -e "PGPORT=5432"
  -e "CATTLE_URL=https://localhost" \
  -e "CATTLE_ACCESS_KEY=myaccesskey" \
  -e "CATTLE_SECRET_KEY=mysecretkey" \
  -e "SIDEKICK_SCRIPT_PATH=/home/ubuntu/shared/tangerine/sidekick.sh"
  -v /home/ubuntu/.pgpass:/root/.pgpass
  --link postgres:postgres \
  zeagler/tangerine:0.1
```

##### Standalone
If you want to run Tangerine outside of Docker you will need to install:   
  Python 2.7  
  Rancher API python library: https://github.com/rancher/cattle-cli `pip install cattle`  
  psycopg2 library for postgres: `sudo apt-get install python-psycopg2` or `pip install psycopg2`  
  boto3 for Amazon `pip install boto3`
  web.py for the status page `pip install web.py`

Check the environment section below to ensure you have your environment set up properly then clone the repository and run the program.  
`git clone https://github.com/zeagler/tangerine.git`  
`cd tangerine`  
`python tangerine.py`  

### Environment
There are a few environment variables that must be present for Tangerine to work properly.  
Standard postgreSQL environment variables. required: `PGHOST` `PGUSER` optional: `PGPORT` `PGDATABASE` `PGPASS`  
If `PGPASS` is not provided a valid .pgpass must exist in the `$HOME` directory  
Rancher API variables are required `CATTLE_URL` `CATTLE_ACCESS_KEY` `CATTLE_SECRET_KEY`  
`TASK_TABLE` Default "tangerine". This is the name of the table in the postgres database. If the table doesn't exist on startup it will be created.  
`TASK_STACK` Default "Tangerine". This is the name of the Rancher Stack that is being used to create services under.  
`HOST_LABEL` Default "tangerine". This is a host label that must be preset on a host to be used by Tangerine.  
`SIDEKICK_SCRIPT_PATH` This needs to be the full path to the sidekick script on the host  
`SLACK_WEBHOOK` If you use Slack notifications, leaving this blank will disable notifications.  
`SPOT_FLEET_REQUEST_ID` If you want to use Spot Fleet auto-scaling, leaving this blank willl disable the feature.  
`EC2_SCALE_LIMIT` Default 20. The maximum amount of instances Tangerine will be allowed to scale to.  
If you want to use Spot Fleet scaling, Tangerine can use the standard AWS config profiles or you can set the Amazon CLI environment variables  
If Tangerine is running on an EC2 instance you can set up an IAM role with appropriate permissions and set the variable `AWS_DEFAULT_REGION`.  
`TZ` The timezone to compare cron configurations. The default is the system timezone.  

### Hosts
Hosts are discovered through Rancher. The Rancher agents need to have a few host labels at boot up.  
`tangerine` This tells Tangerine that the host is intended to managed by it. Only hosts with this label will be given tasks. This can be replaced with the `HOST_LABEL` environment variable.  
`status=idle` The host status is used to indicate availablility. This label is modified to `busy` by Tangerine when a task is scheduled.  
`instanceId=$(wget -q -O - http://instance-data/latest/meta-data/instance-id)` If you are using Spot Fleet autoscaling you will need to have this host label set. This is so Tangerine can ensure only idle hosts are getting terminated when scaling down. If this is not set the hosts will not be terminated automatically after the Spot Fleet is scaled down.  

### Task Table
The task table will be created if it is not already present. Tangerine doesn't have a way to populate a table yet. To create a task you need to run an `INSERT` statement from another tool like psql.

The default task table looks like:
```
CREATE TABLE tangerine (
    name                     varchar(100)  PRIMARY KEY,
    state                    varchar(10)   NOT NULL DEFAULT 'queued',
    dependencies             integer[]     NOT NULL DEFAULT '{}',
    command                  varchar[]     NOT NULL DEFAULT '{}',
    recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
    restartable              boolean       NOT NULL DEFAULT true,
    entrypoint               varchar[]     NOT NULL DEFAULT '{}',
    datavolumes              varchar[]     NOT NULL DEFAULT '{}',
    environment              varchar[][2]  NOT NULL DEFAULT '{}',
    imageuuid                varchar       NOT NULL,
    service_id               varchar(10)   NOT NULL DEFAULT '',
    failures                 integer       NOT NULL DEFAULT 0,
    max_failures             integer       NOT NULL DEFAULT 3,
    cron                     varchar[]
);
```
Example Insert: `INSERT INTO tangerine (name, command, datavolumes, environment, imageuuid) VALUES ('whoami', '{bash, -c, whoami}', '{/tmp:/tmp, /home:/home}', '{{var1, val1}, {var2, val2}}', 'docker:ubuntu:16.04');`  
`name`: The unique name of the task  
`state`: The state of the task, all new tasks should use the Default `queued`  
`dependencies`: A list of dependencies by name. `'{Task1, Task2}'`  
`command`: The command to pass to the docker container as a list `'{bash, -c, whoami}'`  
`recoverable_exitcodes`: A list of exit codes that are allowed to reschedule a task `{3,6}`  
`restartable`: A boolean that determines if the task can be rescheduled on failure  
`entrypoint`: The docker entrypoint command as a list `'{whoami}'`  
`datavolumes`: A list of directories to volume mount `'{/home:/home, /tmp:/tmp}'`  
`environment`: A list of keyval arrays to set environment variables `'{{var1=value1}, {var2=value2}}'`  
`imageuuid`: The docker image to run, prefixed with `docker:` eg: `docker:ubuntu:16.04`  
`service_id`: Set by Tangerine, This tracks the service id of the task in Ranchers  
`failures`: Set by Tangerine, the amount of times the task has failed. 3 is the hardcoded limit for the time being.  
`max_failures`: The amount of failures allowed before the task is not rescheduled.  
`cron`: The cron schedule on which to restart succeeded tasks.  