"""
This module has functions to connect to a postgreSQL database
"""
from task import Task
from run import Run
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
        cur.execute("select exists(select * from information_schema.tables where table_name='authorized_users')")
        if not cur.fetchone()[0]:
            self.create_user_table()

        # Check if the shared task queue exists, create it if it does not
        cur.execute("select exists(select * from information_schema.tables where table_name='task_queue')")
        if not cur.fetchone()[0]:
            self.create_task_queue()

        # Check if the shared ready queue exists, create it if it does not
        cur.execute("select exists(select * from information_schema.tables where table_name='ready_queue')")
        if not cur.fetchone()[0]:
            self.create_ready_queue()

        # Check if the task history table exists, create it if it does not
        cur.execute("select exists(select * from information_schema.tables where table_name='task_history')")
        if not cur.fetchone()[0]:
            self.create_task_history_table()

        # Check if the agent table exists, create it if it does not
        cur.execute("select exists(select * from information_schema.tables where table_name='agents')")
        if not cur.fetchone()[0]:
            self.create_agent_table()

        # Get the column names        
        cur.execute("select column_name from information_schema.columns where table_name='tangerine';")
        setattr(self, "columns", cur.fetchall())
        
        cur.execute("select column_name from information_schema.columns where table_name='authorized_users';")
        setattr(self, "user_columns", cur.fetchall())
        
        cur.execute("select column_name from information_schema.columns where table_name='task_history';")
        setattr(self, "task_history_columns", cur.fetchall())
        
        cur.execute("select column_name from information_schema.columns where table_name='agents';")
        setattr(self, "agent_columns", cur.fetchall())
        
        self.conn.commit()
    
    def execute(self, query):
        """Try to execute a query, rollback on error"""
        cur = self.conn.cursor()
        try:
            cur.execute(query)
            self.conn.commit()
            return cur
        except:
            self.conn.rollback()
            return False
        
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
        self.conn.commit()
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
        
        self.conn.commit()
        return [Task(self.columns, task) for task in cur.fetchall()]

    def add_task(self, name, state, dependencies, image, command, entrypoint, cron,
                 restartable, exitcodes, max_failures, delay, faildelay,
                 environment, datavolumes, port, description):
        """Insert a task into the table"""
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
                env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1].replace("'", "''") + '"}' for e in environment]
                env = ", ".join(env);
            else:
                env = '{"' + environment.split("=")[0] + '","' + environment.split("=")[1].replace("'", "''") + '"}'
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

        query = "INSERT INTO tangerine (id, name, description, state, dependencies, imageuuid, command, entrypoint, " + \
                                       "cron, restartable, recoverable_exitcodes, max_failures, delay, " + \
                                       "reschedule_delay, environment, datavolumes) " + \
                "VALUES (DEFAULT, '"+name+"','"+description.replace("'","''")+"','"+state+"','{"+dep+"}','"+image+"','"+command.replace("'", "''")+"','"+entrypoint.replace("'", "''")+"'," + \
                "'"+cron+"',"+restartable+",'{"+exitcodes+"}','"+max_failures+"','"+delay+"','"+faildelay+"','{"+env+"}','{"+dvl+"}');"
        
        if self.execute(query):            
            # check that the row was entered
            task = self.get_task(name=name)
            
            if task:
                task.initialize()
                return task.__dict__

        return {"error": "Could not add task"}

    def update_task(self, id, name, state, dependencies, image, command, entrypoint, cron,
                    restartable, exitcodes, max_failures, delay, faildelay,
                    environment, datavolumes, port, description):
        """Insert a task into the table"""
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
                env = ['{"' + e.split("=")[0] + '","' + e.split("=")[1].replace("'", "''") + '"}' for e in environment]
                env = ", ".join(env);
            else:
                env = '{"' + environment.split("=")[0] + '","' + environment.split("=")[1].replace("'", "''") + '"}'
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
            
        query = "UPDATE tangerine SET " + \
                "name='" + name + \
                "', description='" + description.replace("'","''") + \
                "', dependencies='{" + dep + \
                "}', imageuuid='" + image + \
                "', command='" + command.replace("'", "''") + \
                "', entrypoint='" + entrypoint.replace("'", "''") + \
                "', cron='" + cron + \
                "', restartable=" + restartable + \
                ", recoverable_exitcodes='{" + exitcodes + \
                "}', max_failures='" + max_failures + \
                "', delay='" + delay + \
                "', reschedule_delay='" + faildelay + \
                "', environment='{" + env + \
                "}', datavolumes='{" + dvl + \
                "}' WHERE id="+str(id)+";"

        if self.execute(query):            
            # check that the row was entered
            task = self.get_task(name=name)
            task.initialize()
            return task.__dict__

        return {"error": "Could not update task"}

    def queue_task(self, name):
        """Queue a task"""
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tangerine WHERE name='"+name+"';")
        self.conn.commit()
        task = Task(self.columns, cur.fetchone())
        task.queue("misfire")
        
    def stop_task(self, name):
        """Stop a task"""
        
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tangerine WHERE name='"+name+"';")
        self.conn.commit()
        task = Task(self.columns, cur.fetchone())
        task.stop()
    
    def load_ready_queue(self):
        """Load the task queue with the id of all the tasks in the task table"""
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE ready_queue IN ACCESS EXCLUSIVE MODE;")
        
        cur.execute("SELECT COUNT(id) FROM ready_queue;")

        # if the task queue still has tasks return nothing
        if cur.fetchone()[0]:
            self.conn.rollback()
        else:
            cur.execute("SELECT COUNT(id) FROM tangerine WHERE state='ready';")

            # If the task table is empty return nothing
            if not cur.fetchone()[0]:
                self.conn.commit()
                return
            
            cur.execute("SELECT id FROM tangerine WHERE state='ready';")
            ids = ("(" + str(id[0]) + ")" for id in cur.fetchall())
            cur.execute("INSERT INTO ready_queue VALUES " + ", ".join(ids) + ";")
            self.conn.commit()
    
    def load_task_queue(self):
        """Load the task queue with the id of all the tasks in the task table"""
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE task_queue IN ACCESS EXCLUSIVE MODE;")
        
        cur.execute("SELECT COUNT(id) FROM task_queue;")

        # if the task queue still has tasks return nothing
        if cur.fetchone()[0]:
            self.conn.rollback()
        else:
            cur.execute("SELECT COUNT(id) FROM tangerine;")

            # If the task table is empty return nothing
            if not cur.fetchone()[0]:
                self.conn.commit()
                return
            
            cur.execute("SELECT id FROM tangerine;")
            ids = ("(" + str(id[0]) + ")" for id in cur.fetchall())
            cur.execute("INSERT INTO task_queue VALUES " + ", ".join(ids) + ";")
            self.conn.commit()
        
    def pop_task_queue(self):
        """Pop the first task id from the processing queue"""
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE task_queue IN ACCESS EXCLUSIVE MODE;")

        cur.execute("SELECT id FROM task_queue LIMIT 1;")
        row = cur.fetchone()
     
        if row:
            id = row[0]
            cur.execute("DELETE FROM task_queue WHERE id='"+str(id)+"';")
        else:
            id = False

        self.conn.commit()
        
        return id
        
    def pop_ready_queue(self):
        """Pop the first task id from the ready queue"""
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE ready_queue IN ACCESS EXCLUSIVE MODE;")

        cur.execute("SELECT id FROM ready_queue LIMIT 1;")
        row = cur.fetchone()
     
        if row:
            id = row[0]
            cur.execute("DELETE FROM ready_queue WHERE id='"+str(id)+"';")
        else:
            id = False

        self.conn.commit()
        
        return id
      
    def get_run(self, id):
        """Get the information of a run"""
        if not id:
            return None
          
        query = "SELECT * FROM task_history WHERE run_id='"+str(id)+"';"
        
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        run = cur.fetchone()
        
        if run:
            return Run(self.task_history_columns, run);
        else:
            return None
      
    def get_runs(self):
        """Get the information of a run"""
        if not id:
            return None
          
        query = "SELECT run_id, name, result_state, run_finish_time_str FROM task_history;"
        
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()

        col = [['run_id'], ['name'], ['result_state'], ['run_finish_time_str']]
        runs = [Run(col, run) for run in cur.fetchall()]
        
        return runs
    
    def reserve_next_run_id(self):
        """Get the next valid run id"""
        query = "SELECT NEXTVAL(pg_get_serial_sequence('task_history', 'run_id'))"
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def reserve_next_agent_id(self):
        """Get the next valid agent id"""
        query = "SELECT NEXTVAL(pg_get_serial_sequence('agents', 'agent_id'))"
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]
      
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
        self.conn.commit()
        return [User(self.user_columns, user) for user in cur.fetchall()]
    
    def add_agent(self, agent_id, host_ip, agent_port, instance_id,
                  instance_type, available_memory, agent_creation_time, agent_key):
        """
        """
        query = "INSERT INTO agents (" + \
                "agent_id, host_ip, agent_port, instance_id, instance_type, " + \
                "available_memory, agent_creation_time, state, agent_key" + \
                ") VALUES (" + \
                "'" + str(agent_id) + \
                "', '" + host_ip + \
                "', '" + str(agent_port) + \
                "', '" + instance_id + \
                "', '" + instance_type + \
                "', '" + str(available_memory) + \
                "', '" + str(agent_creation_time) + \
                "', '" + "active" + \
                "', '" + agent_key + \
                "');"

        if not self.execute(query):
            print "Could not create an entry for the agent on host " + host_ip
            return False
    
    def get_agents(self, state=None, agent_id=None):
        """
        """
        query = "SELECT * FROM agents"
      
        if state:
            query += " WHERE state='" + state + "'"
        elif agent_id:
            query += " WHERE agent_id='" + str(agent_id) + "'"
        
        response = self.execute(query + ";")
        
        if response:
            if agent_id:
                return response.fetchall()[0]
            else:
                return response.fetchall()
        else:
            return False
    
    #
    # Create tables
    # TODO: functions to modify table columns when needed
    #
    def create_task_table(self):
        """Create the table to track tasks"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE tangerine (
            id                       serial        PRIMARY KEY,
            name                     varchar(100)  NOT NULL UNIQUE,
            description              varchar,
            state                    varchar(10)   NOT NULL DEFAULT 'queued',
            next_state               varchar(10),
            dependencies             varchar[]     NOT NULL DEFAULT '{}',
            command                  varchar       NOT NULL DEFAULT '',
            entrypoint               varchar       NOT NULL DEFAULT '',
            recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
            restartable              boolean       NOT NULL DEFAULT true,
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
            queued_by                varchar       NOT NULL DEFAULT '',
            service_id               varchar(10)   NOT NULL DEFAULT '',
            run_id                   integer,
            count                    integer       NOT NULL DEFAULT 0,
            delay                    integer       NOT NULL DEFAULT 0,
            reschedule_delay         integer       NOT NULL DEFAULT 5,
            disabled_time            integer
        );""")
        self.conn.commit()
    
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

    def create_task_queue(self):
        """Create the table to be used as a queue for tangerine in HA"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE task_queue (
            id integer
        );""")
        self.conn.commit()

    def create_ready_queue(self):
        """Create the table to be used as a queue for tangerine in HA"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE ready_queue (
            id integer
        );""")
        self.conn.commit()
        
    def create_task_history_table(self):
        """Create the table to store task run history"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE task_history (
            run_id                   serial        PRIMARY KEY,
            task_id                  integer       NOT NULL,
            name                     varchar(100)  NOT NULL,
            description              varchar,
            result_state             varchar(10),
            result_exitcode          integer,
            dependencies             varchar[]     NOT NULL,
            dependencies_str         varchar,
            command                  varchar       NOT NULL,
            entrypoint               varchar       NOT NULL,
            recoverable_exitcodes    integer[]     NOT NULL,
            restartable              boolean       NOT NULL,
            datavolumes              varchar[]     NOT NULL,
            environment              varchar[][2]  NOT NULL,
            imageuuid                varchar       NOT NULL,
            cron                     varchar(100)  NOT NULL,
            queued_by                varchar       NOT NULL,
            run_start_time           integer,
            run_finish_time          integer,
            run_start_time_str       varchar,
            run_finish_time_str      varchar,
            elapsed_time             varchar,
            max_cpu                  varchar,
            max_memory               varchar,
            max_network_in           varchar,
            max_network_out          varchar,
            max_diskio_in            varchar,
            max_diskio_out           varchar,
            time_scale               varchar[]     NOT NULL DEFAULT '{}',
            cpu_history              varchar[]     NOT NULL DEFAULT '{}',
            memory_history           varchar[]     NOT NULL DEFAULT '{}',
            network_in_history       varchar[]     NOT NULL DEFAULT '{}',
            network_out_history      varchar[]     NOT NULL DEFAULT '{}',
            disk_in_history          varchar[]     NOT NULL DEFAULT '{}',
            disk_out_history         varchar[]     NOT NULL DEFAULT '{}',
            log                      varchar
        );""")
        self.conn.commit()
    
    def create_options_table(self):
        #TODO
        print "WIP"

    def create_host_table(self):
        #TODO
        print "WIP"
    
    def create_agent_table(self):
        """Create the table to store agent history"""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE agents (
            agent_id                 serial        PRIMARY KEY,
            host_ip                  varchar       NOT NULL,
            agent_port               varchar,
            instance_id              varchar,
            instance_type            varchar,
            available_memory         varchar,
            agent_creation_time      integer,
            agent_termination_time   integer,
            run                      varchar       DEFAULT '',
            last_action              varchar       DEFAULT '',
            last_action_time         integer,
            state                    varchar       DEFAULT 'active',
            agent_key                varchar
        );""")
        self.conn.commit()
        
    def create_notifications_table(self):
        #TODO
        print "WIP"
        