"""
User defined Settings

TODO: save settings in the database
"""

import os
import yaml

global config, Amazon, Agent, Docker, Web, Postgresql, Slack, Rancher
config = yaml.safe_load(open(os.path.abspath(os.getcwd()) + "/config.yml"))

def check_agent():
    """Check that the Agent settings are proper"""
    global Agent
    Agent = config['Agent']
    
    if 'DEVELOPMENT' not in Agent.keys(): Agent['DEVELOPMENT'] = False
    
    if not Agent['DEVELOPMENT'] == True:   Agent['DEVELOPMENT'] = False

def check_amazon():
    """Check that the Amazon settings are proper"""
    global Amazon
    Amazon = config['Amazon']

    if 'ENABLED' not in Amazon.keys():               Amazon['ENABLED'] = False
    if 'EC2_SCALE_LIMIT' not in Amazon.keys():       Amazon['EC2_SCALE_LIMIT'] = 20
    if 'SPOT_FLEET_REQUEST_ID' not in Amazon.keys(): Amazon['ENABLED'] = False; Amazon['SPOT_FLEET_REQUEST_ID'] = ""

    if not Amazon['ENABLED']:                        Amazon['ENABLED'] = False
    if not Amazon['EC2_SCALE_LIMIT']:                Amazon['EC2_SCALE_LIMIT'] = 20
    if not Amazon['SPOT_FLEET_REQUEST_ID']:          Amazon['ENABLED'] = False; Amazon['SPOT_FLEET_REQUEST_ID'] = ""

def check_docker():
    """Check that the Docker settings are proper"""
    global Docker
    Docker = config['Docker']

def check_postgresql():
    """Check that the Postgresql settings are proper"""
    global Postgresql
    Postgresql = config['Postgresql']

    if 'PGHOST' not in Postgresql.keys():     print("PGHOST is not set"); exit(1)
    if 'PGUSER' not in Postgresql.keys():     print("PGUSER is not set"); exit(1)
    if 'PGPORT' not in Postgresql.keys():     Postgresql['PGPORT'] = "5432"
    if 'PGPASS' not in Postgresql.keys():     Postgresql['PGPASS'] = ""
    if 'PGDATABASE' not in Postgresql.keys(): Postgresql['PGDATABASE'] = Postgresql['PGUSER']
    if 'TASK_TABLE' not in Postgresql.keys(): Postgresql['TASK_TABLE'] = "tangerine"

    if not Postgresql['PGHOST']:              print("PGHOST is not set"); exit(1)
    if not Postgresql['PGUSER']:              print("PGUSER is not set"); exit(1)
    if not Postgresql['PGPORT']:              Postgresql['PGPORT'] = "5432"
    if not Postgresql['PGDATABASE']:          Postgresql['PGDATABASE'] = Postgresql['PGUSER']
    if not Postgresql['TASK_TABLE']:          Postgresql['TASK_TABLE'] = "tangerine"

def check_rancher():
    """Check that the Rancher settings are proper"""
    global Rancher
    Rancher = config['Rancher']

    if 'CATTLE_URL' not in Rancher.keys():           print("CATTLE_URL is not set"); exit(1)
    if 'CATTLE_ACCESS_KEY' not in Rancher.keys():    print("CATTLE_ACCESS_KEY is not set"); exit(1)
    if 'CATTLE_SECRET_KEY' not in Rancher.keys():    print("CATTLE_SECRET_KEY is not set"); exit(1)
    if 'HOST_LABEL' not in Rancher.keys():           Rancher['HOST_LABEL'] = "tangerine"
    if 'TASK_STACK' not in Rancher.keys():           Rancher['TASK_STACK'] = "Tangerine"
    if 'SIDEKICK_SCRIPT_PATH' not in Rancher.keys(): print("SIDEKICK_SCRIPT_PATH is not set"); exit(1)

    if not Rancher['CATTLE_URL']:                    print("CATTLE_URL is not set"); exit(1)
    if not Rancher['CATTLE_ACCESS_KEY']:             print("CATTLE_ACCESS_KEY is not set"); exit(1)
    if not Rancher['CATTLE_SECRET_KEY']:             print("CATTLE_SECRET_KEY is not set"); exit(1)
    if not Rancher['HOST_LABEL']:                    Rancher['HOST_LABEL'] = "tangerine"
    if not Rancher['TASK_STACK']:                    Rancher['TASK_STACK'] = "Tangerine"
    if not Rancher['SIDEKICK_SCRIPT_PATH']:          print("SIDEKICK_SCRIPT_PATH is not set"); exit(1)

def check_slack():
    """Check that the Slack settings are proper"""
    global Slack
    Slack = config['Slack']

    if 'ENABLED' not in Slack.keys():       Slack['ENABLED'] = False; Slack['SLACK_WEBHOOK'] = ""; return
    if 'SLACK_WEBHOOK' not in Slack.keys(): Slack['ENABLED'] = False; Slack['SLACK_WEBHOOK'] = ""; return

    if not Slack['ENABLED']:                Slack['ENABLED'] = False; Slack['SLACK_WEBHOOK'] = ""; return
    if not Slack['SLACK_WEBHOOK']:          Slack['ENABLED'] = False; Slack['SLACK_WEBHOOK'] = "";

def check_web_interface():
    """Check that the Authorization settings are proper"""
    global Web
    Web = config['Web']

    if 'USE_AUTH' not in Web.keys():              Web['USE_AUTH'] = True
    if 'GITHUB_OAUTH_ID' not in Web.keys():       print("GITHUB_OAUTH_ID is not set"); exit(1)
    if 'GITHUB_OAUTH_SECRET' not in Web.keys():   print("GITHUB_OAUTH_SECRET is not set"); exit(1)
    if 'SSL_CERTIFICATE' not in Web.keys():       print("SSL_CERTIFICATE is not set, SSL is required for now"); exit(1)
    if 'SSL_PRIVATE_KEY' not in Web.keys():       print("SSL_PRIVATE_KEY is not set, SSL is required for now"); exit(1)
    if 'SSL_CERTIFICATE_CHAIN' not in Web.keys(): Web['SSL_CERTIFICATE_CHAIN'] = ""

    if not Web['USE_AUTH'] == True:               Web['USE_AUTH'] = False
    if not Web['GITHUB_OAUTH_ID']:                print("GITHUB_OAUTH_ID is not set"); exit(1)
    if not Web['GITHUB_OAUTH_SECRET']:            print("GITHUB_OAUTH_ID is not set"); exit(1)
    if not Web['SSL_CERTIFICATE']:                print("SSL_CERTIFICATE is not set, SSL is required for now"); exit(1)
    if not Web['SSL_PRIVATE_KEY']:                print("SSL_PRIVATE_KEY is not set, SSL is required for now"); exit(1)

check_agent()
check_amazon()
check_docker()
check_postgresql()
check_rancher()
check_slack()
check_web_interface()