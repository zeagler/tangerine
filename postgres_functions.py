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
    def __init__(self, values):
        """
        Set the initial attributes of this task object

        Args:
            input: the results of a `SELECT *` query on the task table
        """
        cur = conn.cursor()
        cur.execute("select column_name from information_schema.columns where table_name='"+table+"';")
        columns = cur.fetchall()
          
        for i in xrange(len(columns)):
            setattr(self, columns[i][0], values[i])
    
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
        cur = conn.cursor()
        cur.execute("UPDATE "+table+" SET "+column+"='"+str(value)+"' WHERE name='"+str(self.name)+"';")
        conn.commit()
    
    def waiting_on_dependencies(self):
        """
        Check on the dependencies of this task.
        
        Any dependencies that are completed get moved to another column `satisfied_dependencies`
          if the `dependencies` column is empty this will return False. Otherwise it will be True
        
        Returns:
            A boolean that represents whether this task is still waiting on a dependency
        """
        
        # If the dependencies attribute is None, NULL, or empty this task is not waiting on any other task
        if not self.dependencies:
            return False
        
        cur = conn.cursor()
        cur.execute("SELECT name, state FROM "+table+" WHERE state='success' AND name=ANY(ARRAY"+str(self.dependencies)+");")
        completed_dependencies = cur.fetchall()
        
        # if any rows were returned they will be move to `satisfied_dependencies`
        if completed_dependencies:
            # Set satisfied_dependencies to an empty list if it is None
            if not self.satisfied_dependencies:
                self.satisfied_dependencies = []

            # loop through returned rows. dep[0] is the task name in each row
            for dep in completed_dependencies:
                self.dependencies.remove(dep[0])
                self.satisfied_dependencies.append(dep[0])
            
            self.update("dependencies", "{" + str(self.dependencies)[1:-1] + "}")
            self.update("satisfied_dependencies", "{" + str(self.satisfied_dependencies)[1:-1] + "}")
        
        # If dependencies exist this task is still waiting, otherwise it is not
        if self.dependencies:
            return True
        else:
            return False


def open_postgres_connection():
    """
    Open a persistant postgreSQL database connection.
    
    This uses the standard postgreSQL enviroment variables for the username, host,
      port, and database name. The password is retrieved through the .pgpass file
    """
    global conn
    print "Connecting to postgreSQL database"
    host = os.environ['PGHOST']
    user = os.environ['PGUSER']
    port = os.getenv('PGPORT', "5432")
    dbname = os.getenv('PGDATABASE', user)
    conn = psycopg2.connect("host="+host+" dbname="+dbname+" user="+user+" port="+port)

def close_postgres_connection():
    """Close the postgreSQL database connection"""
    print '\n\nclosing postgres connection'
    conn.close()

def create_task_database():
    """Create the task table in the postgreSQL database"""
    cur = conn.cursor()
    cur.execute("""
CREATE TABLE """+table+""" (
    name                     varchar(100)  PRIMARY KEY,
    state                    varchar(10)   NOT NULL DEFAULT 'queued',
    dependencies             integer[]     NOT NULL DEFAULT '{}',
    satisfied_dependencies   integer[]     NOT NULL DEFAULT '{}',
    command                  varchar[]     NOT NULL DEFAULT '{}',
    recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
    restartable              boolean       NOT NULL DEFAULT true,
    entrypoint               varchar[]     NOT NULL DEFAULT '{}',
    datavolumes              varchar[]     NOT NULL DEFAULT '{}',
    environment              varchar[][2]  NOT NULL DEFAULT '{}',
    imageuuid                varchar       NOT NULL,
    service_id               varchar(10)   NOT NULL DEFAULT '',
    failures                 integer       NOT NULL DEFAULT 0,
    cron                     varchar[]
);""")
    conn.commit()

def setup_postgres():
    """
    Connect to the postgreSQL database
    Create the task table if it does not exist
    """
    global table
    table = os.getenv('TASK_TABLE', "tangerine")
    open_postgres_connection()

    # Check if task table exists, create it if it does not
    cur = conn.cursor()
    cur.execute("select exists(select * from information_schema.tables where table_name='"+table+"')")
    if not cur.fetchone()[0]:
        create_task_database()

def get_tasks(column, value):
    """
    Get all tasks whose column matches input value
    
    Args:
        column: The column that will be searched
        value: The required value of the column
    
    Returns:
        A list of Task objects, one for each row that satisfies column=value
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM "+table+" WHERE "+column+"='"+value+"'")
    return [Task(row) for row in cur.fetchall()]