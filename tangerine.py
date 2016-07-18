"""
This program is used to schedule tasks onto hosts in conjunction with Rancher

The tasks are tracked through a table in a postgresql database, this
  allows the Tangerine instance to be restartable and replaceable
  without losing any task data.

The hosts are discovered through the Rancher API. Only hosts with a
  user-defined label: `$HOST_LABEL` will be chosen to recieve tasks.
"""

import thread
from atexit import register
from datetime import datetime
from os import getenv, environ
from time import sleep, strftime
import sys

from amazon_functions import Amazon
from postgres_functions import Postgres
from rancher_functions import Rancher
from slack_functions import Slack
from statuspage import start_statuspage

def check_queue():
    """
    Loop through the waiting queue to find tasks that have had all
      their dependencies fulfilled. Put them in the ready queue
      if all dependencies have a state of `success`
    """
    
    for task in postgres.get_tasks("state", "queued"):
        if task.waiting_on_dependencies():
            print "Task '" + task.name + "' still has unmet dependencies. It will stay in the waiting queue"
        else:
            if task.delay:
                task.update("delay", task.delay-1)
            else:
                print "Task '" + task.name + "' has it's dependencies met. It will be put in the ready queue"
                task.update("state", "ready")

def check_ready():
    """
    Loop through the ready queue and attempt to schedule the tasks.
    If there are tasks ready Rancher is queried for an idle host.
    If a host is available a service is created to start the task.
    """
    
    for task in postgres.get_tasks("state", "ready"):
        host = rancher.get_idle_host()
        if host:
            service = rancher.create_service(host, task)
            if service:
                print "Task '" + task.name + "' has started running on service '" + service.id + "'"
                task.update("state", "running")
                task.update("service_id", service.id)
                task.update("count", task.count + 1)
                host.add_labels("status=busy")
            else:
                print "A service has failed to start for task '" + task.name + "' on host '" + host.id + "'"
        else:
            print "No hosts available to run task '" + task.name + "'"
            break

