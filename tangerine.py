"""
This program is used to schedule tasks onto hosts in conjunction with Rancher

The tasks are tracked through a table in a postgresql database, this
  allows the Tangerine instance to be restartable and replaceable
  without losing any task data.

The hosts are discovered through the Rancher API. Only hosts with a
  user-defined label: `$HOST_LABEL` will be chosen to recieve tasks.
"""

import atexit
import datetime
import time
import os

#from amazon_functions import *
from postgres_functions import *
from rancher_functions import *
from slack_functions import *

def check_queue():
    """
    Loop through the waiting queue to find tasks that have had all
      their dependencies fulfilled. Put them in the ready queue
      if all dependencies have a state of `success`
    """
    
    for task in get_tasks("state", "queued"):
        if task.waiting_on_dependencies():
            print "Task '" + task.name + "' still has unmet dependencies. It will stay in the waiting queue"
        else:
            print "Task '" + task.name + "' has it's dependencies met. It will be put in the ready queue"
            task.update("state", "ready")

def check_ready():
    """
    Loop through the ready queue and attempt to schedule the tasks.
    If there are tasks ready Rancher is queried for an idle host.
    If a host is available a service is created to start the task.
    """
    
    for task in get_tasks("state", "ready"):
        host = get_idle_host()
        if host:
            service = create_service(host, task)
            if service:
                print "Task '" + task.name + "' has started running on service '" + service.id + "'"
                task.update("state", "running")
                task.update("service_id", service.id)
                add_labels_to_host(host, "status=busy")
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

    for task in get_tasks("state", "running"):
        service = get_service_by_id(task.service_id)
        container = get_container_by_service(service.name)
        host = get_host_by_id(container.hostId)

        # First check that the host and the agent are still alive
        # The agent is considered up if it's state is active or unset
        # The host is considerd up only if it's state is active
        if not ((host.agentState == 'active' or host.agentState is None) and (host.state == "active")):
            # If this is the first time the host is inactive, add a host label `badState`
            if not "badState" in host.labels:
                print "Host '" + host.id + "' has entered a bad state while running task '" + task.name + "'"
                add_labels_to_host(host, "badState=")
            
            # If the label `badState` is present then this is the second time the host has
            #   been determined to be inactive. The job is rescheduled and the host is marked for removal
            else:
                if task.restartable:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will be rescheduled"
                    task.update("state", "queued")
                else:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will not be rescheduled as it was created with restartable=false"
                    task.update("state", "failed")
                    
                task.update("service_id", "")
                remove_service(service)
                deactivate_host(host)
            
        # If the loop gets to this condition then the host is active.
        # If the label `badState` is present it can be removed.
        elif 'badState' in host.labels:
            print "Host '" + host.id + "' has returned to an active state"
            remove_labels_from_host(host, "badState")
        
        # If an exit code is available then the container has finished
        # If it is 0 then the tasks state is set to `success`
        # If the exit code is 127, or if it exit code is in a user-defined
        #   list that indicates it should not be restarted, then the state
        #   is set to `failed`
        # Otherwise the tasks state is set to `queued` and will be rescheduled
        elif 'exitCode' in host.labels.keys():
            if host.labels['exitCode'] == "0":
                if task.cron:
                    task.update("state", "cron")
                else:
                    task.update("state", "success")
                
                print "Task '" + task.name + "' has completed successfully"

            elif host.labels['exitCode'] not in task.recoverable_exitcodes:
                task.update("state", "failed")
                print "Task '" + task.name + "' failed with error code '" +host.labels['exitCode']+ "'. It will not be rescheduled"
                # TODO: Send something to Slack
              
            elif not task.restartable:
                task.update("state", "queued")
                print "Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable"
            
            elif task.failures < 2:
                task.update("failures", task.failures + 1)
                task.update("state", "queued")
                print "Task '" + task.name + "' failed with error code '" + host.labels['exitCode'] + "', it will attempt to be rescheduled " + str(3-task.failures) + " more time(s)"
            
            else:
                task.update("failures", task.failures + 1)
                task.update("state", "failed")
                print "Task '" + task.name + "' has failed 3 times, it will not be rescheduled"
                # TODO: Message Slack

            task.update("service_id", "")
            remove_labels_from_host(host, "exitCode,badContainer")
            add_labels_to_host(host, "status=idle")
            remove_service(service)
        
        # If the container is no longer active but has no exit code follow the same
        #   procedure as `badHost` from above.
        elif container.state == "removed" or container.state == "stopped" or container.state == "purged":
            # If this is the first time a container is found to be inactive add a host label `badContainer` 
            if not "badContainer" in host.labels:
                print "Container '" + container.id + "' has entered a bad state while running task '" + task.name + "'"
                add_labels_to_host(host, "badContainer=")
            
            # Otherwise remove the service and reschedule the task
            else:
                print "Container '" + container.id + "' has been marked as a bad container, task '" + task.name + "' will be rescheduled"
                task.update("state", "queued")
                task.update("service_id", "")
                remove_labels_from_host(host, "exitCode,badContainer")
                add_labels_to_host(host, "status=idle")
                remove_service(service)

        elif "badContainer" in host.labels:
            print "Container '" + container.id + "' has returned to a active state"
            remove_labels_from_host(host, "badContainer")

        # If the loop made it this far there is no known problems with the task
        else:
            print "Task '" + task.name + "' is still running"


