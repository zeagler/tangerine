"""
This module creates a connection to a postgreSQL database
"""
from postgres_database import verify_database
from psycopg2 import connect
import os
import yaml

global connections, options

connections = []
options = yaml.safe_load(open(os.path.abspath(os.getcwd()) + "/config.yml"))["Postgresql"]

def close_connections():
    """Close the postgreSQL database connections"""
    print('\n\nclosing postgres connections')
    for connection in connections:
        connection.conn.close()

class PGconnection():
    """
    Open a persistant postgreSQL database connection.
    
    This uses the standard postgreSQL enviroment variables for the username, password,
      host, port, and database name. The password is retrieved through the .pgpass file
      if it is not set as an enviroment variable.
    """
    def __init__(self):
        global connections, options
        connections.append(self)
        
        setattr(self, "host", options['PGHOST'])
        setattr(self, "user", options['PGUSER'])
        setattr(self, "pswd", options['PGPASS'])
        setattr(self, "port", options['PGPORT'])
        setattr(self, "dbname", options['PGDATABASE'])
        setattr(self, "table", options['TASK_TABLE'])

        conn_str = "host="+self.host+" dbname="+self.dbname+" user="+self.user+" port="+str(self.port)
        if self.pswd: conn_str += " password="+self.pswd
        setattr(self, "conn_str", conn_str)
        self.reconnect()
        verify_database(self.conn)
        
    def reconnect(self):
        """Connect to the postgres database"""
        setattr(self, "conn", connect(self.conn_str))        