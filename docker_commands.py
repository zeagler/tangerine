"""
This module is used to communicate with the local docker daemon.
In the future this will completely replace the Rancher module.
"""

from docker import Client
from time import time
from settings import Docker as options
from subprocess import Popen, check_output

def get_log(log_name, lines=200):
    """
    Get the container log from a run using the UNIX shell command `tail`
    
    Args:
        log_name: The name of the file that holds the log. Cannot be empty, usually set
                  by the Tangerine agent that started the container
                  
        lines: The amount of lines to return. Default is 200
    """
    try:
        if not log_name:
            return '{"error": "log_name must be present"}'
        
        log = check_output(["tail", "-n", str(lines), options["log_directory"] + "/" + log_name])
        return log
    except Exception as e:
        print('{!r}; error trying to read log'.format(e))
        return False
    

class Docker(object):
    def __init__(self):
        """
        Connect to the docker daemon
        """
        setattr(self, "docker", Client(base_url='unix://var/run/docker.sock', timeout=10))
        setattr(self, "containers", [])
    
    def start_task(self, task, run_id):
        """
        Create a container for the task and start it
        """
        try:
            if not self.has_image(task.imageuuid):
                self.pull(task.imageuuid)
            
            name = task.name.translate(None, '~`!@#$%^&*()_+{}|[]\\:";\'<>?,./= ')
            volumes = [vol.split(":")[1] for vol in task.datavolumes]

            entrypoint = task.entrypoint
            if entrypoint == "":
                entrypoint = None
            
            command = task.command
            if command == "":
                command = None

            container = self.docker.create_container(
                            image       = task.imageuuid,
                            name        = name + "-" + str(run_id),
                            command     = command,
                            entrypoint  = entrypoint,
                            labels      = {"tangerine.task.container.name": name + "-" + str(run_id),
                                           "tangerine.task.container.run_id": str(run_id)},
                            environment = dict(task.environment),
                            volumes     = volumes,
                            
                            host_config = self.docker.create_host_config(binds=task.datavolumes)
                        )
            
            if container:
                self.docker.start(container['Id'])
                self.containers.append(container)
                self.record_log(container['Id'], name + "-" + str(run_id))
                return container
            
            else:
                return False
              
        except Exception as e:
            print('{!r}; error trying to create container'.format(e))
            return False
    
    def stop_container(self, containerId):
        """ """
        self.docker.stop(containerId)
     
    def remove_container(self, containerId):
        """ """
        self.docker.remove_container(containerId)
    
    def has_image(self, image):
        """ """
        if self.docker.images(name=image):
            return True
        else:
            return False
    
    def pull(self, image):
        """ """
        if "quay.io" in image:
            if not self.login(
                              registry="https://quay.io",
                              username=options["username"],
                              password=options["password"]
                             ):
                return False
            
        response = self.docker.pull(image)
        
        if "Pull complete" in response:
            return True
        else:
            print response
            return False
    
    def login(self, username, password, email="", registry=""):
        """ """
        try:
            response = self.docker.login(username=username, password=password, registry=registry)
       
            if ("Login Succeeded" in str(response)) or (username in str(response)):
                return True
            else:
                print response
                return False
        except Exception as e:
            print('{!r}; error trying to login to registry'.format(e))
            

    def collect_stats(self, containerId):
        """
        Get the metrics of a container and return a dictionary of the metrics
        """
        stats = self.docker.stats(containerId, True, False)
        
        ret_dict = {}
        ret_dict['time'] = int(time())
        
        # Get the CPU usage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        
        if system_delta:
            ret_dict['cpu'] = (1000.0*cpu_delta) / system_delta
        else:
            ret_dict['cpu'] = "0"
        
        # Get the memory usage
        ret_dict['memory'] = stats['memory_stats']['usage']
        ret_dict['max_memory'] = stats['memory_stats']['max_usage']
        
        # Get the disk usage
        disk = stats['blkio_stats']['io_service_bytes_recursive']
        
        if disk:
            ret_dict['read_bytes'] = stats['blkio_stats']['io_service_bytes_recursive'][0]['value']
            ret_dict['write_bytes'] = stats['blkio_stats']['io_service_bytes_recursive'][1]['value']
        else:
            ret_dict['read_bytes'] = "0"
            ret_dict['write_bytes'] = "0"
        
        # Get the network usage
        if "network" in stats:
            ret_dict['rx_bytes'] = stats['networks']['eth0']['rx_bytes']
            ret_dict['tx_bytes'] = stats['networks']['eth0']['tx_bytes']
        else:
            ret_dict['rx_bytes'] = "0"
            ret_dict['tx_bytes'] = "0"
        
        return ret_dict
    
    def record_log(self, containerId, log_name):
        """ """
        try:
            f = open(options["log_directory"] + "/" + log_name + ".log", "w")
            Popen(["docker", "logs", "-f", containerId], stdout=f, stderr=f)
        except Exception as e:
            print('{!r}; error trying to record log'.format(e))
    
    def container_status(self, containerId):
        """ """
        return self.docker.containers(all=True, filters={"id": containerId})[0]['State']
    
    def get_logs(self, containerId):
        """ """
        return self.docker.logs(containerId, stream=False, tail=100, follow=False)
      
    def get_exit_code(self, containerId):
        """ """
        return self.docker.inspect_container(containerId)['State']['ExitCode']
    
    def get_container_id(self, containerName):
        """ """
        containers = self.docker.containers(all=True, filters={"label": "tangerine.task.container.name=" + containerName})
        
        if containers:
            return containers[0]['Id']
        else:
            return None
         