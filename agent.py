"""

"""
from time import time
from json import dumps

from postgres_functions import Postgres
global postgres
postgres = Postgres()
      
def get_agents():
    query = "SELECT * FROM agents WHERE state='active' OR state='bad_agent' OR agent_termination_time>" + str(time()-8*60*60) + " ORDER BY agent_id DESC;"
    agents = postgres.execute(query)
    
    if agents:
        return [Agent(agent) for agent in agents.fetchall()]
    else:
        return None

class Agent(object):
    def __init__(self, values):
        """ """
        global postgres
        for i in range(len(values)):
            setattr(self, postgres.agent_columns[i][0], values[i])

        # Set the JSON representation
        setattr(self, "json", dumps(self.__dict__))
        
        # Get the tasks ran by this agent
        setattr(self, "tasks", [{"name": run.name, "run_id": run.run_id, "result_state": run.result_state} for run in postgres.get_runs_by_agent(self.agent_id)])

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