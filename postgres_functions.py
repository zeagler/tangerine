"""
This module has functions to connect to a postgreSQL database
"""
from task import Task
from run import Run
from user import User
from postgres_connection import PGconnection
from postgres_database import verify_database

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

        verify_database(self.conn)

        # Get the column names        
        cur = self.conn.cursor()

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
    
    def load_queue(self, queue=None):
        """
        Load the queue with the id of all the tasks in the task table
        
        Args:
            queue: the queue to load. Valid queue are `task_queue` `ready_queue`
        """
        if not queue:
            return False
        elif queue == "ready_queue":
            condition = " WHERE state='ready';"
        else:
            condition = ""
        
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE " + queue + " IN ACCESS EXCLUSIVE MODE;")
        
        cur.execute("SELECT COUNT(id) FROM " + queue + ";")

        # if the queue still has tasks return nothing
        if cur.fetchone()[0]:
            self.conn.rollback()
        else:
            cur.execute("SELECT COUNT(id) FROM tangerine" + condition + ";")

            # If the task table is empty return nothing
            if not cur.fetchone()[0]:
                self.conn.commit()
                return
            
            cur.execute("SELECT id FROM tangerine" + condition + ";")
            ids = ("(" + str(id[0]) + ")" for id in cur.fetchall())
            cur.execute("INSERT INTO " + queue + " VALUES " + ", ".join(ids) + ";")
            self.conn.commit()
    
    def pop_queue(self, queue=None):
        """
        Pop the first task id from a queue
        
        Args:
            queue: The queue to pop. Valid queues are `task_queue` `ready_queue`
        """
        if not queue:
            return False
        
        cur = self.conn.cursor()
        cur.execute("LOCK TABLE " + queue + " IN ACCESS EXCLUSIVE MODE;")

        cur.execute("SELECT id FROM " + queue + " LIMIT 1;")
        row = cur.fetchone()
        self.conn.commit()
     
        if row:
            cur.execute("DELETE FROM " + queue + " WHERE id='"+str(row[0])+"';")
            return row[0]
        else:
            return False

    #
    # Runs
    #
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
      
    #
    # Users
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
    
    #
    # Agents
    #
    def reserve_next_agent_id(self):
        """Get the next valid agent id"""
        query = "SELECT NEXTVAL(pg_get_serial_sequence('agents', 'agent_id'))"
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]
    
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
        Return the information of agents matching the arguments
        
        Args:
            state: The state of the agent. Valid states are `active` `inactive` `bad_state`
            agent_id: The id of the agent, this will return only one agent.
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