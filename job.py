"""
This module contains functions to fetch and manage jobs, and holds the class that is used
  to represent a job as an object.
"""
from time import mktime, strftime, time
from json import dumps
from copy import deepcopy
from croniter import croniter
from datetime import datetime

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def get_jobs(id=None, name=None, column=None, value=None):
    """
    Retrieves a list of job objects that satisfy the arguments. If no arguments are set, all
      of the jobs from the database are returned.
    
    Args:
        id: The id of a job, returns a list with a single job
        name: The name of a job, returns a list with a single job
        column: A column from the job table to match, returns a list with every job that satisfies column=value
        value: The value the column being matched, defaults to `NULL` if the `column` argument is set
    """
    query = "SELECT * FROM jobs"
    
    if id:
        query += " WHERE id='"+str(id)+"'"
    elif name:
        query += " WHERE name='"+name+"'"
    elif column:
        if value == None:
            query += " WHERE "+column+"='NULL'"
        else:
            query += " WHERE "+column+"='"+str(value)+"'"

    results = postgres.execute(query + ";")
    
    if results:
        return [Job(values = job) for job in results.fetchall()];
    else:
        return None

def queue_job(id=None, name=None, username=None, mode=0):
    """Queue a job"""
    job = get_jobs(id, name)[0]
    
    if job:
        job.queue("misfire", username, mode)
        return True
    else:
        return False

def stop_job(id=None, name=None, username=None):
    """Stop a job"""
    job = get_jobs(id, name)[0]
    
    if job:
        job.stop()
        return True
    else:
        return False

def disable_job(id=None, name=None, username=None):
    """Disable a job"""
    job = get_jobs(id, name)[0]
    
    if job:
        job.disable()
        return True
    else:
        return False

def delete_job(id=None, name=None, username=None, mode=0):
    """Disable a job"""
    job = get_jobs(id, name)[0]
    
    if job:
        job.delete(mode)
        return True
    else:
        return False
      
def add_job(
              name, description, tags, state, dependencies, parent_job, command,
              entrypoint, exitcodes, restartable, datavolumes, environment, image, cron,
              max_failures, delay, faildelay, port, created_by
            ):
    """
    Insert a job into the table. The individual tasks contained by the job are created seperately.
    """
    # TODO: check input for validity
    if not name:
        return dumps({"error": "Name can not be blank"})
    elif get_jobs(name=name):
        return dumps({"error": "Name '" + name + "' conflicts with an existing job"})

    if not (state == "running" or state == "waiting" or state == "stopped"):
        return dumps({"error": "Requested state is not valid"})

    if not image:
        return dumps({"error": "Image can not be blank"})
    elif " " in image:
        return dumps({"error": "Image can not contain a space"})
      
    # TODO: Check dependencies, give a warning if one doesn't exist
    
    if parent_job == None:
        parent = "NULL"
    else:
        # TODO: check that the parent exists
        parent = str(parent_job)

    # Parse enviroment, datavolumes, ports, and dependencies     
    if environment:
        if type(environment) is list:
            env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1].replace("'", "''") + '"}' for e in environment]
            env = ", ".join(env);
        else:
            env = '{"' + environment.split("=")[0] + '","' + environment.split("=", 1)[1].replace("'", "''") + '"}'
    else:
        env = None
    
    if datavolumes:
        if type(datavolumes) is list:
            dvl = ", ".join(datavolumes)
        else:
            dvl = datavolumes
    else:
        dvl = None
    
    if dependencies:
        if type(dependencies) is list:
            dep = ", ".join(dependencies)
        else:
            dep = dependencies
    else:
        dep = None
        
    if tags == None:
        job_tags = ""
    else:
        if type(tags) is list:
            job_tags = ", ".join(tags)
        else:
            job_tags = tags

    if created_by == None:
        created = None
    else:
        created = created_by

    columns = {}
        
    columns["name"] = name
    columns["state"] = state
    
    if not job_tags == None:     columns["tags"]                    = "{"+job_tags+"}"
    if not dep == None:          columns["dependencies"]            = "{"+dep+"}"
    #if not parent_job == None:   columns["parent_job"]              = str(parent_job)
    if not image == None:        columns["imageuuid"]               = image
    if not command == None:      columns["command"]                 = command.replace("'","''")
    if not entrypoint == None:   columns["entrypoint"]              = entrypoint.replace("'","''")
    if not cron == None:         columns["cron"]                    = cron
    if not restartable == None:  columns["restartable"]             = restartable
    if not exitcodes == None:    columns["recoverable_exitcodes"]   = "{"+exitcodes+"}"
    if not max_failures == None: columns["max_failures"]            = max_failures
    if not delay == None:        columns["delay"]                   = delay
    if not faildelay == None:    columns["reschedule_delay"]        = faildelay
    if not env == None:          columns["environment"]             = "{"+env+"}"
    if not dvl == None:          columns["datavolumes"]             = "{"+dvl+"}"
    if not port == None:         columns["port"]                    = port
    if not description == None:  columns["description"]             = description.replace("'","''")
    if not created == None:      columns["created_by"]              = created

    query = "INSERT INTO jobs (" + ", ".join(columns.keys())  + ") VALUES (" + ", ".join("'" + str(val) + "'" for val in columns.values()) + ")"

    result = postgres.execute(query)
    
    if result:            
        # check that the row was entered
        job = get_jobs(name=name)[0]
        
        if job:
            job.initialize()
            return dumps(job.__dict__)

    return dumps({"error": "Could not add job"})

