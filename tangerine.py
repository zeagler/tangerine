"""
This program is used to schedule tasks onto hosts in conjunction with Rancher

The tasks are tracked through a table in a postgresql database, this
  allows the Tangerine instance to be restartable and replaceable
  without losing any task data.
"""

import sys

import settings
from agent_server import agent_server
from central_server import central_server
from postgres_functions import Postgres
from web_interface import start_web_interface

if __name__ == '__main__':
    print("Starting Tangerine")
    print("  postgreSQL table: " + settings.Postgresql['TASK_TABLE'])
    print("     Slack webhook: " + settings.Slack['SLACK_WEBHOOK'])
    print("Spot Fleet Request: " + settings.Amazon['SPOT_FLEET_REQUEST_ID'])
    
    if len(sys.argv) > 1:
        if (sys.argv[1] == "server"):
            print("Starting Server")
            status = central_server()
            
        elif (sys.argv[1] == "web"):
            print("Starting Web Interface")
            sys.argv[1] = ""
            status = start_web_interface(Postgres())
            
        elif (sys.argv[1] == "agent"):
            print("Starting Agent")
            status = agent_server()
          
        else:
            status = central_server()
    else:
        status = central_server()
        
    exit(status)