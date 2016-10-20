"""
This starts the central server which is responsible for hosting the
  web interface, scaling the AWS Spot Fleet request and cleaning out
  inactive objects from Rancher

TODO: Check on the status of the agents
"""

import thread
from atexit import register
from time import sleep
import urllib2
import ssl

from agent import Agent
from amazon_functions import Amazon
from postgres_functions import Postgres
from postgres_connection import close_connections
from slack_functions import Slack
from web_interface import start_web_interface
from job import get_jobs

def check_queued_task(task):
    if not task.waiting_on_dependencies():
        if task.delay:
            task.update("delay", task.delay-1)
        else:
            print "Task '" + task.name + "' has it's dependencies met. It will be put in the ready queue"
            task.ready()

def check_agents():
    """
    
    """
    unverified_context = ssl._create_unverified_context()
    while True:
        sleep(3)
        try:
            agents = []
            agents += [Agent(agent) for agent in postgres.get_agents(state="active")]
            agents += [Agent(agent) for agent in postgres.get_agents(state="bad_agent")]
            
            for agent in agents:
                try:
                    #url = 'https://'+agent.host_ip+':'+agent.agent_port+'/ping?agent_key=' + agent.agent_key
                    url = 'https://'+agent.host_ip+'/ping?agent_key=' + agent.agent_key
                    response = urllib2.urlopen(url, context=unverified_context, timeout = 5).read()
                except urllib2.URLError:
                    response = ""

                if not response == "pong":
                    # this agent did not respond
                    if agent.state == "active":
                        agent.update_state("bad_agent")
                        agent.update_agent_termination_time("0")
                    
                    # Give the agent room for connection error
                    elif agent.agent_termination_time < 5:
                        agent.update_agent_termination_time(agent.agent_termination_time + 1)
                    
                    # The agent is down
                    else:
                        agent.update_state("inactive")
                        agent.update_agent_termination_time()
                        
                        # if the agent was running a task clean it up
                        if agent.run:
                            run = postgres.get_run(agent.run)
                            task = postgres.get_task(id=run.task_id)
                            run.finish("host failure")
                            task.queue("host")

                        # TODO: remove the EC2 host or try to start a new agent and recover the task

                elif agent.state == "bad_agent":
                    # This agent is back up
                    agent.update_state("active")

        except Exception as e:
            print('{!r}; error checking agents'.format(e))

def check_ec2_fleet():
    """
    Scale the Spot Request based on the size of the queue
    
    This keeps the scale of the Spot Fleet at 1/3 the sum of the running
      and ready queue. The hosts are not terminated when the Spot Fleet is
      scaled down. Instead this function will check if the number of active hosts
      in Rancher is greater than the target capacity of the Spot Fleet. This
      function will then terminate an idle instance once per loop to bring the active
      host count down to match the target capacity.
    
    TODO: Scale 1 at a time
    TODO: Add variable scaling rules
    TODO: Wait variable minutes before terminating
    TODO: Scale up timeout
    TODO: Base scale on throughput and history
    """
    loop_delay = 30 # seconds
    timeout_limit = 1800/loop_delay # 30 minutes
    scale_down_timeout = 0
    
    while True:
        try:
            sleep(loop_delay)
            
            if amazon.enabled():
                capacity = amazon.get_target_capacity()
                if capacity == "disabled":
                    continue

                agents = [Agent(agent) for agent in postgres.get_agents(state='active')]
                agent_count = len(agents)
                running_tasks = len(postgres.get_tasks("state", "running"))
                ready_tasks = len(postgres.get_tasks("state", "ready"))
                target = ready_tasks + running_tasks

                # Spot fleet requests have a lower limit of 1
                if (target == 0):
                    target = 1
                
                # Don't go over the user defined limit
                if (target > amazon.scale_limit()):
                    target = amazon.scale_limit()

                if capacity < target:
                    amazon.scale_spot_request(target)
                    slack.send_message("Scaling spot fleet request up to " + str(target) + " hosts")
                    scale_down_timeout = 0
                    continue
                  
                elif capacity > target:
                    if scale_down_timeout > timeout_limit:
                        amazon.scale_spot_request(target)
                        slack.send_message("Scaling spot fleet request down to " + str(target) + " hosts")
                        scale_down_timeout = 0
                        continue
                    else:
                        scale_down_timeout += 1
                        
                elif capacity == target:
                    scale_down_timeout = 0

                # Terminate an EC2 instance if the active amount is more than EC2 capacity
                if agent_count > capacity:
                    for agent in agents:
                        if agent.run:
                            continue
                          
                        amazon.terminate_instance(agent.instance_id)
                        agent.update_state("removing")
                        break # This only terminates 1 instance per function call
                      
                #TODO: Check if agent count is less than ec2 count
                #      Restart the missing agents or get a new ec2 instance

        except Exception as e:
            print('{!r}; error in EC2 scale thread'.format(e))

