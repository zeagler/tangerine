"""
This starts the Tangerine Agent which is responsible for processing
  and monitoring tasks on a host
"""

import thread
from atexit import register
from time import sleep, time
import urllib2
from uuid import uuid4

from agent import Agent
from amazon_functions import Amazon
from docker_commands import Docker
from postgres_functions import Postgres
from postgres_connection import close_connections
from rancher_functions import Rancher
from slack_functions import Slack
from UI.agent_web import start_agent_web
from settings import Agent as options

from requests.exceptions import ReadTimeout

def start_task(task):
    """
    Attempt to schedule a task with a `ready` state.
    """
    
    task.starting()

    # Reserve the next run_id
    run_id = postgres.reserve_next_run_id();
    agent.update_run(run_id)
    
    if not run_id:
        task.ready()
        print "Could not reserve a run id"
        return
    
    container = docker.start_task(task, run_id)
    if container:
        print "Run #" + str(run_id) + " for task '" + task.name + "' has started running"
        task.running(run_id, agent.agent_id)
        run = postgres.get_run(run_id)
        if monitor_task(container, run) == "stopped":
            return
            
        check_exitcode(run)
        
    else:
        task.ready()
        print "A container has failed to start for task '" + task.name + "'"

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
        print "Task '" + task.name + "' has completed successfully"
        slack.send_message("Task '" + task.name + "' has completed successfully")

    elif exit_code not in task.recoverable_exitcodes and 0 not in task.recoverable_exitcodes:
        task.failed()
        print "Task '" + task.name + "' failed with error code '" +str(exit_code)+ "'. It will not be rescheduled"
        slack.send_message("Task '" + task.name + "' failed with error code '" +str(exit_code)+ "'. It will not be rescheduled")
      
    elif not task.restartable:
        task.failed()
        print "Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable"
        slack.send_message("Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable")
    
    elif (task.failures + 1) <= task.max_failures:
        task.queue("failed")
        print "Task '" + task.name + "' failed with error code '" + str(exit_code) + "', it will attempt to be rescheduled " + str(task.max_failures-task.failures) + " more time(s)"
    
    else:
        task.failed()
        print "Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled"
        slack.send_message("Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled")

def check_halting(run, container):
    """
    If a task is being halted clean up the task
    """
    task = postgres.get_task(run.task_id)

    if task.state == "stopping" or task.state == "disabling":
        docker.stop_container(container['Id'])

        if task.state == "stopping":
            task.stop()
        elif task.state == "disabling":
            task.disable()
        
        return "stopped"

def add_agent():
    """
    
    """
    # Reserve the next agent_id
    agent_key = uuid4().hex
    agent_id = postgres.reserve_next_agent_id();

    if not agent_id:
        print "Could not reserve an agent id"
        return
      
    if options['DEVELOPMENT']:
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
                          host_ip = urllib2.urlopen('http://169.254.169.254/latest/meta-data/local-ipv4').read(),
                          agent_port = 443,
                          instance_id = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read(),
                          instance_type = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-type').read(),
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
    print agent_info
    thread.start_new_thread(start_agent_web, (agent_info['agent_key'], ))
    agent = Agent(postgres.get_agents(agent_id=agent_info['agent_id']))

    # Loop through the task queue
    while True:
        id = postgres.pop_queue("ready_queue")

        if id:
            task = postgres.get_task(id)
            
            if task:
                if task.state == "ready":
                    start_task(task)
                    agent.update_run("")
                    
        else:
            postgres.load_queue("ready_queue")
            
            # Sleep between load and process
            sleep(3)