def check_table():
    """
    Check the task table to see if any tasks are still in the queue
    If there are no tasks ready or running but there is a task in the
      waiting queue then the task can not be started without user intervention
    """
    
    if (not get_tasks("state", "running")) and (not get_tasks("state", "ready")):
        # TODO: check cron jobs
        if not get_tasks("state", "queued"):
            print "No Tasks are running or in the queue"
            # Send one time message to slack stating that tasks are done only if there are no failures
        else:
            # Check waiting queue before sending out an error message
            # This is the code from check_queue
            for task in get_tasks("state", "queued"):
                if not task.waiting_on_dependencies():
                    print "Task '" + task.name + "' has it's dependencies met. It will be put in the ready queue"
                    task.update("state", "ready")
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
    
    for host in list_inactive_hosts():
        # add a host label `badHost` if the host is not active
        if not "badHost" in host.labels:
            print "Host '" + host.id + "' has entered a bad state and has been marked for removal"
            add_labels_to_host(host, "badHost=")
        
        # remove hosts with the label `badHost` if they are still not active
        else:
            print "Host '" + host.id + "' has been inactive for 5 minutes, it is being removed"
            deactivate_host(host)
            remove_host(host)
            purge_host(host)

def check_cron(now, cron):
    """
    Compare a cron configuration with the current time
    
    Args:
        now: An array of cron values of the current time [minute, hour, day of month, month, weekday]
        cron: The cron configuration to compare to
    
    Returns: True if the time satisfies the cron configuration, otherwise False
    """
    for i in reversed(range(5)):
        if cron[i] == "*":
            continue

        # Parse cron lists and ranges
        else:
            expanded_cron = []
            for item in cron[i].split(","):
                if "-" in item:
                    for item in range(int(item.split("-")[0]), int(item.split("-")[1])+1):
                        expanded_cron.append(str(item))
                else:
                    expanded_cron.append(item)

            if str(now[i]) not in expanded_cron:
                return False
              
    return True

def check_cron_tasks():
    """
    Check all tasks that have a cron schedule set. If the current time matches the cron
      configuration then it put in the waiting queue.
    """
    dt = datetime.datetime.now()
    now = [dt.minute, dt.hour, dt.day, dt.month, dt.weekday()]

    for task in get_tasks("state", "cron"):
        if check_cron(now, task.cron):
            print "Task '" + task.name + "' has been put in the queue on schedule"
            task.update("state", "queued")

def main():
    print "Starting Tangerine"
    print "  postgreSQL table: " + os.getenv('TASK_TABLE', "tangerine")
    print "      Rancher Host: " + os.environ['CATTLE_URL']
    print "     Rancher stack: " + os.getenv('TASK_STACK', "Tangerine")
    print "     Slack webhook: " + os.getenv('SLACK_WEBHOOK', "")

    # Close postgresql connection on exit
    atexit.register(close_postgres_connection)
    
    # connect to the Postgresql database
    # Setup the required table if it does not exist
    setup_postgres()
    
    # Open a persistant connection to the Rancher API
    # Get the Stack that will be used by this instance
    connect_to_rancher()
    set_rancher_variables()
    open_slack_webhook()

    # use these variable to alternate between functions in the loop
    function_counter = 0
    rancher_host_counter = 0

    while True:
        if function_counter == 0: 
            check_queue()
            function_counter = 1
            
        elif function_counter == 1:
            check_ready()
            function_counter = 2
            
        elif function_counter == 2:
            check_running()
            function_counter = 3
            
        elif function_counter == 3:
            check_cron_tasks()
            function_counter = 4
            
        else:
            check_table()
            function_counter = 0
        
        # Check on hosts every 2.5 minutes
        if rancher_host_counter >= 15:
            check_hosts()
            rancher_host_counter = 0
        else:
            rancher_host_counter += 1
            
        
        # Sleep 10 seconds between loops
        time.sleep(10)
  
if __name__ == '__main__':
    status = main()
    exit(status)