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
from time import sleep
import sys

from amazon_functions import Amazon
from UI.API import API
from postgres_functions import Postgres
from postgres_connection import close_connections
from rancher_functions import Rancher
from slack_functions import Slack
from UI.web_interface import start_web_interface
import settings

def process_queued_task(task):
    """
    Check if a queued task has it's dependencies fulfilled. Put it in the `ready` queue
      if all dependencies have a state of `success`
    """
    
    # TODO: UI warning if task is invalid or can't be scheduled
    if task.waiting_on_dependencies():
        #print "Task '" + task.name + "' still has unmet dependencies. It will stay in the waiting queue"
        pass
    else:
        if task.delay:
            task.update("delay", task.delay-1)
        else:
            print "Task '" + task.name + "' has it's dependencies met. It will be put in the ready queue"
            task.ready()

def process_ready_task(task):
    """
    Attempt to schedule a task with a `ready` state.
    Rancher is queried for an idle host.
    If a host is available a service is created to start the task.
    """

    host = rancher.get_idle_host()
    if host:
        # Reserve the next run_id
        run_id = postgres.reserve_next_run_id();
        
        if not run_id:
            print "Could not reserve a run id"
            return
        
        service = rancher.create_service(host, task, run_id)
        if service:
            print "Run #" + str(run_id) + " for task '" + task.name + "' has started running on service '" + service.id + "'"
            task.running(service.id, run_id)
            host.add_labels("status=busy")
        else:
            print "A service has failed to start for task '" + task.name + "' on host '" + host.id + "'"
    else:
        print "No hosts available to run task '" + task.name + "'"

def process_running_task(task):
    """
    Check on the status of a running task.
    If the host has failed take action to reschedule the task.
    If the container has finished, check the exit code to
      determine what actions need to be taken
    """

    service = rancher.get_service_by_id(task.service_id)
    container = rancher.get_container_by_service(service.name)
    host = rancher.get_host_by_id(container.hostId)
    run = postgres.get_run(task.run_id)
    
    if not host:
        return

    # First check that the host and the agent are still alive
    # The agent is considered up if it's state is active or unset
    # The host is considerd up only if it's state is active
    if not ((host.agentState == 'active' or host.agentState is None) and (host.state == "active")):
        # If this is the first time the host is inactive, add a host label `badState`
        if not "badState" in host.labels:
            print "Host '" + host.id + "' has entered a bad state while running task '" + task.name + "'"
            host.add_labels("badState=0")
        
        # If the label `badState` is present then this is the second time the host has
        #   been determined to be inactive. The job is rescheduled and the host is marked for removal
        else:
            if int(host.labels['badState']) < 20:
                host.add_labels("badState=" + str(int(host.labels['badState'])+1))
            else:                
                if task.restartable:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will be rescheduled"
                    task.queue("host")
                else:
                    print "Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will not be rescheduled as it was created with restartable=false"
                    slack.send_message("Host '" + host.id + "' has been marked as a bad host, task '" + task.name + "' will not be rescheduled as it was created with restartable=false")
                    task.failed()

                service.remove()
                run.finish()
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
    elif run.result_exitcode is not None:
        if run.result_exitcode == 0:
            task.success()
            print "Task '" + task.name + "' has completed successfully"
            slack.send_message("Task '" + task.name + "' has completed successfully")

        elif run.result_exitcode not in task.recoverable_exitcodes and 0 not in task.recoverable_exitcodes:
            task.failed()
            print "Task '" + task.name + "' failed with error code '" +str(run.result_exitcode)+ "'. It will not be rescheduled"
            slack.send_message("Task '" + task.name + "' failed with error code '" +str(run.result_exitcode)+ "'. It will not be rescheduled")
          
        elif not task.restartable:
            task.failed()
            print "Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable"
            slack.send_message("Task '" + task.name + "' failed, it will not restart as it was inserted into the table as non-restartable")
        
        elif (task.failures + 1) <= task.max_failures:
            task.queue("failed")
            print "Task '" + task.name + "' failed with error code '" + str(run.result_exitcode) + "', it will attempt to be rescheduled " + str(task.max_failures-task.failures) + " more time(s)"
        
        else:
            task.failed()
            print "Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled"
            slack.send_message("Task '" + task.name + "' has failed "+str(task.max_failures)+" times, it will not be rescheduled")

        host.remove_labels("badContainer")
        host.add_labels("status=idle")
        service.remove()
        run.finish()

    
    # If the container is no longer active but has no exit code follow the same
    #   procedure as `badHost` from above.
    elif container.state == "removed" or container.state == "stopped" or container.state == "purged":
        # If this is the first time a container is found to be inactive add a host label `badContainer` 
        if not "badContainer" in host.labels:
            print "Container '" + container.id + "' has entered a bad state while running task '" + task.name + "'"
            host.add_labels("badContainer=0")
        
        # Otherwise remove the service and reschedule the task
        else:
            if int(host.labels['badContainer']) < 20:
                host.add_labels("badContainer=" + str(int(host.labels['badContainer'])+1))
            else:
                print "Container '" + container.id + "' has been marked as a bad container, task '" + task.name + "' will be rescheduled"
                task.queue("container")
                host.remove_labels("badContainer")
                host.add_labels("status=idle")
                service.remove()
                run.finish()

    elif "badContainer" in host.labels:
        print "Container '" + container.id + "' has returned to a active state"
        host.remove_labels("badContainer")

    # If the loop made it this far there is no known problems with the task
    else:
        #print "Task '" + task.name + "' is still running"
        pass


