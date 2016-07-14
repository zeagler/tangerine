"""
This module has functions to connect to a postgreSQL database, and a class
  to represent each task.
"""
import psycopg2
import os

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
        for i in xrange(len(self.postgres.columns)):
            setattr(self, self.postgres.columns[i][0], values[i])
    
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
        cur = self.postgres.conn.cursor()
        cur.execute("UPDATE "+self.postgres.table+" SET "+column+"='"+str(value)+"' WHERE name='"+str(self.name)+"';")
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
        for task in self.postgres.tasks:
            if task.name in self.dependencies:
                if task.state == "success" or task.state == "cron":
                    completed_dependencies += 1

        if completed_dependencies == len(self.dependencies):
            return False
        else:
            return True


    def cron_is_satisfied(self, now):
        """
        Compare a cron configuration with a given time
        
        Args:
            now: An array of cron values of the current time [minute, hour, day of month, month, weekday]
            
        Returns: True if the time satisfies the cron configuration, otherwise False
        """
        for i in reversed(range(5)):
            if self.cron[i] == "*":
                continue

            # Parse cron lists and ranges
            else:
                expanded_cron = []
                for item in self.cron[i].split(","):
                    if "-" in item:
                        for item in range(int(item.split("-")[0]), int(item.split("-")[1])+1):
                            expanded_cron.append(str(item))
                    else:
                        expanded_cron.append(item)

                if str(now[i]) not in expanded_cron:
                    return False
                  
        return True


class Postgres():
    """
    Open a persistant postgreSQL database connection.
    
    This uses the standard postgreSQL enviroment variables for the username, password,
      host, port, and database name. The password is retrieved through the .pgpass file
      if it is not set as an enviroment variable.
    """
    def __init__(self):
        print "Connecting to postgreSQL database"
        setattr(self, "host", os.environ['PGHOST'])
        setattr(self, "user", os.environ['PGUSER'])
        setattr(self, "pswd", os.getenv('PGPASS', ''))
        setattr(self, "port", os.getenv('PGPORT', "5432"))
        setattr(self, "dbname", os.getenv('PGDATABASE', self.user))
        
        conn_str = "host="+self.host+" dbname="+self.dbname+" user="+self.user+" port="+self.port
        if self.pswd: conn_str += " password="+self.pswd

        setattr(self, "conn", psycopg2.connect(conn_str))
        setattr(self, "table", os.getenv('TASK_TABLE', "tangerine"))

        # Check if task table exists, create it if it does not
        cur = self.conn.cursor()
        cur.execute("select exists(select * from information_schema.tables where table_name='"+self.table+"')")
        if not cur.fetchone()[0]:
            cur.execute("""
            CREATE TABLE """+self.table+""" (
                name                     varchar(100)  PRIMARY KEY,
                state                    varchar(10)   NOT NULL DEFAULT 'queued',
                dependencies             varchar[]     NOT NULL DEFAULT '{}',
                command                  varchar[]     NOT NULL DEFAULT '{}',
                recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
                restartable              boolean       NOT NULL DEFAULT true,
                entrypoint               varchar[]     NOT NULL DEFAULT '{}',
                datavolumes              varchar[]     NOT NULL DEFAULT '{}',
                environment              varchar[][2]  NOT NULL DEFAULT '{}',
                imageuuid                varchar       NOT NULL,
                service_id               varchar(10)   NOT NULL DEFAULT '',
                failures                 integer       NOT NULL DEFAULT 0,
                max_failures             integer       NOT NULL DEFAULT 3,
                cron                     varchar[]
            );""")
            self.conn.commit()
            
        cur = self.conn.cursor()
        cur.execute("select column_name from information_schema.columns where table_name='"+self.table+"';")
        setattr(self, "columns", cur.fetchall())
        setattr(self, "tasks", [])
        self.refresh_tasks()
        
    def close_connection(self):
        """Close the postgreSQL database connection"""
        print '\n\nclosing postgres connection'
        self.conn.close()

    def get_tasks(self, column, value):
        """
        Get all tasks whose column matches input value
        
        Args:
            column: The column that will be searched
            value: The required value of the column
        
        Returns:
            A list of Task objects, one for each row that satisfies column=value
        """
        ret_val = []
        for task in self.tasks:
            if task.__dict__[column] == value:
                ret_val.append(task)
        return ret_val

    def refresh_tasks(self):
        """Refresh the in memory copy of the tasks"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM "+self.table)
        self.tasks = [Task(row, self) for row in cur.fetchall()]
        return