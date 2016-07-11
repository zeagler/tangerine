"""
This module has functions to connect to and communicate with the Rancher API
"""
import os
import cattle

def connect_to_rancher():
    """
    Create a persistant connection to the Rancher API using standard `CATTLE_` environment variables
    Grab the Stack that is being used for task scheduling, set by the variable `TASK_STACK`
    """
    global client
    print "Connecting to the Rancher API"
    client = cattle.Client(url=os.environ['CATTLE_URL'],
                           access_key=os.environ['CATTLE_ACCESS_KEY'],
                           secret_key=os.environ['CATTLE_SECRET_KEY'])

def set_rancher_variables():
    """
    Set the global variables that are used in this module
    stack: the name of the stack that will be used to create services
    environment: the stack object fetched through the Rancher API
    host_label: the label that must be present on hosts that are intended to recieve tasks
    
    Defaults environment variables:
      TASK_STACK: "Task-Scheduling-Stack"
      HOST_LABEL: "tasks"
    """
    global environment, host_label, stack, sidekick_script_path
    
    stack = os.getenv('TASK_STACK', "Tangerine")
    host_label = os.getenv('HOST_LABEL', "tangerine")
    sidekick_script_path = os.environ['SIDEKICK_SCRIPT_PATH']
    for env in client.list_environment():
        if env.name == stack:
            environment = env
            return
    
    raise ValueError("The Stack '"+stack+"' does not exist in the Rancher environment")

def get_service_by_id(serviceId):
    """Return a service that has the specified serviceId"""
    return client.by_id_service(serviceId)

def get_container_by_service(service):
    """
    Return a container that was started by the specified service
    
    Args:
        stack_service: The io.rancher.stack_service.name label value to search for 
    """
    for container in client.list_container():
        if 'io.rancher.stack_service.name' in container.labels.keys():
            if container.labels['io.rancher.stack_service.name'] == stack + "/" + service:
                return container
    return None

def get_host_by_id(hostId):
    """Return the host that has the specified hostId"""
    return client.by_id_host(hostId)

def list_hosts():
    """Return all the hosts in the environment"""
    return client.list_host()

def list_active_hosts():
    """Return all the hosts in the environment whose state is active"""
    ret_list = []
    for host in list_hosts():
        if host_label in host.labels:
            if 'status' not in host.labels:
                add_labels_to_host(host, "status=idle")
                
            if (host.agentState == 'active' or host.agentState is None) and (host.state == 'active'):
                ret_list.append(host)

    return ret_list

def list_inactive_hosts():
    """Return all the hosts in the environment whose state is not active"""
    ret_list = []
    for host in list_hosts():
        if host_label in host.labels:
            if (host.agentState == 'active' or host.agentState is None) and (host.state == 'active'):
                pass
            else:
                ret_list.append(host)

    return ret_list

def list_hosts_by_label(key, value):
    """Return all active hosts that have a specifc key/value label"""
    ret_list = []
    for host in list_active_hosts():
        if key in host.labels.keys():
            if host.labels[key] == value:
                ret_list.append(host)

    return ret_list

def list_host_by_label(key, value):
    """Return a single host that has a specifc key/value label"""
    for host in list_active_hosts():
        if key in host.labels.keys():
            if host.labels[key] == value:
                return host

def get_idle_host():
    """Return the first active host with a host label status=idle"""
    for host in list_active_hosts():
        if 'status' in host.labels.keys():
            if host.labels['status'] == 'idle':
                return host

    return None

def add_labels_to_host(host, keyvalarr):
    """
    Add multiple host lables to a host
    
    Args:
        Host: The host object to modify labels on
        keyvalarr: A comma-delimeted string of labels and their values
                   Example: "label1=value1,label_w/o_value=,label2=value2"
    """
    for entry in keyvalarr.split(","):
        keyval = entry.split("=")
        host.labels[keyval[0]] = keyval[1]
    client.update(host, labels=host.labels)

def remove_labels_from_host(host, keyarr):
    """
    Remove multiple host labels from a host
    
    Args:
        host: The host object to modify labels on
        keyarr: A comma-delimed string of labels
                Example: "label1,label_w/o_value,label2"
    """
    try:
        for key in keyarr.split(","):
            if key in host.labels:
                del host.labels[key]
        client.update(host, labels=host.labels)
    except KeyError:
        pass

def activate_host(host):
    """Activate a host if it is in a valid state"""
    if 'activate' in host.actions:
        host.activate()

def deactivate_host(host):
    """Dectivate a host if it is in a valid state"""
    if 'deactivate' in host.actions:
        host.deactivate()

def remove_host(host):
    """Remove a host if it is in a valid state"""
    if 'remove' in host.actions:
        host.remove()
    
def restore_host(host):
    """Restore a host if it is in a valid state"""
    if 'restore' in host.actions:
        host.restore()
    
def purge_host(host):
    """Purge a host if it is in a valid state"""
    if 'purge' in host.actions:
        host.purge()

def create_service(host, task):
    """
    Create a service to run a task
    
    Creates a service in the Rancher environment that will execute on the specified host.
      The service consists of two launch configurations, the main config is built using the
      values from the task object. The second config is for a sidekick container that is used
      to monitor the exit code of the container from the first launch configuration. 
    
    Args:
        host: The host object that the task will be executed on
        task: The task object to execute
    """
    
    task_name = task.name.translate(None, '~`!@#$%^&*()_+{}|[]\\:";\'<>?,./=')
    env_variables = dict(task.environment)
    if "docker:" in task.imageuuid:
        image = task.imageuuid
    else:
        image = "docker:" + task.imageuuid
 
    return client.create_service (
      environmentId=environment.id,
      name="Task-" + task_name,
      launchConfig={
        "command": task.command,
        "dataVolumes": task.datavolumes,
        "environment": env_variables,
        "entrypoint": task.entrypoint,
        "name": task_name,
        "labels": {
          "io.rancher.container.start_once": "true"
        },
        "requestedHostId": host.id,
        "imageUuid": image
      },
      secondaryLaunchConfigs=[
        {
          "dataVolumes": ["/var/run/docker.sock:/var/run/docker.sock",
                          sidekick_script_path + ":/sidekick.sh"],
          "environment": {"CATTLE_URL": os.environ['CATTLE_URL'],
                          "CATTLE_ACCESS_KEY": os.environ['CATTLE_ACCESS_KEY'],
                          "CATTLE_SECRET_KEY": os.environ['CATTLE_SECRET_KEY'],
                          "CONTAINER_NAME": environment.name + "_Task-" + task_name + "_1",
                          "HOST_ID": host.id
                          },
          "entryPoint": ["bash", "/sidekick.sh"],
          "name": 'SideKick-' + task_name,
          "labels": {
            "io.rancher.container.start_once": "true"
          },
          "imageUuid": "docker:rancher/agent"
        }
      ],
      startOnCreate="true"
    )
          
def remove_service(service):
    """Remove a service from the Rancher environment"""
    service.remove()