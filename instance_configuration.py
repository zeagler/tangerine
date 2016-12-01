"""
This module is used to create, validate and store an instance profile.

In terms of Tangerine an instance profile is a set of attributes used to provision
  EC2 instances on AWS. This includes AMI, type, storage, spot/demand, security groups
  IAM roles, user-data, and subnet.
"""
from time import time
from json import dumps
from base64 import b64encode

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def get_default():
    query = "SELECT * FROM instance_configurations WHERE default_configuration='true'"
    
    results = postgres.execute(query + " ;")
    
    if results:
        return [Host_Configuration(values=config) for config in results.fetchall()][0];
    else:
        return None

def get_configuration(id=None, name=None):
    query = "SELECT * FROM instance_configurations"
    
    if id:
        query += " WHERE id='"+str(id)+"'"
    elif name:
        query += " WHERE name='"+name+"'"
    
    results = postgres.execute(query + " ORDER BY id DESC;")
    
    if results:
        return [Host_Configuration(values=config) for config in results.fetchall()];
    else:
        return []

def create(
            name, ami, key, iam, ebssize,
            ebstype, userdata, instance_type, spot, bid,
            subnet, sg, tag, default
          ):
    """
    Create an instance configuration after validating the input.

    An EC2 instance configuration must contain the following attributes:
      AMI, This must be available to the AWS account.
      keyname, This must exists in the AWS account
      security_groups, This is a list of one or more existing security groups
      instance_type, This is a valid EC2 instance type
      block_ebs_size, (if applicable) The size of the EBS in GB
      block_ebs_type, (if applicable) The type of EBS - io1, gp2, st1 or sc1
      iam_profile_name, (optional) An existing IAM instance profile
      user_data, The user data to run on instance startup
      subnet_id, A list of one or more existing subnet ids
      spot_instance, (optional) A boolean to indicate whether a spot instance should be requested.
                                If a spot instance is being requested the instance type must be eligible for a spot instance
      spot_price, (optional) The maximum bid for the spot instance request.
                            If spot_instance is enabled the default is the on-demand price for the instance type
      name_tag, (optional) The name to add to the instance

    Args:
        configuration: The Host_Configuration object with the above attributes
    """
    
    if not name:
        return dumps({"error": "Name can not be blank"})
    elif len(get_configuration(name=name)) > 0:
        return {"error": "Name '" + name + "' conflicts with an existing configuration"}
      
    if not ami:
        return {"error": "AMI can not be blank"}

    if not key:
        return {"error": "Key can not be blank"}

    if not ebssize:
        return {"error": "EBS size can not be blank"}

    if not ebstype:
        return {"error": "EBS type must be set"}

    if not instance_type:
        return {"error": "Instance type must be set"}

    if (spot == "true") and not bid:
        return {"error": "Max bid must be set when using spot instances"}
      
    if not subnet:
        return {"error": "At least one subnet must be set"}
         
    # If tags is a list make it a string
    if tag == None:
        config_tags = ""
    else:
        if type(tag) is list:
            config_tags = ['{"' + t.split("=")[0] + '","' + t.split("=", 1)[1].replace("'", "''") + '"}' for t in tag]
            config_tags = ", ".join(config_tags)
        else:
            config_tags = '{"' + tag.split("=")[0] + '","' + tag.split("=", 1)[1].replace("'", "''") + '"}'
    
    # If security groups is a list make it a string
    if sg == None:
        security_groups = ""
    else:
        if type(sg) is list:
            security_groups = ", ".join(sg)
        else:
            security_groups = sg
    
    # If subnet is a list make it a string
    if type(subnet) is list:
        subnet_id = ", ".join(subnet)
    else:
        subnet_id = subnet
  
    if bid == None or bid == "":
        bid = '0.00'
  
    if default == "true":
        default_configuration = "true"
    else:
        default_configuration = "false"
      
      
    columns = {}
  
    columns["name"]    = name
    columns["AMI"]     = ami
    columns["keyname"] = key
    columns["instance_type"]  = instance_type
    columns["block_ebs_size"] = ebssize
    columns["block_ebs_type"] = ebstype
    columns["subnet_id"]      = "{"+subnet_id+"}"
    columns["default_configuration"] = default_configuration
    
    if not sg == None:                columns["security_groups"]   = "{"+security_groups+"}"
    if not tag == None:               columns["tags"]              = "{"+config_tags+"}"
    if not spot == None:              columns["spot_instance"]     = spot
    if not bid == None:               columns["spot_price"]        = bid
    if not iam == None:               columns["iam_profile_name"]  = iam
    if not userdata == None:          columns["user_data"]         = userdata.replace("'","''")
    if not userdata == None:          columns["user_data_base64"]  = b64encode(userdata.encode()).decode("utf-8")
  
    query = "INSERT INTO instance_configurations (" + ", ".join(columns.keys())  + ") VALUES (" + ", ".join("'" + str(val) + "'" for val in columns.values()) + ")"

    result = postgres.execute(query)
    
    if result:
        # check that the row was entered
        config = get_configuration(name=name)
        
        if len(config) > 0:
            if default_configuration == "true":
                postgres.execute("UPDATE instance_configurations SET default_configuration='false' WHERE name!='" + name + "';")
                
            return dumps(config[0].__dict__)
          
    return {"error": "Could not add configuration"}