def job_status(tasks):
    """
    Determine the status of a job based on the state of the tasks contained in the job.
    """
    success = sum(1 if task.state == "success" else 0 for task in tasks)
    failed  = sum(1 if task.state == "failed"  else 0 for task in tasks)
    ready   = sum(1 if task.state == "ready"   else 0 for task in tasks)
    running = sum(1 if task.state == "running" else 0 for task in tasks)
    queued  = sum(1 if task.state == "queued"  else 0 for task in tasks)
    stopped = sum(1 if task.state == "stopped" else 0 for task in tasks)
    warnings = [task.warning for task in tasks if task.warning]

    if warnings:
        return "blocked"
        
    if success == len(tasks):
        return "success"
        
    elif success + failed == len(tasks):
        # All the tasks executed, but there was an error
        # TODO: alert the user in the UI when a task in a job fails
        return "failed"
    
    elif success + failed + queued + ready + running == len(tasks):
        return "running"
    
    elif success + failed + stopped == len(tasks):
        # No tasks are awaiting execution, the user stopped some tasks
        return "stop"
        
    elif success + failed + queued + stopped == len(tasks):
        # Tasks are awaiting execution, but they have not moved to the ready state
        #   This might be caused by a blocked task
        
        for task in tasks:
            if task.state == "queued":
                for dependency in task.dependencies:
                    for task_2 in tasks:
                        if task_2.name == dependency:
                            if task_2.state == "failed" or task_2.state == "stopped":
                                print("'" + str(task.name) + "' in job #" + str(task.parent_job) + " is dependent on the stopped or failed task '" + str(task_2.name) + "'")
                                return "blocked"
                    else:
                        print("'" + str(task.name) + "' in job #" + str(task.parent_job) + " is dependent on a task '" + str(task_2.name) + "' which does not exist in the job")
                        return "blocked"
    else:
        return
    
                                      
def monitor_jobs():
    """
    Continously monitor the job queue. Start a job when it's cron schedule is passed.
    """
    while True:
        try:
            id = postgres.pop_queue("job_queue")

            if id:
                job_list = get_jobs(id=id)

                if job_list:
                    job = job_list[0]
                    tasks = job.child_tasks()
                    
                    # If a task inside the job was misfired mark the job as running
                    if not job.state == "running":
                        set_running = False
                        for task in tasks:
                            if task.state == "running" or task.state == "ready" or task.state == "queued":
                                job.update("state", "running")
                                set_running = True
                                break

                        # Skip to the next job if the above code changed the state of this job
                        if set_running:
                            continue

                    # Check the job for it recurring time
                    if job.state == "success" or job.state == "waiting":
                        job.check_next_run_time()
                        
                    # Check the recurring time for failed jobs if the user enabled it
                    elif job.restartable == True and job.state == "failed":
                        job.check_next_run_time()
                    
                    # Check the child tasks to determine if the job is still active
                    #
                    # if tasks are blocked mark the job and show a warning
                    # if no tasks can be ran mark the job as failed or stopped
                    # otherwise assume the job is healthy
                    
                    elif job.state == "stopping":
                        for task in tasks:
                            if not task.state == "stopped":
                                break
                        else:
                            job.stop()
                    
                    elif job.state == "running":
                        status = job_status(tasks)
                        
                        if status == "success":
                            job.success()
                            
                        elif status == "failed":
                            job.failed()
                            
                        elif status == "stop":
                            job.warn(None)
                            job.update("state", "stopped")
                            
                        elif status == "blocked":
                            if not job.warning:
                                job.warn("Tasks are blocked")
                                
                        elif status == "running":
                            if job.warning:
                                job.warn(None)
                            
                            
            else:
                postgres.load_queue("job_queue")
                
                # Sleep between load and process
                sleep(3)

        except Exception as e:
            print('{!r}; error monitoring jobs'.format(e))
                
            # Sleep after an error
            sleep(3)

def central_server():
    """
    This starts the central server which is responsible for hosting the
      web interface, scaling the AWS Spot Fleet request and cleaning out
      inactive objects from Rancher
    """
    global postgres, amazon, slack
    register(close_connections) # Close postgres connection at exit
    postgres = Postgres()
    amazon = Amazon()
    slack = Slack()

    thread.start_new_thread(start_web_interface, (postgres, ))
    thread.start_new_thread(check_ec2_fleet, ())
    thread.start_new_thread(check_agents, ())
    thread.start_new_thread(monitor_jobs, ())

    # Infinite loop while the functions above do the work
    while True:
        try:
            # Check if any queued tasks have dependencies fulfilled. Put them in the `ready` queue
            #   if all dependencies have a state of `success`

            id = postgres.pop_queue("task_queue")

            if id:
                task = postgres.get_task(id)
                
                if task:  
                    if task.state == "queued":
                        check_queued_task(task)
                        
                    elif task.state == "running":
                        #check_running_task(task)
                        pass
                      
                    # TODO: also check the recurring time for failed tasks
                    elif task.state == "success" or task.state == "waiting":
                        task.check_next_run_time()
            else:
                postgres.load_queue("task_queue")
                
                # Sleep between load and process
                sleep(3)
        except Exception as e:
            print('{!r}; error monitoring tasks'.format(e))      
            
            # Sleep after an error
            sleep(3)