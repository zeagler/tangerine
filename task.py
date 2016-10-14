"""
This module is a class used to represent a task.
"""
from time import mktime, strftime, time
from croniter import croniter
from datetime import datetime
from json import dumps
import copy

from postgres_connection import PGconnection
global postgres
postgres = PGconnection()

class Task(object):
    """
    This class is used to represent and manipulate a row in the task table
    All columns of the table become attributes of this object

    Methods:
        update: Update this task's column in the postgreSQL task table
        waiting_on_dependencies: check if this task still has unmet dependencies
    """
    def __init__(self, columns, values):
        """
        Set the initial attributes of this task object

        Args:
            input: the results of a `SELECT *` query on the task table
        """
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
          
        setattr(self, "environment_raw", copy.deepcopy(self.environment))
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
        """Return a string representation of all the attributes of this task"""
        return ', '.join("%s: %s" % item for item in vars(self).items())    

    def initialize(self):
        """Call this when a task is inserted or updated"""
        self.set_next_run_time()
        self.set_modified_time()

    def update(self, column, value):
        """
        Update the value of a column in this task's row

        Args
            column: The column that will be updated
            value: The new value to be set
        """
        global postgres
        setattr(self, column, value)
        
        if value == None:
            query = "UPDATE "+postgres.table+" SET "+column+"=NULL"
        else:
            query = "UPDATE "+postgres.table+" SET "+column+"='"+str(value)+"'"
        
        cur = postgres.conn.cursor()
        try:
            cur.execute(query + " WHERE name='"+str(self.name)+"';")
            postgres.conn.commit()
            return True
        except:
            postgres.conn.rollback()
            return False

    def waiting_on_dependencies(self):
        """
        Check on the dependencies of this task.

        Loop through the in-memory copy of the tasks to find the dependencies and their state.
          If any dependency is in the queued, ready, running or failed state this task
          is not ready to be scheduled.

        Returns:
            A boolean that represents whether this task is still waiting on a dependency
        """
        global postgres
        # If the dependencies attribute is None, NULL or empty
        #   this task is not waiting on any other task
        if not self.dependencies:
            return False
          
        # Check that a task is not dependent on itself
        if self.name in self.dependencies:
            self.warn("Task is dependent on itself")
            return True
          
        for tag in self.tags:
            if "tag:" + tag in self.dependencies:
                self.warn("Task is dependent on itself by the tag `" + tag + "`")
                return True

        cur = postgres.conn.cursor()

        # Make a list of the task's dependencies
        dependencies = ["'" + dep + "'" for dep in self.dependencies if not dep[0:4] == "tag:"]
        if dependencies:
            dep_names = " name IN (" + ",".join(dependencies) + ") "
        else:
            dep_names = " "

        dep_tags = " OR ".join(["tags @> '{" + tag[4:] + "}' " for tag in self.dependencies if tag[0:4] == "tag:"])
        if dependencies and dep_tags:
            query_conditions = dep_names + " OR " + dep_tags
        elif dependencies:
            query_conditions = dep_names
        elif dep_tags:
            query_conditions = dep_tags
        else:
            query_conditions = ""

        # Select the task dependencies
        query = "SELECT name, state, next_run_time, parent_job, tags FROM tangerine WHERE " + query_conditions + ";"
        
        try:
            cur.execute(query)
            postgres.conn.commit()
        except:
            postgres.conn.rollback()
            print("Error: error executing query `" + query + "`")
            return True
          
        tasks = cur.fetchall()
        
        # Check that the tasks exist
        if tasks == None or tasks == False:
            print("Error: Something went wrong getting dependencies for the task '" + self.name + "'\nQuery: `" + query + "`")
            return True
        else:
            dep = [task[0] for task in tasks]
            missing = [task for task in self.dependencies if task not in dep and not task[0:4] == "tag:"]
            
            if missing:
                self.warn("Task is dependent on tasks that do not exist: " + ",".join(missing))
                return True
        
        is_blocked = False
        
        # Loop through the tasks to evaluate their state
        for task in tasks:
            # This will catch errors for tasks that are explicitly included as dependencies
            if not task[3] == self.parent_job:
                if task[0] in self.dependencies:
                    # This task was not included by a tag, but an explicit dependency
                    # The task does not share the same parent, making it an invalid dependency
                    self.warn("Task is dependent on a task `" + task[0] + "` which does not have the same parent")
                    return True
                else:
                    # This task is included by a tag, but does not share the same parent and should not be evaluated
                    continue

            if task[1] == "success" and (task[2] is None or task[2] > int(time())):
                # This task is not blocking execution
                continue
              
            elif task[1] == "failed" or task[1] == "stopped":
                # This task is blocking execution and the user needs to be warned about it
                self.warn("Task is dependent on a " + task[1] + " task: " + task[0])
                return True
              
            else:
                # Any state other than `success` is blocking execution.
                # This doesn't return immediately because the above condition can still
                #   warn the user about problems
                is_blocked = True
        
        # If the previous loop finished there were no warnings for blocked tasks
        self.warn(None)
        return is_blocked

    def warn(self, warning_message=None):
        if warning_message == None:
            if self.warning:
                self.update("warning", "false")
                self.update("warning_message", "")
        
        elif warning_message == self.warning_message:
            return
        else:
            print("Warning: '" + self.name + "' - " +  warning_message)
            self.update("warning", "true")
            self.update("warning_message", warning_message)

    def queue(self, cause, username=None):
        """
        Go through the process to mark a task as queued
        Different causes have a different queue process
        """
        if cause == "failed":
            self.update("queued_by", "auto-restart")
            self.update("failures", self.failures+1)
            self.update("delay", self.reschedule_delay)
            self.set_last_fail_time()
            self.update("state", "queued")
            
        elif cause == "host" or cause == "container":
            self.update("queued_by", "auto-restart")
            self.update("state", "queued")
            
        elif cause == "cron":
            self.update("queued_by", "cron")
            self.update("failures", 0)
            self.update("next_run_time", None)
            self.update("state", "queued")
            
        elif cause == "misfire":
            self.update("queued_by", username)
            self.update("failures", 0)

            if self.state == "running":
                self.update("next_state", "queued")
                self.stop()
                
            elif self.state == "stopping":
                self.update("next_state", "queued")
            
            else:
                self.update("state", "queued")

    def ready(self):
        """Go through the process to mark a task as ready"""
        self.warn(None)
        self.update("state", "ready")

    def starting(self):
        """Go through the process to mark a task as starting"""
        self.warn(None)
        self.update("state", "starting")

    def running(self, run_id, agent_id):
        """
        Go through the process to mark a task as running
        Create an entry in the task_history table
        """
        self.warn(None)
        self.update("run_id", run_id)
        self.update("count", self.count + 1)
        self.set_last_run_time()
        self.update("state", "running")
        
        # Log the run in the history table
        self.create_run(run_id, agent_id)

    def success(self):
        """Go through the process to mark a task as success"""
        if self.cron: self.set_next_run_time()
        self.warn(None)
        self.update("run_id", "")
        self.set_last_success_time()
        self.update("state", "success")
        
    def failed(self):
        """Go through the process to mark a task as failed"""
        self.warn(None)
        self.update("run_id", "")
        self.update("failures", self.failures+1)
        self.set_last_fail_time()
        self.update("state", "failed")
        
    def stop(self):
        """Go through the process of stopping a task"""
        self.warn(None)
        if self.state == "running":
            self.update("state", "stopping")
        else:
            if self.next_state:
                self.update("state", self.next_state)
                self.update("next_state", "")
            else:
                self.update("state", "stopped")

    def set_next_run_time(self, cron=None):
        """Use croniter to generate the next run time based on the cron schedule"""
        
        # If this is a child of another entity, it follows the parent's cron schedule
        if not self.parent_job == None:
            return
        
        # Check twice, first set cron if it wasn't user-defined, then check if it is still empty
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
        """Set the time the task was created or modified"""
        if self.creation_time:
            self.update("last_modified_time", int(time()))
        else:
            self.update("creation_time", int(time()))

    def check_next_run_time(self):
        """Check if the next run time has passed, queue the task if it has"""

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
        Disable the task. Disabling hides the task from non-admin users and stops processing,
          to completely remove the task you need to use the purge function
        """
        if self.state == "running":
            self.update("state", "disabling")
        else:
            self.update("state", "disabled")
            self.update("disabled_time", int(time()))
            
    def delete(self):
        """
        Delete the task.
        """
        if self.state == "running":
            self.update("state", "deleting")
        else:
            global postgres
            query = "DELETE FROM tangerine WHERE id=" + str(self.id) + ";"
            cur = postgres.conn.cursor()
            
            print(query)
            
            try:
                cur.execute(query)
                postgres.conn.commit()
                
            except:
                print "Could not delete task #" + str(self.id)
                postgres.conn.rollback()
            
    def create_run(self, run_id, agent_id):
        global postgres
        
        # TODO: group runs with the parent
        #If this is a child of another entity, it shares a run with the parent
        #if not self.parent_job == None:
        #    return "child"

        query = "INSERT INTO task_history (" + \
                "run_id, task_id, name, description, tags, dependencies, dependencies_str, command, entrypoint" + \
                ", recoverable_exitcodes, restartable, datavolumes" + \
                ", environment, imageuuid, cron, queued_by, agent_id, run_start_time, run_start_time_str, log" + \
                ") VALUES (" + \
                str(run_id) + \
                ", " + str(self.id) + \
                ", '" + self.name + \
                "', '" + self.description.replace("'","''") + \
                "', '" + "{" + ', '.join(self.tags) + "}" + \
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
            print "Error running query: " + query
            print "Could not create an entry for run #" + str(run_id)
            postgres.conn.rollback()
            