"""

"""
from time import time
from json import dumps

from postgres_functions import Postgres
global postgres
postgres = Postgres()

class Agent(object):
    def __init__(self, values):
        """ """
        global postgres
        for i in range(len(values)):
            setattr(self, postgres.agent_columns[i][0], values[i])

        # Set the JSON representation
        setattr(self, "json", dumps(self.__dict__))

    def update_state(self, state):
        """ """
        global postgres
        query = "UPDATE agents SET state = '" + state + "' WHERE agent_id='" + str(self.agent_id) + "';"
        postgres.execute(query)
        
    def update_run(self, run_id):
        """ """
        global postgres
        query = "UPDATE agents SET run = '" + str(run_id) + "' WHERE agent_id='" + str(self.agent_id) + "';"
        postgres.execute(query)
    
    def update_last_action(self, last_action):
        """ """
        global postgres
        
        query = "UPDATE task_history SET" + \
              " last_action='" + last_action + "'" + \
              " last_action_time=" + str(int(time())) + \
              " WHERE agent_id='" + str(self.agent_id) + "';"

        postgres.execute(query)
        
    def update_agent_termination_time(self, agent_termination_time=None):
        global postgres
        if agent_termination_time:
            query = "UPDATE agents SET agent_termination_time = '" + str(agent_termination_time) + "' WHERE agent_id='" + str(self.agent_id) + "';"
        else:
            query = "UPDATE agents SET agent_termination_time = '" + str(int(time())) + "' WHERE agent_id='" + str(self.agent_id) + "';"
        
        postgres.execute(query)