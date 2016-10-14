# TODO:
#   -Delete a task
#   Get task history
#   Get hosts - Rancher and AWS
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

import job

class API(object):
    def __init__(self, postgres):
        # The API needs to connect to the database
        setattr(self, "postgres", postgres)

    def get_users(self, username=None, userid=None, usertype=None):
        if username:   column="username"; value=username
        elif userid:   column="userid";   value=userid
        elif usertype: column="usertype"; value=usertype
        else:          column=None;       value=None

        return self.postgres.get_users(column, value)

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
              
    def queue_task(self, id, username):
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
            task.queue("misfire", username)
            return dumps({"success": "Task was queued"})
            
        return dumps({"error": "Requested task does not exist"})
      
    def get_task(self, id):
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
        
        if log:
            return log
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
            return dumps({"error": "Task ID is not defined"})
      
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
      
    def queue_job(self, id=None, name=None, username=None, mode=0):
        return job.queue_job(id, name, username, mode)
    
    def stop_job(self, id=None, name=None, username=None):
        return job.stop_job(id, name, username)
    
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