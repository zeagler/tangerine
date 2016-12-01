"""
This module contains functions to fetch and manage jobs, and holds the class that is used
  to represent a job as an object.
"""
from time import mktime, strftime, time
from json import dumps
from uuid import uuid4
from hashlib import sha1
from datetime import datetime
import hmac

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def get_hooks(id=None, api_token=None, action=None, state=None, target=None):
    """
    Retrieves a list of hooks that match the request
    
    Args:
        id: The id of a hook, returns a list with a single hook
        api_token: The api token associated with a hook, returns a list with a single hook
        action: The action associated with a hook, returns a list with every hook that uses the action
        target: The target associated with a hook, returns a list with every hook that has the target
    """
    query = "SELECT * FROM hooks"
    
    if not id == None:
        query += " WHERE id='"+str(id)+"'"
    elif not api_token == None:
        query += " WHERE api_token='"+str(api_token)+"'"
    elif not action == None:
        query += " WHERE action='"+str(action)+"'"
    elif not target == None:
        query += " WHERE target='"+str(target)+"'"
    elif not state == None:
        query += " WHERE state='"+str(state)+"'"

    results = postgres.execute(query + " ORDER BY id DESC;")
    
    if results:
        return [Hook(values = hook) for hook in results.fetchall()];
    else:
        return None

def delete_hook(id):
    """Delete a hook"""
    query = "DELETE FROM hooks WHERE id=" + str(id)
    results = postgres.execute(query + ";")

    if len(get_hooks(id=id)) == 0:
        return {"success": "Hook was deleted"}
    else:
        return {"error": "Hook was not deleted"}

def deactivate_hook(id):
    """Deactivate a hook"""
    hook = get_hooks(id)[0]
    
    if hook:
        return hook.deactivate()
    else:
        return None

def activate_hook(id):
    """Activate a hook"""
    hook = get_hooks(id)[0]
    
    if hook:
        return hook.activate()
    else:
        return None

def create_hook(name, action, targets):
    """
    Create a new hook.
    """
    if name == None:
        return {"error": "Name can not be empty"}
    
    if not action in ["misfire"]:
        return {"error": "The requested action is not supported by webhooks yet"}

    if type(targets) is list:
        tar = ", ".join(targets)
    else:
        tar = targets

    token = generate_token()
    columns = {}
    
    columns["name"] = name
    columns["action"] = action
    columns["targets"] = "{"+tar+"}"
    columns["state"] = "active"
    columns["api_token"] = token
    columns["created"] = int(time())

    query = "INSERT INTO hooks (" + ", ".join(columns.keys())  + ") VALUES (" + ", ".join("'" + str(val) + "'" for val in columns.values()) + ")"

    result = postgres.execute(query)
    
    if result:
        # check that the row was entered
        hook = get_hooks(api_token=token)[0]
        
        if hook:
            return hook.__dict__
          
    return {"error": "Could not add hook"}

def generate_token():
    token = hmac.new(uuid4().bytes, digestmod=sha1).hexdigest()
    
    # ensure a unique key is generated
    while len(get_hooks(api_token=token)) > 0:
        token = hmac.new(uuid4().bytes, digestmod=sha1).hexdigest()
    
    return token

class Hook(object):
    """
    This class is used to represent and manipulate a webhook in the hook table.
    All columns of the table become attributes of this object

    Methods:
        deactivate
        activate
    """
    def __init__(self, columns=None, values=None):
        """
        Set the initial attributes of this job object

        Args:
            columns: A list with the columns of this hook. The default value will become every
                     column from the postgres table in the order they exist in the table.

            values: A list of column values of this hook. The order of
                    the values needs to be the same as the `columns` list.
        """
        global postgres
        
        if columns == None:
            # This loop runs for tuples (returned by psycopg)
            columns = postgres.hook_columns
                
            for i in range(len(values)):
                setattr(self, columns[i][0], values[i])
        else:
            # This loop runs for lists
            for i in range(len(values)):
                setattr(self, columns[i], values[i])
                
        if self.last_used: setattr(self, "last_used_str", datetime.fromtimestamp(self.last_used).strftime('%I:%M:%S%p %B %d, %Y'))
        else: setattr(self, "last_used_str", "")

    def set_last_used(self):
        global postgres
        query = "UPDATE hooks SET last_used=" + str(int(time())) + " WHERE id=" + str(self.id) + ";"
        postgres.execute(query)

    def deactivate(self):
        """
        Deavtivate this hook.
        """
        global postgres
        query = "UPDATE hooks SET state='inactive' WHERE id=" + str(self.id) + ";"
        results = postgres.execute(query)
        
        if results:
            return {"success": "Hook was deactivated"}
        else:
            return {"error": "Could not deactivate hook"}

    def activate(self):
        """
        Reavtivate this hook.
        """
        global postgres
        query = "UPDATE hooks SET state='active' WHERE id=" + str(self.id) + ";"
        results = postgres.execute(query)
        
        if results:
            return {"success": "Hook was reactivated"}
        else:
            return {"error": "Could not reactivate hook"}