def update(
            name, ami, key, iam, ebssize,
            ebstype, userdata, instance_type, spot, bid,
            subnet, sg, tag, id, default
          ):
    """
    Update an instance configuration after validating the input.
    """
    
    if not name:
        return dumps({"error": "Name can not be blank"})
    elif len(get_configuration(name=name)) > 1:
        return {"error": "Name '" + name + "' conflicts with an existing configuration"}
      
    if not ami:
        return {"error": "AMI can not be blank"}

    if not key:
        return {"error": "Key can not be blank"}

    if not ebssize:
        return {"error": "EBS size can not be blank"}

    if not ebstype:
        return {"error": "EBS type must be set"}

    if not instance_type:
        return {"error": "Instance type must be set"}

    if (spot == "true") and not bid:
        return {"error": "Max bid must be set when using spot instances"}
      
    if not subnet:
        return {"error": "At least one subnet must be set"}
         
    # If tags is a list make it a string
    if tag == None:
        config_tags = ""
    else:
        if type(tag) is list:
            config_tags = ['{"' + t.split("=")[0] + '","' + t.split("=", 1)[1].replace("'", "''") + '"}' for t in tag]
            config_tags = ", ".join(config_tags)
        else:
            config_tags = '{"' + tag.split("=")[0] + '","' + tag.split("=", 1)[1].replace("'", "''") + '"}'
    
    # If security groups is a list make it a string
    if sg == None:
        security_groups = ""
    else:
        if type(sg) is list:
            security_groups = ", ".join(sg)
        else:
            security_groups = sg
    
    # If subnet is a list make it a string
    if type(subnet) is list:
        subnet_id = ", ".join(subnet)
    else:
        subnet_id = subnet
  
    if bid == None or bid == "":
        bid = '0.00'
  
    if default == "true":
        default_configuration = "true"
    else:
        default_configuration = "false"
        
    columns = {}
  
    columns["name"]    = name
    columns["AMI"]     = ami
    columns["keyname"] = key
    columns["instance_type"]  = instance_type
    columns["block_ebs_size"] = ebssize
    columns["block_ebs_type"] = ebstype
    columns["subnet_id"]      = "{"+subnet_id+"}"
    columns["default_configuration"] = default_configuration
    
    if not sg == None:                columns["security_groups"]   = "{"+security_groups+"}"
    if not tag == None:               columns["tags"]              = "{"+config_tags+"}"
    if not spot == None:              columns["spot_instance"]     = spot
    if not bid == None:               columns["spot_price"]        = bid
    if not iam == None:               columns["iam_profile_name"]  = iam
    if not userdata == None:          columns["user_data"]         = userdata.replace("'","''")
    if not userdata == None:          columns["user_data_base64"]  = b64encode(userdata.encode()).decode("utf-8") 
  
    query = "UPDATE instance_configurations SET "
    query += ", ".join([column + "='" + columns[column] + "'" for column in columns])
    query += " WHERE id=" + str(id)

    result = postgres.execute(query + ";")
    
    if result:
        # TODO: Verify that the new column values match the update request
        # check that the row was entered
        config = get_configuration(name=name)
        
        if len(config) > 0:
            if default_configuration == "true":
                postgres.execute("UPDATE instance_configurations SET default_configuration='false' WHERE name!='" + name + "';")
                
            return dumps(config[0].__dict__)
          
    return {"error": "Could not update configuration"}

def delete(id):
    """Delete a configuration"""
    query = "DELETE FROM instance_configurations WHERE id=" + str(id)
    results = postgres.execute(query + ";")

    if len(get_configuration(id=id)) == 0:
        return {"success": "Configuration was deleted"}
    else:
        return {"error": "Configuration was not deleted"}

class Host_Configuration:
    def __init__(self, columns=None, values=None):
        global postgres
        
        if columns == None:
            columns = postgres.host_configuration_columns
          
        for i in range(len(values)):
            setattr(self, columns[i][0], values[i])