def update_job(
                  id, name, description, tags, state, dependencies, parent_job, command,
                  entrypoint, exitcodes, restartable, datavolumes, environment, image, cron,
                  max_failures, delay, faildelay, port
                ):
    """Update an existing job"""
    # TODO: check input for validity
    if not id:
        return dumps({"error": "The Job ID must be provided when updating a job"})
  
    job = get_jobs(id=id)[0]
    
    if not name:
        return dumps({"error": "Name can not be blank"})
    elif not name == job.name:
        if get_jobs(name=name):
            return dumps({"error": "Name '" + name + "' conflicts with an existing job"})

    if not image:
        return dumps({"error": "Image can not be blank"})
    elif " " in image:
        return dumps({"error": "Image can not contain a space"})
      
    # TODO: Check dependencies, give a warning if one doesn't exist
    
    if parent_job == None:
        parent = "NULL"
    else:
        # TODO: check that the parent exists
        parent = str(parent_job)
        
    # Parse enviroment, datavolumes, ports, and dependencies     
    if environment:
        if type(environment) is list:
            env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1].replace("'", "''") + '"}' for e in environment]
            env = ", ".join(env);
        else:
            env = '{"' + environment.split("=")[0] + '","' + environment.split("=", 1)[1].replace("'", "''") + '"}'
    else:
        env = ""
    
    if datavolumes:
        if type(datavolumes) is list:
            dvl = ", ".join(datavolumes)
        else:
            dvl = datavolumes
    else:
        dvl = ""
    
    if dependencies:
        if type(dependencies) is list:
            dep = ", ".join(dependencies)
        else:
            dep = dependencies
    else:
        dep = ""
        
    if tags:
        if type(tags) is list:
            job_tags = ", ".join(tags)
        else:
            job_tags = tags
    else:
        job_tags = ""

    query = "UPDATE jobs SET "
    query += "name='" + name + "'"
    
    if not job_tags == None:     query += ", tags='{" + job_tags + "}'"
    if not dep == None:          query += ", dependencies='{" + dep + "}'"
    #if not parent_job == None:   query += ", parent_job='" + str(parent_job) + "'"
    if not image == None:        query += ", imageuuid='" + image + "'"
    if not command == None:      query += ", command='" + command.replace("'", "''") + "'"
    if not entrypoint == None:   query += ", entrypoint='" + entrypoint.replace("'", "''") + "'"
    if not cron == None:         query += ", cron='" + cron + "'"
    if not restartable == None:  query += ", restartable='" + restartable + "'"
    if not exitcodes == None:    query += ", recoverable_exitcodes='{" + exitcodes + "}'"
    if not max_failures == None: query += ", max_failures='" + max_failures + "'"
    if not delay == None:        query += ", delay='" + delay + "'"
    if not faildelay == None:    query += ", reschedule_delay='" + faildelay + "'"
    if not env == None:          query += ", environment='{" + env + "}'"
    if not dvl == None:          query += ", datavolumes='{" + dvl + "}'"
    if not description == None:  query += ", description='" + description.replace("'","''") + "'"
    
    query += " WHERE id="+str(id)+";"

    result = postgres.execute(query)

    if result:
        # check that the row was updated
        job = get_jobs(id=id)[0]
        
        # TODO: Verify that the new column values match the update request
        if job:
            job.initialize()
            return dumps(job.__dict__)

    return dumps({"error": "Could not update job"})


