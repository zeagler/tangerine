"""
This starts the Tangerine Agent which is responsible for processing
  and monitoring tasks on a host
"""

import threading
from atexit import register
from time import sleep, strftime, time
from uuid import uuid4
from urllib.request import urlopen
import urllib.error

from agent import Agent
from amazon_functions import Amazon
from docker_commands import Docker
from postgres_functions import Postgres
from postgres_connection import close_connections
from slack_functions import Slack
from agent_web import start_agent_web
from settings import Agent as options
from job import get_jobs

from requests.exceptions import ReadTimeout

def start_task(task, job=None):
    """
    Attempt to schedule a task with a `ready` state.
    """

    task.starting()
    
    # Set fields inherited from the parent
    if not job == None:
        task.name = job.name + "_" + task.name
      
        if task.command == '':
            task.command = job.command_raw
            task.command = task.command.replace("$$count", str(task.count))
            task.command = task.command.replace("$$date", strftime("%Y%m%d"))
            task.command = task.command.replace("$$time", strftime("%H%M%S"))
            
            if task.environment:
                for i in range(len(task.environment)):
                        task.command = task.command.replace("$$" + task.environment[i][0], task.environment[i][1])

            
        if task.entrypoint == '':
            task.entrypoint = job.entrypoint_raw
            task.entrypoint = task.entrypoint.replace("$$count", str(task.count))
            task.entrypoint = task.entrypoint.replace("$$date", strftime("%Y%m%d"))
            task.entrypoint = task.entrypoint.replace("$$time", strftime("%H%M%S"))
            
            if task.environment:
                for i in range(len(task.environment)):
                        task.entrypoint = task.entrypoint.replace("$$" + task.environment[i][0], task.environment[i][1])

        if task.imageuuid == '':
            task.imageuuid = job.imageuuid
            
        env_dict = dict(task.environment)
        for env in job.environment_raw:
            # Don't include the parent value if the environment variable was overridden
            if env[0] in env_dict.keys():
                continue
              
            # Don't include the parent value if the environment variable was removed
            elif "env:" + env[0] in task.removed_parent_defaults:
                continue
              
            # Add the parent's environment variable if the above conditions are not applicable
            else:
                env[1] = env[1].replace("$$count", str(task.count))
                env[1] = env[1].replace("$$date", strftime("%Y%m%d"))
                env[1] = env[1].replace("$$time", strftime("%H%M%S"))
                
                task.environment.append(env)
                task.command = task.command.replace("$$" + env[0], env[1])
                task.entrypoint = task.entrypoint.replace("$$" + env[0], env[1])
              
        dvl_dict = dict([d.split(":") for d in task.datavolumes])
        for dvl in job.datavolumes:
            mount_destination = dvl.split(":")[1]
          
            # Don't include the parent value if the environment variable was overridden
            if mount_destination in dvl_dict.values():
                continue
              
            # Don't include the parent value if the environment variable was removed
            elif "dvl:" + mount_destination in task.removed_parent_defaults:
                continue
              
            # Add the parent's environment variable if the above conditions are not applicable
            else:
                task.datavolumes.append(dvl)

    # Reserve the next run_id
    run_id = postgres.reserve_next_run_id();
    agent.update_run(run_id)
    
    if not run_id:
        task.ready()
        print("Could not reserve a run id")
        return
    
    container = docker.start_task(task, run_id)
    if container:
        print("Run #" + str(run_id) + " for task '" + task.name + "' has started running")
        task.running(run_id, agent.agent_id)
        run = postgres.get_run(run_id)
        if monitor_task(container, run) == "stopped":
            return
            
        check_exitcode(run)
        
    else:
        task.ready()
        print("A container has failed to start for task '" + task.name + "'")

def monitor_task(container, run):
    # Check task for stopping, disabling

    # wait until the container is finished, keep a record of docker stats
    # check that the user has not requested a stop
    
    while True:
        try:
            if docker.container_status(container['Id']) == "exited":
                break
          
            if check_halting(run, container) == "stopped":
                run.finish("stopped")
                return "stopped"

            stats = docker.collect_stats(container['Id'])
            run.insert_stats(stats)
        
        except ReadTimeout:
            pass
        
        except Exception as e:
            print('{!r}; error while monitoring task'.format(e))
            
        sleep(3)

    # Get the Exit code
    exit_code = docker.get_exit_code(container['Id'])
    if exit_code is None:
        exit_code = 1
    
    run.finish(exit_code)
  
    return exit_code

