"""
This module has functions to connect to and communicate with the Rancher API
"""
import os
import cattle

class Host(object):
    def __init__(self, host, client):
        setattr(self, "host", host)
        setattr(self, "labels", host.labels)
        setattr(self, "agentState", host.agentState)
        setattr(self, "state", host.state)
        setattr(self, "id", host.id)
        setattr(self, "client", client)

    # These are here because the cattle library doesn't handle invalid state requests.
    def activate(self):
        """Activate a host if it is in a valid state"""
        if 'activate' in self.host.actions:
            self.host.activate()

    def deactivate(self):
        """Dectivate a host if it is in a valid state"""
        if 'deactivate' in self.host.actions:
            self.host.deactivate()

    def remove(self):
        """Remove a host if it is in a valid state"""
        if 'remove' in self.host.actions:
            self.host.remove()
        
    def restore_host(self):
        """Restore a host if it is in a valid state"""
        if 'restore' in self.host.actions:
            self.host.restore()
        
    def purge_host(self):
        """Purge a host if it is in a valid state"""
        if 'purge' in self.host.actions:
            self.host.purge()
    
    
    def add_labels(self, keyvalarr):
        """
        Add multiple host lables to a host
        
        Args:
            keyvalarr: A comma-delimeted string of labels and their values
                      Example: "label1=value1,label_w/o_value=,label2=value2"
        """
        for entry in keyvalarr.split(","):
            keyval = entry.split("=")
            self.labels[keyval[0]] = keyval[1]
        self.client.update(self.host, labels=self.labels)

    def remove_labels(self, keyarr):
        """
        Remove multiple host labels from a host
        
        Args:
            keyarr: A comma-delimed string of labels
                    Example: "label1,label_w/o_value,label2"
        """
        try:
            for key in keyarr.split(","):
                if key in self.labels:
                    del self.labels[key]
            self.client.update(self.host, labels=self.labels)
        except KeyError:
            pass


class Rancher(object):
    """
    Connect to the Rancher API and communicate with it to find hosts, create
      services and modify the host states and labels.
    """
    def __init__(self):
        print "Connecting to the Rancher API"
        
        setattr(self, "url", os.environ['CATTLE_URL'])
        setattr(self, "access_key", os.environ['CATTLE_ACCESS_KEY'])
        setattr(self, "secret_key", os.environ['CATTLE_SECRET_KEY'])
        
        setattr(self, "client", cattle.Client(url=self.url,
                                              access_key=self.access_key,
                                              secret_key=self.secret_key))
        
        setattr(self, "stack", os.getenv('TASK_STACK', "Tangerine"))
        setattr(self, "host_label", os.getenv('HOST_LABEL', "tangerine"))
        setattr(self, "sidekick_script_path", os.environ['SIDEKICK_SCRIPT_PATH'])
        
        # Loop through the Rancher stacks to get tangerine's stack as an object
        for env in self.client.list_environment():
            if env.name == self.stack:
                setattr(self, "environment", env)
                return
        
        # This only executes if the above for loop can't find the stack in Rancher
        raise ValueError("The Stack '"+self.stack+"' does not exist in the Rancher environment")

    def get_service_by_id(self, serviceId):
        """Return a service that has the specified serviceId"""
        return self.client.by_id_service(serviceId)

    def get_container_by_service(self, service):
        """
        Return a container that was started by the specified service
        
        Args:
            stack_service: The io.rancher.stack_service.name label value to search for 
        """
        for container in self.client.list_container():
            if 'io.rancher.stack_service.name' in container.labels.keys():
                if container.labels['io.rancher.stack_service.name'] == self.stack + "/" + self.service:
                    return container
        return None

    def get_host_by_id(self, hostId):
        """Return the host that has the specified hostId"""
        return Host(self.client.by_id_host(hostId))

    def list_hosts(self):
        """Return all the hosts in the environment"""
        return [Host(host, self.client) for host in self.client.list_host()]

    def list_active_hosts(self):
        """Return all the hosts in the environment whose state is active"""
        ret_list = []
        for host in self.list_hosts():
            if self.host_label in host.labels:
                if 'status' not in host.labels:
                    host.add_labels("status=idle")
                    
                if (host.agentState == 'active' or host.agentState is None) and (host.state == 'active'):
                    ret_list.append(host)

        return ret_list

    def list_inactive_hosts(self):
        """Return all the hosts in the environment whose state is not active"""
        ret_list = []
        for host in self.list_hosts():
            if self.host_label in host.labels:
                if (host.agentState == 'active' or host.agentState is None) and (host.state == 'active'):
                    pass
                else:
                    ret_list.append(host)

        return ret_list

    def list_hosts_by_label(self, key, value):
        """Return all active hosts that have a specifc key/value label"""
        ret_list = []
        for host in self.list_active_hosts():
            if key in host.labels.keys():
                if host.labels[key] == value:
                    ret_list.append(host)

        return ret_list

    def list_host_by_label(self, key, value):
        """Return a single host that has a specifc key/value label"""
        for host in self.list_active_hosts():
            if key in host.labels.keys():
                if host.labels[key] == value:
                    return host

    def get_idle_host(self):
        """Return the first active host with a host label status=idle"""
        for host in self.list_active_hosts():
            if 'status' in host.labels.keys():
                if host.labels['status'] == 'idle':
                    return host

        return None

    def create_service(self, host, task):
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
    
        return self.client.create_service (
          environmentId=self.environment.id,
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
                              self.sidekick_script_path + ":/sidekick.sh"],
              "environment": {"CATTLE_URL": self.url,
                              "CATTLE_ACCESS_KEY": self.access_key,
                              "CATTLE_SECRET_KEY": self.secret_key,
                              "CONTAINER_NAME": self.environment.name + "_Task-" + task_name + "_1",
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