"""
This module represents a user from the database
"""
from json import dumps

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def delete_user(userid):
    query = "DELETE FROM authorized_users WHERE userid='" + userid + "';"
    result = postgres.execute(query)
    
    if result:
        return({"success": "User was deleted"})
    else:
        return({"error": "Could not delete user"})
      
def update_user(userid, usertype):
    query = "UPDATE authorized_users SET usertype='" + usertype + "' WHERE userid='" + userid + "';"
    result = postgres.execute(query)
    
    if result:
        return({"success": "User type was updated"})
    else:
        return({"error": "Could not update user type"})

def add_user(username, userid, usertype):
    query = "INSERT INTO authorized_users (userid, username, usertype) VALUES('" + userid + "', '" + username + "', '" + usertype + "');"
    result = postgres.execute(query)
    
    if result:
        return({"success": "User was added"})
    else:
        return({"error": "Could not add user"})
  
def get_users(column=None, value=None):
    """
    Get information on users
    
    Args: 
        column: The column that will be searched
        value: The required value of the column
    
    Returns:
        A list of User objects, one for each row that satisfies column=value
    """
    query = "SELECT * FROM authorized_users"
    
    if column:
        query += " WHERE " + column + "='" + (value if value else "NULL") + "'"
    
    results = postgres.execute(query + ";")
          
    if results:
        return [User(postgres.user_columns, user) for user in results.fetchall()]
    else:
        return None
      
class User(object):
    def __init__(self, columns, values):
      """
      Set the initial attributes of this user object

      Args:
          input: the results of a `SELECT *` query on the user table
      """
      for i in range(len(values)):
          setattr(self, columns[i][0], values[i])

      setattr(self, "json", dumps(self.__dict__))