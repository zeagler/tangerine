"""
This module is a class used to represent a task.
"""
from time import mktime, strftime, time
from croniter import croniter
from datetime import datetime

class Task(object):
    """
    This class is used to represent and manipulate a row in the task table
    All columns of the table become attributes of this object

    Methods:
        update: Update this task's column in the postgreSQL task table
        waiting_on_dependencies: check if this task still has unmet dependencies
    """
    def __init__(self, values, postgres):
        """
        Set the initial attributes of this task object

        Args:
            input: the results of a `SELECT *` query on the task table
        """
        setattr(self, "postgres", postgres)
        for i in range(len(values)):
            setattr(self, self.postgres.columns[i][0], values[i])

        # Interpolate enviroment variables
        for i in range(len(self.environment)):
            self.environment[i][1] = self.environment[i][1].replace("$$count", str(self.count))
            self.environment[i][1] = self.environment[i][1].replace("$$date", strftime("%Y%m%d"))
            self.environment[i][1] = self.environment[i][1].replace("$$time", strftime("%H%M%S"))

        # For the web interface
        setattr(self, "dependencies_str", ', '.join(self.dependencies))
        if self.next_run_time:
            setattr(self, "next_run_str", datetime.fromtimestamp(self.next_run_time).strftime('%I:%M%p %B %d, %Y'))
        else:
            setattr(self, "next_run_str", "")

    def __repr__(self):
        """Return a string representation of all the attributes of this task"""
        return ', '.join("%s: %s" % item for item in vars(self).items())

    def update(self, column, value):
        """
        Update the value of a column in this task's row

        Args
            column: The column that will be updated
            value: The new value to be set
        """
        setattr(self, column, value)
        
        if value == None:
            query = "UPDATE "+self.postgres.table+" SET "+column+"=NULL"
        else:
            query = "UPDATE "+self.postgres.table+" SET "+column+"='"+str(value)+"'"
        
        cur = self.postgres.conn.cursor()
        cur.execute(query + " WHERE name='"+str(self.name)+"';")
        self.postgres.conn.commit()

    def waiting_on_dependencies(self):
        """
        Check on the dependencies of this task.

        Loop through the in-memory copy of the tasks to find the dependencies and their state.
          If any dependency is in the queued, ready, running or failed state this task
          is not ready to be scheduled.

        Returns:
            A boolean that represents whether this task is still waiting on a dependency
        """

        # If the dependencies attribute is None, NULL or empty
        #   this task is not waiting on any other task
        if not self.dependencies:
            return False

        completed_dependencies = 0
        for task in self.postgres.get_tasks():
            if task.name in self.dependencies:
                if task.state == "success" and task.check_next_run_time():
                    completed_dependencies += 1

        if completed_dependencies == len(self.dependencies):
            return False
        else:
            return True

    def queue(self, cause):
        """
        Go through the process to mark a task as queued
        Different causes have a different queue process
        """
        if cause == "failed":
            self.update("service_id", "")
            self.update("failures", self.failures+1)
            self.update("delay", self.reschedule_delay)
            self.set_last_fail_time()
            self.update("state", "queued")
        elif cause == "host" or cause == "container":
            self.update("service_id", "")
            self.update("state", "queued")
        elif cause == "cron":
            self.update("failures", 0)
            self.update("next_run_time", None)
            self.update("state", "queued")
        elif cause == "misfire":
            self.update("failures", 0)
            self.update("state", "queued")

    def ready(self):
        """Go through the process to mark a task as ready"""
        self.update("state", "ready")

    def running(self, service_id):
        """Go through the process to mark a task as running"""
        self.update("service_id", service_id)
        self.update("count", self.count + 1)
        self.set_last_run_time()
        self.update("state", "running")

    def success(self):
        """Go through the process to mark a task as success"""
        if self.cron: self.set_next_run_time()
        self.update("service_id", "")
        self.set_last_success_time()
        self.update("state", "success")

    def failed(self):
        """Go through the process to mark a task as failed"""
        self.update("service_id", "")
        self.update("failures", self.failures+1)
        self.set_last_fail_time()
        self.update("state", "failed")
        
    def stop(self):
        """Go through the process of stopping a task"""
        if self.state == "running":
            self.update("state", "stopping")
        else:
            self.update("service_id", "")
            self.update("state", "stopped")

    def set_next_run_time(self, cron=None):
        """Use croniter to generate the next run time based on the cron schedule"""
        
        # Check twice, first set cron if it wasn't user-defined, then check if it is still empty
        if not cron: cron = self.cron
        if not cron: return
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

    def check_next_run_time(self):
        """Check if the next run time has passed, queue the task if it has"""

         # Set the next run time if cron is set but the next run time is blank
        if not self.next_run_time:
            if self.cron:
                self.set_next_run_time()

        # Check that the current time has passed the run time
        elif self.next_run_time <= int(time()):
            self.queue("cron")
            return True

        # Run time hasn't passed or no cron is applied
        return False