def check_running():
    """
    Loop through the running tasks and check on their state.
    If the host has failed take action to reschedule the task.
    If the container has finished, check the exit code to
    determine what actions need to be taken
    """

    for task in postgres.get_tasks("state", "running"):
        service = rancher.get_service_by_id(task.service_id)
        container = rancher.get_container_by_service(service.name)
        host = rancher.get_host_by_id(container.hostId)

        # First check that the host and the agent are still alive
        # The agent is considered up if it's state is active or unset
        # The host is considerd up only if it's state is active
        if not ((host.agentState == 'active' or host.agentState is None) and (host.state == "active")):
            # If this is the first time the host is inactive, add a host label `badState`
            if not "badState" in host.labels:
                print "Host '" + host.id + "' has entered a bad state while running task '" + task.name + "'"
                host.add_labels("badState=")
            
            # If the label `badState` is present then this is the second time the host has
            #   been determined to be inactive. The job is rescheduled and the host is marked for removal
            else:
                if task.restartable:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will be rescheduled"
                    task.update("state", "queued")
                else:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will not be rescheduled as it was created with restartable=false"
                    slack.send_message("Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will not be rescheduled as it was created with restartable=false")
                    task.update("state", "failed")
                    
                task.update("service_id", "")
                service.remove()
                host.deactivate()
            
        # If the loop gets to this condition then the host is active.
        # If the label `badState` is present it can be removed.
        elif 'badState' in host.labels:
            print "Host '" + host.id + "' has returned to an active state"
            host.remove_labels("badState")
        
        # If an exit code is available then the container has finished
        # If it is 0 then the tasks state is set to `success`
        # If the exit code is 127, or if it exit code is in a user-defined
        #   list that indicates it should not be restarted, then the state
        #   is set to `failed`
        # Otherwise the tasks state is set to `queued` and will be rescheduled
        elif 'exitCode' in host.labels.keys():
            if host.labels['exitCode'] == "0":
                task.update("failures", 0)
                if task.cron:
                    task.update("state", "cron")
                else:
                    task.update("state", "success")
                
                print "Task '" + task.name + "' has completed successfully"
                slack.send_message("Task '" + task.name + "' has completed successfully")

            elif host.labels['exitCode'] not in task.recoverable_exitcodes and 0 not in task.recoverable_exitcodes:
                task.update("state", "failed")
                print "Task '" + task.name + "' failed with error code '" +host.labels['exitCode']+ "'. It will not be rescheduled"
                slack.send_message("Task '" + task.name + "' failed with error code '" +host.labels['exitCode']+ "'. It will not be rescheduled")
              
            elif not task.restartable:
                task.update("state", "failed")
                print "Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable"
                slack.send_message("Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable")
            
            elif (task.failures + 1) <= task.max_failures:
                task.update("failures", task.failures + 1)
                task.update("state", "queued")
                task.update("delay", task.reschedule_delay)
                print "Task '" + task.name + "' failed with error code '" + host.labels['exitCode'] + "', it will attempt to be rescheduled " + str(task.max_failures-task.failures) + " more time(s)"
            
            else:
                task.update("failures", task.failures + 1)
                task.update("state", "failed")
                print "Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled"
                slack.send_message("Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled")

            task.update("service_id", "")
            host.remove_labels("exitCode,badContainer")
            host.add_labels("status=idle")
            service.remove()
        
        # If the container is no longer active but has no exit code follow the same
        #   procedure as `badHost` from above.
        elif container.state == "removed" or container.state == "stopped" or container.state == "purged":
            # If this is the first time a container is found to be inactive add a host label `badContainer` 
            if not "badContainer" in host.labels:
                print "Container '" + container.id + "' has entered a bad state while running task '" + task.name + "'"
                host.add_labels("badContainer=")
            
            # Otherwise remove the service and reschedule the task
            else:
                print "Container '" + container.id + "' has been marked as a bad container, task '" + task.name + "' will be rescheduled"
                task.update("state", "queued")
                task.update("service_id", "")
                host.remove_labels("exitCode,badContainer")
                host.add_labels("status=idle")
                service.remove()

        elif "badContainer" in host.labels:
            print "Container '" + container.id + "' has returned to a active state"
            host.remove_labels("badContainer")

        # If the loop made it this far there is no known problems with the task
        else:
            print "Task '" + task.name + "' is still running"


def check_table():
    """
    Check the task table to see if any tasks are still in the queue
    If there are no tasks ready or running but there is a task in the
      waiting queue then the task can not be started without user intervention
    """
    
    # Refresh the in memory copy of tasks
    postgres.refresh_tasks()
    
    if (not postgres.get_tasks("state", "running")) and (not postgres.get_tasks("state", "ready")):
        if not postgres.get_tasks("state", "queued"):
            print "No Tasks are running or in the queue"
            # Send one time message to slack stating that tasks are done only if there are no failures
        else:
            # Check waiting queue before sending out an error message
            for task in postgres.get_tasks("state", "queued"):
                if not task.waiting_on_dependencies():
                    return

            print "There are tasks with un-met dependencies, but there are no tasks in the queue"
            # TODO: Send one time message to slack stating required tasks are missing

