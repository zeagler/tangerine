"""
This module has functions to connect to a postgreSQL database
"""
from psycopg2 import connect
from settings import Postgresql as options
from task import Task

class Postgres():
    """
    Open a persistant postgreSQL database connection.
    
    This uses the standard postgreSQL enviroment variables for the username, password,
      host, port, and database name. The password is retrieved through the .pgpass file
      if it is not set as an enviroment variable.
    """
    def __init__(self):
        setattr(self, "host", options['PGHOST'])
        setattr(self, "user", options['PGUSER'])
        setattr(self, "pswd", options['PGPASS'])
        setattr(self, "port", options['PGPORT'])
        setattr(self, "dbname", options['PGDATABASE'])
        setattr(self, "table", options['TASK_TABLE'])

        conn_str = "host="+self.host+" dbname="+self.dbname+" user="+self.user+" port="+str(self.port)
        if self.pswd: conn_str += " password="+self.pswd
        setattr(self, "conn", connect(conn_str))

        # Check if task table exists, create it if it does not
        cur = self.conn.cursor()
        cur.execute("select exists(select * from information_schema.tables where table_name='"+self.table+"')")
        if not cur.fetchone()[0]:
            self.create_task_table()

        # Check if the authorized user table exists, create it if it does not
        cur = self.conn.cursor()
        cur.execute("select exists(select * from information_schema.tables where table_name='authorized_users')")
        if not cur.fetchone()[0]:
            self.create_user_table()

        # Get the column names
        cur = self.conn.cursor()
        cur.execute("select column_name from information_schema.columns where table_name='"+self.table+"';")
        setattr(self, "columns", cur.fetchall())
        print("Connected to postgreSQL database")

    def close_connection(self):
        """Close the postgreSQL database connection"""
        print('\n\nclosing postgres connection')
        self.conn.close()
        
    def create_task_table(self):
        """Create the table to track tasks"""
        cur = self.conn.cursor()
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
            cron                     varchar(100)  NOT NULL DEFAULT '',
            next_run_time            integer,
            last_run_time            integer,
            last_success_time        integer,
            last_fail_time           integer,
            failures                 integer       NOT NULL DEFAULT 0,
            max_failures             integer       NOT NULL DEFAULT 3,
            service_id               varchar(10)   NOT NULL DEFAULT '',
            count                    integer       NOT NULL DEFAULT 0,
            delay                    integer       NOT NULL DEFAULT 0,
            reschedule_delay         integer       NOT NULL DEFAULT 5
        );""")
        self.conn.commit()
            
    #
    # Begin task queries
    #
    def get_tasks(self, column=None, value=None):
        """
        Get all tasks whose column matches input value
        
        Args:
            column: The column that will be searched
            value: The required value of the column
        
        Returns:
            A list of Task objects, one for each row that satisfies column=value
        """
        cur = self.conn.cursor()
        if column == None:
            cur.execute("SELECT * FROM "+self.table+";")
        elif value == None:
            cur.execute("SELECT * FROM "+self.table+" WHERE "+column+"='NULL';")
        else:
            cur.execute("SELECT * FROM "+self.table+" WHERE "+column+"='"+value+"';")
        
        ret_val = []
        for task in cur.fetchall():
            ret_val.append(Task(task, self))
        return ret_val
    
    def update_task(self, name, column, value):
        """Update a single task"""
        # TODO: ensure a lock is placed on the table
        
        # Stopping a task has extra steps
        if column == "state" and value == "stopped":
            self.stop_task(name)
            return True
        elif column == "state" and value == "queued":
            self.queue_task(name)
            return True
        else:
            cur = self.conn.cursor()
            
            if value == None:
                cur.execute("UPDATE "+self.table+" SET "+column+"=NULL WHERE name='"+name+"';")
            else:
                cur.execute("UPDATE "+self.table+" SET "+column+"='"+value+"' WHERE name='"+name+"';")
                
            self.conn.commit()

            cur = self.conn.cursor()
            
            # check that the row was updated
            cur.execute("SELECT "+column+" FROM "+self.table+" WHERE name='"+name+"';")
            if cur.fetchone()[0] == value:
                return True
            else:
                return False

    def add_task(self, name, state, dep, image, command, entrypoint, cron,
                 restartable, exitcodes, max_failures, delay, faildelay,
                 environment, datavolumes):
        """Insert a task into the table"""
        
        env = ["{" + e.split("=")[0] + "," + e.split("=")[1] + "}" for e in environment.split(",")]
        
        cur = self.conn.cursor()
        cur.execute("INSERT INTO "+self.table+"(name, state, dependencies, imageuuid, command, entrypoint, " + \
                                               "cron, restartable, recoverable_exitcodes, max_failures, delay, " + \
                                               "reschedule_delay, environment, datavolumes) " + \
                    "VALUES ('"+name+"','"+state+"','{"+dep+"}','"+image+"','{"+command.replace(" ", ",")+"}','{"+entrypoint.replace(" ", ",")+"}'," + \
                    "'"+cron+"',"+restartable+",'{"+exitcodes+"}','"+max_failures+"','"+delay+"','"+faildelay+"','{"+",".join(env)+"}','{"+datavolumes+"}');")
    
        self.conn.commit()
        
        # check that the row was entered
        cur.execute("SELECT name FROM "+self.table+" WHERE name='"+name+"';")
        if cur.fetchone()[0] == name:
            return True
        else:
            return False
        
    def queue_task(self, name):
        """Stop a task"""
        # TODO: ensure a lock is placed on the database table
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM "+self.table+" WHERE name='"+name+"';")
        task = Task(cur.fetchone(), self)
        task.queue("misfire")
        
    def stop_task(self, name):
        """Stop a task"""
        # TODO: ensure a lock is placed on the database table
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM "+self.table+" WHERE name='"+name+"';")
        task = Task(cur.fetchone(), self)
        task.stop()
    
    def delete_task(self, name):
        """Delete a task definition"""
        # TODO: ensure a lock is placed on the database table
        # TODO: you can only delete a stopped task
        
        cur = self.conn.cursor()
        cur.execute("DELETE FROM "+self.table+" WHERE name='"+name+"';")
        self.conn.commit()
        
        # check that the row was deleted
        cur.execute("SELECT name FROM "+self.table+" WHERE name='"+name+"';")
        if cur.fetchone()[0] == None:
            return True
        else:
            return False
        
    #
    # Begin tangerine administration queries
    #
    def create_user_table(self):
        """Create the table to store authorized users"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE authorized_users (
            userid    integer       PRIMARY KEY,
            username  varchar(100)  NOT NULL UNIQUE,
            usertype  varchar(10)   NOT NULL DEFAULT 'user'
        );""")
        self.conn.commit()

    def get_user(self, userid):
        """Get the informaton about the user"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM authorized_users WHERE userid='" + str(userid) + "';")
        return cur.fetchone()
        