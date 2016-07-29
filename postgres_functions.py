"""
This module has functions to connect to a postgreSQL database
"""
from task import Task
from user import User
from postgres_connection import PGconnection

class Postgres():
    """
    Open a persistant postgreSQL database connection.
    
    This uses the standard postgreSQL enviroment variables for the username, password,
      host, port, and database name. The password is retrieved through the .pgpass file
      if it is not set as an enviroment variable.
    """
    def __init__(self):
        postgres = PGconnection()
        setattr(self, "conn", postgres.conn)

        # Check if task table exists, create it if it does not
        cur = self.conn.cursor()
        cur.execute("select exists(select * from information_schema.tables where table_name='tangerine')")
        if not cur.fetchone()[0]:
            self.create_task_table()

        # Check if the authorized user table exists, create it if it does not
        cur = self.conn.cursor()
        cur.execute("select exists(select * from information_schema.tables where table_name='authorized_users')")
        if not cur.fetchone()[0]:
            self.create_user_table()

        # Get the column names
        cur = self.conn.cursor()
        
        cur.execute("select column_name from information_schema.columns where table_name='tangerine';")
        setattr(self, "columns", cur.fetchall())
        
        cur.execute("select column_name from information_schema.columns where table_name='authorized_users';")
        setattr(self, "user_columns", cur.fetchall())
            
    #
    # Begin task queries
    #
    def get_task(self, id=None, name=None):
        """Get the information of a task"""
        query = "SELECT * FROM tangerine WHERE "
        if id: query += "id='"+str(id)+"';"
        elif name: query += "name='"+name+"';"
        else: return None
        
        cur = self.conn.cursor()
        cur.execute(query)
        task = cur.fetchone()
        
        if task:
            return Task(self.columns, task);
        else:
            return None
      
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
            cur.execute("SELECT * FROM tangerine;")
        elif value == None:
            cur.execute("SELECT * FROM tangerine WHERE "+column+"='NULL';")
        else:
            cur.execute("SELECT * FROM tangerine WHERE "+column+"='"+value+"';")
        
        return [Task(self.columns, task) for task in cur.fetchall()]
    
    def add_task(self, name, state, dependencies, image, command, entrypoint, cron,
                 restartable, exitcodes, max_failures, delay, faildelay,
                 environment, datavolumes, port, description):
        """Insert a task into the table"""
        # TODO: try/catch rollback on commit
        # TODO: check input for validity
        if not name:
            return {"error": "Name can not be blank"}
        elif self.get_task(name=name):
                return {"error": "Name conflicts with existing task"}

        if not (state == "queued" or state == "waiting" or state == "stopped"):
            return {"error": "Requested state is not valid"}

        if not image:
            return {"error": "Image can not be blank"}
        elif " " in image:
            return {"error": "Image can not contain a space"}
          
        # TODO: Check dependencies, give a warning if one doesn't exist

        # Parse enviroment, datavolumes, ports, and dependencies     
        if environment:
            if type(environment) is list:
                env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1] + '"}' for e in environment]
                env = ", ".join(env);
            else:
                env = '{"' + environment.split("=")[0] + '","' + environment.split("=")[1] + '"}'
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
            
        if restartable == "on" or restartable == "true":
            rstr = "true"
        else:
            rstr = "false"
            
        cur = self.conn.cursor()
        cur.execute("INSERT INTO tangerine (id, name, description, state, dependencies, imageuuid, command, entrypoint, " + \
                                     "cron, restartable, recoverable_exitcodes, max_failures, delay, " + \
                                     "reschedule_delay, environment, datavolumes) " + \
                    "VALUES (DEFAULT, '"+name+"','"+description.replace("'","''")+"','"+state+"','{"+dep+"}','"+image+"','"+command+"','"+entrypoint+"'," + \
                    "'"+cron+"',"+rstr+",'{"+exitcodes+"}','"+max_failures+"','"+delay+"','"+faildelay+"','{"+env+"}','{"+dvl+"}');")
        self.conn.commit()
        
        # check that the row was entered
        task = self.get_task(name=name)
        
        if task:
            task.initialize()
            return task.__dict__
        else:
            return {"error": "Could not add task"}

    def update_task(self, id, name, state, dependencies, image, command, entrypoint, cron,
                    restartable, exitcodes, max_failures, delay, faildelay,
                    environment, datavolumes, port, description):
        """Insert a task into the table"""
        # TODO: try/catch rollback on commit
        # TODO: check input for validity
        if not id:
            return {"error": "Task ID must be provided when updating a task"}
      
        task = self.get_task(id)
        
        if not name:
            return {"error": "Name can not be blank"}
        elif not name == task.name:
            if self.get_task(name=name):
                return {"error": "Name conflicts with another task"}

        if not image:
            return {"error": "Image can not be blank"}
        elif " " in image:
            return {"error": "Image can not contain a space"}
          
        # TODO: Check dependencies, give a warning if one doesn't exist

        # Parse enviroment, datavolumes, ports, and dependencies     
        if environment:
            if type(environment) is list:
                env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1] + '"}' for e in environment]
                env = ", ".join(env);
            else:
                env = '{"' + environment.split("=")[0] + '","' + environment.split("=")[1] + '"}'
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
            
        if restartable == "on" or restartable == "true":
            rstr = "true"
        else:
            rstr = "false"
            
        cur = self.conn.cursor()
        cur.execute("UPDATE tangerine SET " + \
                      "name='" + name + \
                    "', description='" + description.replace("'","''") + \
                    "', dependencies='{" + dep + \
                    "}', imageuuid='" + image + \
                    "', command='" + command + \
                    "', entrypoint='" + entrypoint + \
                    "', cron='" + cron + \
                    "', restartable=" + rstr + \
                    ", recoverable_exitcodes='{" + exitcodes + \
                    "}', max_failures='" + max_failures + \
                    "', delay='" + delay + \
                    "', reschedule_delay='" + faildelay + \
                    "', environment='{" + env + \
                    "}', datavolumes='{" + dvl + \
                    "}' WHERE id="+str(id)+";")
        self.conn.commit()

        task.initialize()
        return task.__dict__

    def queue_task(self, name):
        """Stop a task"""
        # TODO: ensure a lock is placed on the database table
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tangerine WHERE name='"+name+"';")
        task = Task(self.columns, cur.fetchone())
        task.queue("misfire")
        
    def stop_task(self, name):
        """Stop a task"""
        # TODO: ensure a lock is placed on the database table
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tangerine WHERE name='"+name+"';")
        task = Task(self.columns, cur.fetchone())
        task.stop()

    #
    # Begin tangerine administration queries
    #
    def get_users(self, column=None, value=None):
        """
        Get information on users
        
        Args: 
            column: The column that will be searched
            value: The required value of the column
        
        Returns:
            A list of User objects, one for each row that satisfies column=value
        """
        cur = self.conn.cursor()
        query = "SELECT * FROM authorized_users"
        if column:
            query += " WHERE " + column + "='" + (value if value else "NULL") + "'"
        
        cur.execute(query+";")
        return [User(self.user_columns, user) for user in cur.fetchall()]

    #
    # Create tables
    # TODO: functions to modify table columns when needed
    #
    def create_task_table(self):
        """Create the table to track tasks"""
        # TODO: try/catch rollback on commit
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE tangerine (
            id                       serial        PRIMARY KEY,
            name                     varchar(100)  NOT NULL UNIQUE,
            description              varchar,
            state                    varchar(10)   NOT NULL DEFAULT 'queued',
            dependencies             varchar[]     NOT NULL DEFAULT '{}',
            command                  varchar       NOT NULL DEFAULT '',
            recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
            restartable              boolean       NOT NULL DEFAULT true,
            entrypoint               varchar       NOT NULL DEFAULT '',
            datavolumes              varchar[]     NOT NULL DEFAULT '{}',
            environment              varchar[][2]  NOT NULL DEFAULT '{}',
            imageuuid                varchar       NOT NULL,
            cron                     varchar(100)  NOT NULL DEFAULT '',
            next_run_time            integer,
            last_run_time            integer,
            last_success_time        integer,
            last_fail_time           integer,
            creation_time            integer,
            last_modified_time       integer,
            failures                 integer       NOT NULL DEFAULT 0,
            max_failures             integer       NOT NULL DEFAULT 3,
            service_id               varchar(10)   NOT NULL DEFAULT '',
            count                    integer       NOT NULL DEFAULT 0,
            delay                    integer       NOT NULL DEFAULT 0,
            reschedule_delay         integer       NOT NULL DEFAULT 5,
            disabled_time            integer
        );""")
        self.conn.commit()
    
    def create_user_table(self):
        """Create the table to store authorized users"""
        # TODO: try/catch rollback on commit
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE authorized_users (
            userid    integer       PRIMARY KEY,
            username  varchar(100)  NOT NULL UNIQUE,
            usertype  varchar(10)   NOT NULL DEFAULT 'user'
        );""")
        self.conn.commit()

    def create_task_history_table(self):
        #TODO
        print "WIP"
    
    def create_options_table(self):
        #TODO
        print "WIP"

    def create_host_table(self):
        #TODO
        print "WIP"
    
    def create_notifications_table(self):
        #TODO
        print "WIP"
        