class Job(object):
    """
    This class is used to represent and manipulate a row in the job table
    All columns of the table become attributes of this object

    Methods:
        update: Update this job's column in the postgreSQL job table
        waiting_on_dependencies: check if this job still has unmet dependencies
    """
    def __init__(self, columns=None, values=None):
        """
        Set the initial attributes of this job object

        Args:
            columns: A list with the columns being set for this job. The default value will become every
                     column from the postgres table in the order they exist in the table.

            values: A list of column values that will be set as an attribute of this job. The order of
                    the values needs to be the same as the `columns` list.
        """
        global postgres
        
        if columns == None:
            columns = postgres.job_columns
            
        for i in range(len(values)):
            setattr(self, columns[i][0], values[i])

        # Interpolate variables
        setattr(self, "command_raw", self.command)
        if self.command:
            self.command = self.command.replace("$$count", str(self.count))
            self.command = self.command.replace("$$date", strftime("%Y%m%d"))
            self.command = self.command.replace("$$time", strftime("%H%M%S"))
        
        setattr(self, "entrypoint_raw", self.entrypoint)
        if self.entrypoint:
            self.entrypoint = self.entrypoint.replace("$$count", str(self.count))
            self.entrypoint = self.entrypoint.replace("$$date", strftime("%Y%m%d"))
            self.entrypoint = self.entrypoint.replace("$$time", strftime("%H%M%S"))
          
        setattr(self, "environment_raw", deepcopy(self.environment))
        if self.environment:
            for i in range(len(self.environment)):
                self.environment[i][1] = self.environment[i][1].replace("$$count", str(self.count))
                self.environment[i][1] = self.environment[i][1].replace("$$date", strftime("%Y%m%d"))
                self.environment[i][1] = self.environment[i][1].replace("$$time", strftime("%H%M%S"))
                
                if self.command:
                    self.command = self.command.replace("$$" + self.environment[i][0], self.environment[i][1])

        # For the web interface
        setattr(self, "dependencies_str", ', '.join(self.dependencies))
        
        if self.next_run_time: setattr(self, "next_run_str", datetime.fromtimestamp(self.next_run_time).strftime('%I:%M%p %B %d, %Y'))
        else: setattr(self, "next_run_str", "")
        
        if self.last_run_time: setattr(self, "last_run_str", datetime.fromtimestamp(self.last_run_time).strftime('%I:%M%p %B %d, %Y'))
        else: setattr(self, "last_run_str", "")
        
        if self.last_success_time: setattr(self, "last_success_str", datetime.fromtimestamp(self.last_success_time).strftime('%I:%M%p %B %d, %Y'))
        else: setattr(self, "last_success_str", "")
        
        if self.last_fail_time: setattr(self, "last_fail_str", datetime.fromtimestamp(self.last_fail_time).strftime('%I:%M%p %B %d, %Y'))
        else: setattr(self, "last_fail_str", "")
        
        setattr(self, "json", dumps(self.__dict__))

    def __repr__(self):
        """Return a string representation of all the attributes of this job"""
        return ', '.join("%s: %s" % item for item in vars(self).items())    

    def initialize(self):
        """Call this when a job is inserted or updated"""
        self.set_next_run_time()
        self.set_modified_time()

    def update(self, column, value):
        """
        Update the value of a column in this job's row

        Args
            column: The column that will be updated
            value: The new value to be set
        """
        global postgres
        setattr(self, column, value)
        
        if value == None:
            query = "UPDATE jobs SET "+column+"=NULL"
        else:
            query = "UPDATE jobs SET "+column+"='"+str(value)+"'"
        
        cur = postgres.conn.cursor()
        try:
            cur.execute(query + " WHERE name='"+str(self.name)+"';")
            postgres.conn.commit()
            return True
        except:
            postgres.conn.rollback()
            return False

    def child_tasks(self):
        global postgres
        return postgres.get_tasks("parent_job", str(self.id))

    def queue(self, cause, username=None, mode=0):
        """
        Go through the process to mark a job as queued
        Different causes have a different queue process
        """
        # mode 0 = restart all
        if int(mode) == 0:
            for task in self.child_tasks():
                task.queue(cause, username)
                
        # mode 1 = restart failed
        elif int(mode) == 1:
            for task in self.child_tasks():
                if task.state == "failed":
                    task.queue(cause, username)
          
        # any other mode is invalid
        else:
            return False
        
        if cause == "cron":
            self.update("queued_by", "cron")
            self.update("failures", 0)
            self.update("next_run_time", None)
            self.update("state", "queued")
            
        elif cause == "misfire":
            self.update("queued_by", username)
            self.update("failures", 0)
                        
            if self.state == "running":
                self.update("next_state", "queued")

            elif self.state == "stopping":
                self.update("next_state", "queued")
            
            else:
                self.update("state", "queued")

    def warn(self, warning_message=None):
        if warning_message == None:
            if self.warning:
                self.update("warning", "false")
                self.update("warning_message", "")
                
        else:
            self.update("warning", "true")
            self.update("warning_message", warning_message)

    def ready(self):
        """Go through the process to mark a job as ready"""
        self.update("state", "ready")

    def starting(self):
        """Go through the process to mark a job as starting"""
        self.update("state", "starting")

    def running(self, run_id=0, agent_id=0):
        """
        Go through the process to mark a job as running
        Create an entry in the task_history table
        """
        self.update("run_id", run_id)
        self.update("count", self.count + 1)
        self.set_last_run_time()
        self.update("state", "running")
        
        # Log the run in the history table
        self.create_run(run_id, agent_id)

    def success(self):
        """Go through the process to mark a job as success"""
        if self.cron: self.set_next_run_time()
        self.warn(None)
        self.update("run_id", "")
        self.set_last_success_time()
        self.update("state", "success")
        
    def failed(self):
        """Go through the process to mark a job as failed"""
        if self.restartable: self.set_next_run_time()
        self.warn(None)
        self.update("run_id", "")
        self.update("failures", self.failures+1)
        self.set_last_fail_time()
        self.update("state", "failed")

    def stop(self):
        """
        Go through the process of stopping a job. This is done by stopping all the tasks
          that are contained within the job.
        """
        for task in self.child_tasks():
            task.stop()        
        
        self.warn(None)
        if self.state == "running":
            self.update("state", "stopping")
        else:
            if self.next_state:
                self.update("state", self.next_state)
                self.update("next_state", "")
            else:
                self.update("state", "stopped")

    def stopped(self):
        """
        Mark the job as stopped. Use this when a sub-task is stopped.
        """
        self.update("state", "stopped")
        
    def set_next_run_time(self, cron=None):
        """Use croniter to generate the next run time based on the cron schedule"""
        
        # If this is a child of another entity, it follows the parent's cron schedule
        if not self.parent_job == None:
            return False
          
        # Check twice. First set cron if it wasn't user-defined. Then check if it is still empty
        if not cron:
            cron = self.cron
            
        if not cron:
            if self.next_run_time:
                self.update("next_run_time", None)
            return
          
        new_iter = croniter(cron, datetime.now())
        next_run = int(mktime(new_iter.get_next(datetime).timetuple()))
        self.update("next_run_time", next_run)

    def set_last_run_time(self):
        """Set the last run time to now"""
        self.update("last_run_time", int(time()))

    def set_last_success_time(self):
        """Set the last success time to now"""
        self.update("last_success_time", int(time()))

    def set_last_fail_time(self):
        """Set the last failed time to now"""
        self.update("last_fail_time", int(time()))
    
    def set_modified_time(self):
        """Set the time the job was created or modified"""
        if self.creation_time:
            self.update("last_modified_time", int(time()))
        else:
            self.update("creation_time", int(time()))

    def check_next_run_time(self):
        """Check if the next run time has passed, queue the job if it has"""
        
        # If this is a child of another entity, it follows the parent's cron schedule
        if not self.parent_job == None:
            return False

         # Set the next run time if cron is set but the next run time is blank
        if not self.next_run_time:
            if self.cron:
                self.set_next_run_time()
            else:
                return False

        # Check that the current time has passed the run time
        elif self.next_run_time <= int(time()):
            self.queue("cron")
            return True

        # Run time hasn't passed or no cron is applied
        return False
    
    def disable(self):
        """
        Disable the job. Disabling hides the job from non-admin users and stops processing.
          To completely remove the job you need to use the purge function
        """
        for task in self.child_tasks():
            task.disable()        
        
        if self.state == "running":
            self.update("state", "disabling")
        else:
            self.update("state", "disabled")
            self.update("disabled_time", int(time()))
            
    def delete(self, mode=0):
        """
        Delete the job.
        
        Args:
            mode: 0 - Move all child tasks (default)
                  1 - Delete all child tasks
        """
        if int(mode) == 0:
            for task in self.child_tasks():
                task.update("parent_job", None)
        elif int(mode) == 1:
            for task in self.child_tasks():
                task.delete()
        
        global postgres
        query = "DELETE FROM jobs WHERE id=" + str(self.id) + ";"
        cur = postgres.conn.cursor()
        
        try:
            cur.execute(query)
            postgres.conn.commit()
            
        except:
            print "Could not delete job #" + str(self.id)
            postgres.conn.rollback()
            
    def create_run(self, run_id, agent_id):
        global postgres
        
        # TODO: make runs for jobs
        return
      
        # TODO: group runs with the parent
        #If this is a child of another entity, it shares a run with the parent
        #if not self.parent_job == None:
        #    return "child"

        query = "INSERT INTO task_history (" + \
                "run_id, task_id, name, description, dependencies, dependencies_str, command, entrypoint" + \
                ", recoverable_exitcodes, restartable, datavolumes" + \
                ", environment, imageuuid, cron, queued_by, agent_id, run_start_time, run_start_time_str, log" + \
                ") VALUES (" + \
                str(run_id) + \
                ", " + str(self.id) + \
                ", '" + self.name + \
                "', '" + self.description.replace("'","''") + \
                "', '" + "{" + ', '.join(self.dependencies) + "}" + \
                "', '" + ', '.join(self.dependencies) + \
                "', '" + self.command.replace("'","''") + \
                "', '" + self.entrypoint.replace("'","''") + \
                "', '" + "{" + ', '.join([str(i) for i in self.recoverable_exitcodes]) + "}" + \
                "', " + str(self.restartable) + \
                ", '" + "{" + ', '.join(self.datavolumes) + "}" + \
                "', '" + "{" + ', '.join(["{" + env[0] + "," + env[1].replace("'","''") + "}" for env in self.environment]) + "}" + \
                "', '" + self.imageuuid + \
                "', '" + self.cron + \
                "', '" + self.queued_by + \
                "', '" + str(agent_id) + \
                "', '" + str(self.last_run_time) + \
                "', '" + datetime.fromtimestamp(self.last_run_time).strftime('%I:%M%p %B %d, %Y') + \
                "', '" + self.name + "-" + str(run_id) + ".log" + \
                "');"

        cur = postgres.conn.cursor()
        try:
            cur.execute(query)
            postgres.conn.commit()
            
        except:
            print "Could not create an entry for run #" + str(run_id)
            postgres.conn.rollback()
            