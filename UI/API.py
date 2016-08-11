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

    def add_task(self, name=None, state=None, dep=None, image=None, cmd=None, etp=None,
                 cron=None, rsrt=None, rec=None, mxf=None, idl=None, daf=None,
                 env=None, dvl=None, prt=None, desc=None):
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
                    dependencies = dep,
                    image = image,
                    command = cmd,
                    entrypoint = etp,
                    cron = cron,
                    restartable = rsrt,
                    exitcodes = rec,
                    max_failures = mxf,
                    delay = idl,
                    faildelay = daf,
                    environment = env,
                    datavolumes = dvl,
                    port = prt,
                    description = desc
                  ))
        
    def update_task(self, id=None, name=None, state=None, dep=None, image=None, cmd=None, etp=None,
                 cron=None, rsrt=None, rec=None, mxf=None, idl=None, daf=None,
                 env=None, dvl=None, prt=None, desc=None):
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
                    dependencies = dep,
                    image = image,
                    command = cmd,
                    entrypoint = etp,
                    cron = cron,
                    restartable = rsrt,
                    exitcodes = rec,
                    max_failures = mxf,
                    delay = idl,
                    faildelay = daf,
                    environment = env,
                    datavolumes = dvl,
                    port = prt,
                    description = desc
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
              
    def queue_task(self, id):
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
            task.queue("misfire")
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