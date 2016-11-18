"""
User defined Settings

TODO: save settings in the database
"""

import os
import yaml

global settings
settings = {}

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def check_agent():
    """Check that the Agent settings are proper"""
    global settings

    if 'agent_development_mode' not in settings.keys():
        set_setting("agent_development_mode", "false")

def check_amazon():
    """Check that the Amazon settings are proper"""
    global settings

    if 'ec2_scaling_enabled' not in settings.keys():
        set_setting("ec2_scaling_enabled", "false")

    if 'ec2_scale_limit' not in settings.keys():
        set_setting("ec2_scale_limit", "10")

    if 'spot_fleet_request_id' not in settings.keys():
        set_setting("ec2_scaling_enabled", "false")
        set_setting("spot_fleet_request_id", "")

def check_docker():
    """Check that the Docker settings are proper"""
    global settings

    if 'docker_log_directory' not in settings.keys():
        set_setting("docker_log_directory", "/logs")

    if 'docker_registry_url' not in settings.keys():
        set_setting("docker_registry_url", "")

    if 'docker_registry_username' not in settings.keys():
        set_setting("docker_registry_username", "")

    if 'docker_registry_password' not in settings.keys():
        set_setting("docker_registry_password", "")

def check_postgres():
    """Check that the postgres settings are set"""
    global settings, postgres
    
    if 'postgres_host' not in settings.keys():
        set_setting("postgres_host", postgres.postgres.host)
        
    if 'postgres_user' not in settings.keys():
        set_setting("postgres_user", postgres.postgres.user)
        
    if 'postgres_port' not in settings.keys():
        set_setting("postgres_port", postgres.postgres.port)
        
    if 'postgres_dbname' not in settings.keys():
        set_setting("postgres_dbname", postgres.postgres.dbname)

def check_slack():
    """Check that the Slack settings are proper"""
    global settings

    if 'slack_enabled' not in settings.keys():
        set_setting("slack_enabled", "false")

    if 'slack_webhook' not in settings.keys():
        set_setting("slack_enabled", "false")
        set_setting("slack_webhook", "")

def check_web_interface():
    """Check that the Authorization settings are proper"""
    global settings

    if 'web_use_auth' not in settings.keys():
        set_setting("web_use_auth", "false")

    if 'web_use_ssl' not in settings.keys():
        set_setting("web_use_ssl", "true")
        
    if 'web_github_oauth_id' not in settings.keys():
        set_setting("web_github_oauth_id", "")

    if 'web_github_oauth_secret' not in settings.keys():
        set_setting("web_github_oauth_secret", "")

    if 'web_ssl_cert_path' not in settings.keys():
        set_setting("web_ssl_cert_path", "cert.pem")

    if 'web_ssl_key_path' not in settings.keys():
        set_setting("web_ssl_key_path", "privkey.pem")

    if 'web_ssl_chain_path' not in settings.keys():
        set_setting("web_ssl_chain_path", "")

def load_settings():
    query = "SELECT setting_name, setting_value FROM settings;"
    result = postgres.execute(query)

    if result:
        for setting in result.fetchall():
            settings[setting[0]] = setting[1]
    else:
        print("Error: Couldn't load settings from database")
        exit()

def set_setting(setting_name, setting_value):
    if setting_name in settings.keys():
        query = "UPDATE settings SET setting_value='" + str(setting_value) + "' WHERE setting_name='" + setting_name + "';"
    else:
        query = "INSERT INTO settings VALUES ('" + setting_name + "', '" + str(setting_value) + "');"
        
    result = postgres.execute(query)
    
    if result:
        settings[setting_name] = setting_value
        return({"success": "Setting was updated"})
    else:
        return({"error": "Couldn't update setting"})

def set_settings(settings_name, values):
    if type(settings_name) is not list:
        return set_setting(settings_name, values)
    else:
        for i in range(len(settings_name)):
            set_setting(settings_name[i], values[i])
        
        for i in range(len(settings_name)):
            if not settings[settings_name[i]] == values[i]:
                return({"error": "Some settings failed to update"})
        
        return({"success": "Settings were updated"})
    
def get_settings():
    return settings

load_settings()
check_agent()
check_amazon()
check_docker()
check_postgres()
check_slack()
check_web_interface()