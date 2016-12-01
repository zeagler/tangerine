# TODO:
#   Get specific host
#   Get host history
#   Get scaling history
#   Rancher like controls
#   Pretty Print - Web side

"""
This module holds all of the API reference calls. It is served CherryPy from
  the module `UI/web_interface` which imports this module.
"""

from json import dumps
from docker_commands import get_log

import agent
from amazon_functions import Amazon
import hook
import job
import settings
import user
import instance_configuration

class API(object):
    def __init__(self, postgres):
        # The API needs to connect to the database
        setattr(self, "postgres", postgres)

    def get_users(self, username=None, userid=None, usertype=None):
        if username:   column="username"; value=username
        elif userid:   column="userid";   value=userid
        elif usertype: column="usertype"; value=usertype
        else:          column=None;       value=None

        return user.get_users(column, value)
      
    def get_hosts(self):
        return dumps({
                      "hosts": [host.__dict__ for host in agent.get_agents()],
                      "queued_task_count": self.postgres.get_queued_task_count()
                      })

    def add_task(self, name=None, state=None, tag=None, dependency=None, parent_job=None, removed_parent_defaults=None,
                 image=None, command=None, entrypoint=None, cron=None, restartable=None, exitcodes=None, max_failures=None, delay=None,
                 faildelay=None, environment=None, datavolumes=None, port=None, description=None):
        """
        Add a task to the database
        
        Args:
            All columns in the `tangerine` database
        
        Return:
            if success: the json of the task
            if failure: an appropriate error response
        """
        # add a task
        return dumps(self.postgres.add_task(
                    name = name,
                    state = state,
                    tags = tag,
                    dependencies = dependency,
                    parent_job = parent_job,
                    removed_parent_defaults = removed_parent_defaults,
                    image = image,
                    command = command,
                    entrypoint = entrypoint,
                    cron = cron,
                    restartable = restartable,
                    exitcodes = exitcodes,
                    max_failures = max_failures,
                    delay = delay,
                    faildelay = faildelay,
                    environment = environment,
                    datavolumes = datavolumes,
                    port = port,
                    description = description
                  ))
        
    def update_task(self, id=None, name=None, state=None, tag=None, dependency=None, parent_job=None, removed_parent_defaults=None,
                    image=None, command=None, entrypoint=None, cron=None, restartable=None, exitcodes=None, max_failures=None, delay=None,
                    faildelay=None, environment=None, datavolumes=None, port=None, description=None):
        """
        Update a task
        
        Args:

        
        Returns:
            if success: a json of the request
            if failed: a proper error code
        """
        # update a task
        return dumps(self.postgres.update_task(
                    id = id,
                    name = name,
                    state = state,
                    tags = tag,
                    dependencies = dependency,
                    parent_job = parent_job,
                    removed_parent_defaults = removed_parent_defaults,
                    image = image,
                    command = command,
                    entrypoint = entrypoint,
                    cron = cron,
                    restartable = restartable,
                    exitcodes = exitcodes,
                    max_failures = max_failures,
                    delay = delay,
                    faildelay = faildelay,
                    environment = environment,
                    datavolumes = datavolumes,
                    port = port,
                    description = description
                  ))

    def disable_task(self, id):
        """
        Disable a task. Disabling hides the task from non-admin users and stops processing
          to completely remove a task it needs to be purged with the purge_task(id)
        
        Args:
            id: The id of the task to disable
            
        Return:
            if success: A json confirmation
            if failed: a proper error code
        """
        if not id:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id)
        
        if task:
            task.disable()
            return dumps({"success": "Task was disabled"})
            
        return dumps({"error": "Requested task does not exist"})
      
    def delete_task(self, id, username=""):
        """
        Delete a task.
        
        Args:
            id: The id of the task to delete
            
        Return:
            if success: A json confirmation
            if failed: a proper error code
        """
        if not id:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id)
        
        if task:
            task.delete(username)
            return dumps({"success": "Task was deleted"})
            
        return dumps({"error": "Requested task does not exist"})
      
    def stop_task(self, id):
        """
        Stop a task.
        
        Args:
            id: The id of the task to disable
            
        Return:
            if success: A json confirmation
            if failed: a proper error code
        """
        if not id:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id)
        
        if task:
            task.stop()
            return dumps({"success": "Task was stopped"})
            
        return dumps({"error": "Requested task does not exist"})
              
    def queue_task(self, id=None, name=None, username=None):
        """
        Start a task.
        
        Args:
            id: The id of the task to start
            
        Return:
            if success: A json confirmation
            if failed: a proper error code
        """
        if not id and not name:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id, name)
        
        if task:
            task.queue("misfire", username)
            return dumps({"success": "Task was queued"})
            
        return dumps({"error": "Requested task does not exist"})
                    
    def queue_tag(self, tag, username):
        """
        Start tasks with a tag.
        
        Args:
            id: The tag of tasks to start
            
        Return:
            if success: A json confirmation
            if failed: a proper error code
        """
        if not tag:
            return dumps({"error": "Tag is not defined"})
      
        tasks = self.postgres.get_tasks_tag(tag)
        
        if tasks:
            for task in tasks:
                if task.parent_job == None:
                    task.queue("misfire", username)
            
            return dumps({"success": "Tasks were queued"})
            
        return dumps({"error": "Requested task does not exist"})
      
    def get_task(self, id, name):
        """
        Get a specific task's information
        
        Args:
            id: The id of the task to get
            
        Return:
            if success: A json response of the task
            if failed: a proper error code
        """
        if not id and not name:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id, name)
        return dumps(task.__dict__)
        
    def get_task_object(self, id):
        """
        Get a specific task's information
        
        Args:
            id: The id of the task to get
            
        Return:
            if success: A json response of the task
            if failed: a proper error code
        """
        if not id:
            return dumps({"error": "Task ID is not defined"})
      
        task = self.postgres.get_task(id)
        return task
        
    def get_tasks(self):
        """
        Get the information of all tasks in the database
        
        Args: None
        
        Return:
            a json response of all the tasks
        """
        return dumps([task.__dict__ for task in self.postgres.get_tasks()])
        
    def get_tasks_summary(self):
        """
        Get the information of all tasks in the database
        
        Args: None
        
        Return:
            a json response of all the tasks
        """
        return dumps([task.__dict__ for task in self.postgres.get_tasks_summary()])
      
    def get_runs(self):
        """
        Get information of all runs in the database
        
        Args: None
        
        Return:
            a json response of all the tasks
        """
        return '{ "data": [ ' + ", ".join([run.json for run in self.postgres.get_runs()]) + ']}'
      
    def get_run_object(self, id):
        """
        Get a specific run's information
        
        Args:
            id: The id of the run to get
            
        Return:
            if success: A json response of the run
            if failed: a proper error code
        """
        if not id:
            return dumps({"error": "Run ID is not defined"})
      
        return self.postgres.get_run(id)
      
    def get_log(self, log_name, lines=200):
        """
        
        """
        if not log_name:
            return '{"error": "log_name must be present"}'
        
        log = get_log(log_name=log_name, lines=lines)
        
        if not log == None:
            return log.decode("utf-8")
        else:
            return '{"error": "Could not get log for ' + log_name + '"}'
    
    
    #
    #
    # Begin functions for jobs
    # TODO: Combine the API module with the web_interface module
    #       
    #
    def get_jobs(self, id=None, name=None, column=None, value=None):
        return dumps([j.__dict__ for j in job.get_jobs(id, name, column, value)])

    def get_jobs_summary(self):
        return dumps([j.__dict__ for j in job.get_jobs()])
      
    def get_job_object(self, id=None, name=None):
        """
        Get a specific job's information
        
        Args:
            id: The id of the job to get
            name: The name of the job to get
            
        Return:
            if success: A json response of the task
            if failed: a proper error code
        """
        if id == None and name == None:
            return dumps({"error": "Job ID is not defined"})
      
        jobs = job.get_jobs(id, name)
        return jobs[0]
                      
    def add_job(
                  self, name=None, description="", tags=None, state=None, dependencies=None,
                  parent_job=None, command="", entrypoint="", exitcodes="",
                  restartable=True, datavolumes=None, environment=None, image=None, cron="",
                  max_failures=3, delay=0, faildelay=5, port=None, created_by=""
              ):
      
        return job.add_job(
                            name, description, tags, state, dependencies,
                            parent_job, command, entrypoint, exitcodes,
                            restartable, datavolumes, environment, image, cron,
                            max_failures, delay, faildelay, port, created_by
                          )
      
    def disable_job(self, id=None, name=None, username=None):
        return job.disable_job(id, name, username)
      
    def delete_job(self, id=None, name=None, username=None, mode=0):
        return job.delete_job(id, name, username, mode)
      
    def queue_job(self, id=None, name=None, username=None, state=""):
        return job.queue_job(id, name, username, state)
    
    def stop_job(self, id=None, name=None, username=None, state=""):
        return job.stop_job(id, name, username, state)
    
    def update_job(
                    self,
                    id=None, name=None, description="", tags=None, state=None, dependencies=None,
                    parent_job=None, command="", entrypoint="", exitcodes="",
                    restartable=True, datavolumes=None, environment=None, image=None, cron="",
                    max_failures=3, delay=0, faildelay=5, port=None
                  ):
        return job.update_job(
                                id, name, description, tags, state, dependencies, parent_job, command,
                                entrypoint, exitcodes, restartable, datavolumes, environment, image, cron,
                                max_failures, delay, faildelay, port
                              )
      
    # Tangerine Services
    def add_incoming_hook(self, name=None, action=None, targets=None):
        return dumps(hook.create_hook(name, action, targets))
      
    def get_hooks(self, id=None, action=None, target=None, state=None, api_token=None):
        return dumps({"hooks": [h.__dict__ for h in hook.get_hooks(id, action, target, state, api_token)]})

    def delete_hook(self, id):
        return dumps(hook.delete_hook(id))

    def disable_hook(self, id):
        return dumps(hook.deactivate_hook(id))

    def enable_hook(self, id):
        return dumps(hook.activate_hook(id))
      
    def hook(self, api_token):
        """Execute a webhook"""
        hooks = hook.get_hooks(api_token=api_token)
        
        if hooks:
            h = hooks[0]
            
            if h.state == "inactive":
                return dumps({"error": "Hook is not valid"})
            
            if h.action == "misfire":
                h.set_last_used()
                for target in h.targets:
                    if target[0:5] == "task:":
                        self.queue_task(name=target[5:], username="webhook-" + str(h.id))
                    elif target[0:4] == "job:":
                        self.queue_job(name=target[4:], username="webhook-" + str(h.id))
                    elif target[0:4] == "tag:":
                        self.queue_tag(target[4:], username="webhook-" + str(h.id))
                
                return dumps({"success": "Hook actions were executed"})
            
            return dumps({"error": "Hook is not valid"})
            
        else:
            return dumps({"error": "Could not get requested hook"})
          
    def set_setting(self, setting=None, value=None):
        return dumps(settings.set_setting(setting, value))
      
    def update_user(self, userid, usertype):
        return dumps(user.update_user(userid, usertype))
      
    def delete_user(self, userid):
        return dumps(user.delete_user(userid))
      
    def add_user(self, username, userid, usertype):
        return dumps(user.add_user(username, userid, usertype))
        
    def get_instance_configurations(self, id=None, name=None):
        return dumps({"configs": [c.__dict__ for c in instance_configuration.get_configuration(id, name)]})
      
    def add_instance_configuration(self, name=None, ami=None, key=None, iam=None, ebssize=None,
                                   ebstype=None, userdata=None, instance_type=None, spot=None, bid=None,
                                   subnet=None, sg=None, tag=None, id=None, default=False):
        if id == None:
            return dumps(instance_configuration.create(name, ami, key, iam, ebssize,
                                                        ebstype, userdata, instance_type, spot, bid,
                                                        subnet, sg, tag, default))
        else:
            return dumps(instance_configuration.update(name, ami, key, iam, ebssize,
                                                       ebstype, userdata, instance_type, spot, bid,
                                                       subnet, sg, tag, id, default))          
          
    def delete_configuration(self, id):
        return dumps(instance_configuration.delete(id))
    