def check_hosts():
    """
    Remove inactive hosts from Rancher
    
    If the state of a host is not active, a flag `badHost` is added. If the host
      is still not active on the next execution of the function it is deactivated and removed
    """
    # Future TODO: check with Amazon about status of host, terminate any unresponsive instances 
    
    for host in rancher.list_inactive_hosts():
        # add a host label `badHost` if the host is not active
        if not "badHost" in host.labels:
            print "Host '" + host.id + "' has entered a bad state and has been marked for removal"
            host.add_labels("badHost=")
        
        # remove hosts with the label `badHost` if they are still not active
        else:
            print "Host '" + host.id + "' has been inactive for 5 minutes, it is being removed"
            host.deactivate()
            host.remove()
            host.purge()
            
    for host in rancher.list_active_hosts():
        if "badHost" in host.labels:
            print "Host '" + host.id + "' has returned to an active state"
            host.remove_labels("badHost")

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
    """
    global scale_down_timeout
    capacity = amazon.get_target_capacity()
    if capacity is None:
        return

    running_tasks = len(postgres.get_tasks("state", "running"))
    ready_tasks = len(postgres.get_tasks("state", "ready"))
    target = ready_tasks + running_tasks
    if (target == 0): target = 1
    
    if capacity < target:
        amazon.scale_spot_request(target)
        slack.send_message("Scaling spot fleet request up to " + str(target) + " hosts")
        scale_down_timeout = 0
        return
    elif capacity > target:
        # 30 loops = 30 minutes
        if scale_down_timeout > 30:
            amazon.scale_spot_request(target)
            slack.send_message("Scaling spot fleet request down to " + str(target) + " hosts")
            scale_down_timeout = 0
            return
        else:
            scale_down_timeout += 1
    elif capacity == target:
        scale_down_timeout = 0

    # Terminate an EC2 instance if the active amount is more than EC2 capacity
    hosts = rancher.list_active_hosts()
    if len(hosts) > capacity:
        for host in hosts:
            if 'status' not in host.labels or 'instanceId' not in host.labels:
                continue
            if host.labels['status'] != 'idle':
                continue
              
            amazon.terminate_instance(host.labels['instanceId'])
            host.deactivate()
            break # This only terminates 1 instance per function call

def check_cron_tasks():
    """
    Check all tasks that have a cron schedule set. If the current time matches the cron
      configuration then it put in the waiting queue.
    """
    dt = datetime.now()
    now = [dt.minute, dt.hour, dt.day, dt.month, dt.weekday()]

    for task in postgres.get_tasks("state", "cron"):
        if task.cron_is_satisfied(now):
            task.update("state", "queued")
            print "Task '" + task.name + "' has been put in the queue on it's cron schedule"
            slack.send_message("Task '" + task.name + "' has been put in the queue on it's cron schedule")

def main():
    print "Starting Tangerine"
    print "  postgreSQL table: " + getenv('TASK_TABLE', "tangerine")
    print "      Rancher Host: " + environ['CATTLE_URL']
    print "     Rancher stack: " + getenv('TASK_STACK', "Tangerine")
    print "     Slack webhook: " + getenv('SLACK_WEBHOOK', "")
    print "Spot Fleet Request: " + getenv('SPOT_FLEET_REQUEST_ID', "")

    global postgres, rancher, amazon, slack, scale_down_timeout
    postgres = Postgres()
    register(postgres.close_connection) # Close postgres connection at exit
    rancher = Rancher()
    amazon = Amazon()
    slack = Slack()
    thread.start_new_thread(start_statuspage, (postgres, ))

    # use these variable to alternate between functions in the loop
    function_counter = 0
    rancher_host_counter = 0
    scale_down_timeout = 0
    
    while True:
        if   function_counter == 0: thread.start_new_thread(check_queue, ())
        elif function_counter == 1: thread.start_new_thread(check_ready, ())
        elif function_counter == 2: thread.start_new_thread(check_running, ())
        elif function_counter == 3: thread.start_new_thread(check_cron_tasks, ())
        elif function_counter == 4: thread.start_new_thread(check_ec2_fleet, ())
        else: thread.start_new_thread(check_table, ())

        # Check on hosts every 2.5 minutes
        if rancher_host_counter >= 15: thread.start_new_thread(check_hosts, ())
        
        # Increment or reset counters
        function_counter = (function_counter + 1)%6
        rancher_host_counter = (rancher_host_counter + 1)%16

        # Sleep 10 seconds between loops
        sleep(10)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if (sys.argv[1] == "load"):
            print "WIP"
            status = 0
        elif (sys.argv[1] == "statuspage"):
            sys.argv[1] = ""
            postgres = Postgres()
            status = start_statuspage(postgres)
        else:
            status = main()
    else:
        status = main()
        
    exit(status)