def process_halting_task(task):
    """
    If a task is being halted clean up the task
    """
    
    service = rancher.get_service_by_id(task.service_id)
    container = rancher.get_container_by_service(service.name)
    host = rancher.get_host_by_id(container.hostId)
        
    host.remove_labels("badContainer,badHost")
    host.add_labels("status=idle")
    service.remove()
    
    if task.state == "stopping":
        task.stop()
    elif task.state == "disabling":
        task.disable()

def check_hosts():
    """
    Remove inactive hosts from Rancher
    
    If the state of a host is not active, a flag `badHost` is added. If the host
      is still not active on the next execution of the function it is deactivated and removed
    """
    # Future TODO: check with Amazon about status of host, terminate any unresponsive instances 

    rancher_host_counter = 0
    while True:
        # Sleep 5 seconds between loops
        sleep(5)
        # Increment or reset counter
        rancher_host_counter = (rancher_host_counter + 1)%31
        
        # Check on hosts every 2.5 minutes
        if rancher_host_counter >= 30:
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
    TODO: Base scale on throughput and history
    """
    scale_down_timeout = 0
    loop_delay = 60 # seconds
    
    while True:
        sleep(loop_delay)
        
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
            # 60 loops = 30 minutes
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

def main():
    print "Starting Tangerine"
    print "  postgreSQL table: " + settings.Postgresql['TASK_TABLE']
    print "      Rancher Host: " + settings.Rancher['CATTLE_URL']
    print "     Rancher stack: " + settings.Rancher['TASK_STACK']
    print "     Slack webhook: " + settings.Slack['SLACK_WEBHOOK']
    print "Spot Fleet Request: " + settings.Amazon['SPOT_FLEET_REQUEST_ID']

    global postgres, rancher, amazon, slack
    register(close_connections) # Close postgres connection at exit
    postgres = Postgres()
    rancher = Rancher()
    amazon = Amazon()
    slack = Slack()

    thread.start_new_thread(start_web_interface, (postgres, ))
    thread.start_new_thread(check_hosts, ())
    thread.start_new_thread(check_ec2_fleet, ())

    while True:
        id = postgres.pop_queue()

        if id:
            task = postgres.get_task(id)
            
            if task:                
                if task.state == "stopping" or task.state == "disabling":
                    process_halting_task(task)
                
                elif task.state == "queued":
                    process_queued_task(task)
                  
                elif task.state == "ready":
                    process_ready_task(task)
                    
                elif task.state == "running":
                    process_running_task(task)
                
                # TODO: also check the recurring time for failed tasks
                elif task.state == "success" or task.state == "waiting":
                    task.check_next_run_time()
        else:
            postgres.load_queue()
            
            # Sleep between load and process
            sleep(3)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if (sys.argv[1] == "load"):
            # To load a CSV file of task definitions
            print "WIP"
            status = 0
        elif (sys.argv[1] == "web"):
            sys.argv[1] = ""
            postgres = Postgres()
            status = start_web_interface(postgres)
        else:
            status = main()
    else:
        status = main()
        
    exit(status)