def check_exitcode(run):
    """
    Check on the status of a running task.
    If the host has failed take action to reschedule the task.
    If the container has finished, check the exit code to
      determine what actions need to be taken
    """

    task = postgres.get_task(run.task_id)
    exit_code = run.result_exitcode

    # If the exit code is 0 then the tasks state is set to `success`
    # If the exit code is 127, or if it exit code is in a user-defined
    #   list that indicates it should not be restarted, then the state
    #   is set to `failed`
    # Otherwise the tasks state is set to `queued` and will be rescheduled
    if exit_code == 0:
        task.success()
        print("Task '" + task.name + "' has completed successfully")
        slack.send_message("Task '" + task.name + "' has completed successfully")

    elif exit_code not in task.recoverable_exitcodes and 0 not in task.recoverable_exitcodes:
        task.failed()
        print("Task '" + task.name + "' failed with error code '" +str(exit_code)+ "'. It will not be rescheduled")
        slack.send_message("Task '" + task.name + "' failed with error code '" +str(exit_code)+ "'. It will not be rescheduled")
      
    elif not task.restartable:
        task.failed()
        print("Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable")
        slack.send_message("Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable")
    
    elif (task.failures + 1) < task.max_failures:
        task.queue("failed")
        print("Task '" + task.name + "' failed with error code '" + str(exit_code) + "', it will attempt to be rescheduled " + str(task.max_failures-task.failures) + " more time(s)")
    
    else:
        task.failed()
        print("Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled")
        slack.send_message("Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled")

def check_halting(run, container):
    """
    If a task is being halted clean up the task
    """
    task = postgres.get_task(run.task_id)

    if task.state == "stopping" or task.state == "disabling" or task.state == "deleting":
        docker.stop_container(container['Id'])

        if task.state == "stopping":
            task.stop()
        elif task.state == "disabling":
            task.disable()
        elif task.state == "deleting":
            task.delete()
        
        return "stopped"

def add_agent():
    """
    
    """
    # Reserve the next agent_id
    agent_key = uuid4().hex
    agent_id = postgres.reserve_next_agent_id();

    if not agent_id:
        print("Could not reserve an agent id")
        return
      
    if options['DEVELOPMENT'] == True:
        import socket
        postgres.add_agent(
                          agent_id = agent_id,
                          host_ip = socket.gethostbyname(socket.gethostname()),
                          agent_port = 443,
                          instance_id = "i-123abc",
                          instance_type = "foo.bar",
                          available_memory = dict((i.split()[0].rstrip(':'),int(i.split()[1])) for i in open('/proc/meminfo').readlines())['MemTotal'],
                          agent_creation_time = int(time()),
                          agent_key = agent_key
                        )
    else:
        postgres.add_agent(
                          agent_id = agent_id,
                          host_ip = urlopen('http://169.254.169.254/latest/meta-data/local-ipv4').read(),
                          agent_port = 443,
                          instance_id = urlopen('http://169.254.169.254/latest/meta-data/instance-id').read(),
                          instance_type = urlopen('http://169.254.169.254/latest/meta-data/instance-type').read(),
                          available_memory = dict((i.split()[0].rstrip(':'),int(i.split()[1])) for i in open('/proc/meminfo').readlines())['MemTotal'],
                          agent_creation_time = int(time()),
                          agent_key = agent_key
                        )
    
    return {"agent_key": agent_key, "agent_id": agent_id}
        
"""
This starts the Tangerine Agent which is responsible for processing
  and monitoring tasks on a host
"""
def agent_server():
    global agent, docker, postgres, slack
    register(close_connections) # Close postgres connection at exit
    postgres = Postgres()
    slack = Slack()
    docker = Docker()

    agent_info = add_agent()
    print(agent_info)
    
    server_thread = threading.Thread(target=start_agent_web, args=(agent_info['agent_key'], ))
    server_thread.daemon = True
    server_thread.start()
    
    agent = Agent(postgres.get_agents(agent_id=agent_info['agent_id']))

    # Loop through the task queue
    while True:
        id = postgres.pop_queue("ready_queue")

        if id:
            task = postgres.get_task(id)
            
            if task:
                if task.state == "ready":
                    if task.parent_job:
                        job = get_jobs(id=task.parent_job)[0]
                        
                        if job == None:
                            console.log("Couldn't get parent job")
                            continue
                    else:
                        job = None
                        
                    start_task(task, job)
                    agent.update_run("")
                    
        else:
            postgres.load_queue("ready_queue")
            
            # Sleep between load and process
            sleep(3)
