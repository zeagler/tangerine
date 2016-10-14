"""
This module is used to create, validate and store an instance profile.

In terms of Tangerine an instance profile is a set of attributes used to provision
  EC2 instances on AWS. This includes AMI, type, storage, spot/demand, security groups
  IAM roles, user-data, and subnet.
  

profile = Profile()
profile.AMI = 'ami-db4cf4cc'
profile.keyname = 'di-server-qa'
profile.security_groups = ['sg-3e279e45']
profile.instance_type = 't2.micro'
profile.block_ebs_size = 20
profile.block_ebs_type = 'gp2'
profile.iam_profile_name = 'di-server-iam-profile'
profile.user_date = ""\"sudo apt-get update
sudo apt-get install -y python-pip
sudo pip install boto3""\"

profile.subnet_id = 'subnet-5b1c7071'

profile.spot_instance = False
profile.spot_price = '0.05'
profile.name_tag = "Tangerine-test-instance"

"""
from time import time
from json import dumps
from base64 import b64encode

from postgres_functions import Postgres
global postgres
postgres = Postgres()

def create_ec2_configuration(
      name,
      AMI,
      keyname,
      security_groups,
      instance_type,
      block_ebs_size,
      block_ebs_type,
      iam_profile_name,
      user_data,
      subnet_id,
      spot_instance,
      spot_price,
      name_tag
    ):
  
    # Make an object with the input as attributes
    config = Host_Configuration(
                                  ['name', 'AMI','keyname','security_groups',
                                   'instance_type','block_ebs_size','block_ebs_type',
                                   'iam_profile_name','user_data','subnet_id','spot_instance',
                                   'spot_price','name_tag'],
      
                                  [name,AMI,keyname,security_groups,instance_type,
                                   block_ebs_size,block_ebs_type,iam_profile_name,user_data,
                                   subnet_id,spot_instance,spot_price,name_tag]
                                )

    result = validate_ec2_configuration(config)
    
    if result == True:
        return save_host_configuration(config)
    else:
        # return the error
        return result
    
def validate_ec2_configuration(configuration):
    """
    Ensure that a host configuration for an EC2 instance is proper.
    
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
    # Validation only needs to occur on the creation of a host configuration

    # TODO
    return True

def save_host_configuration(configuration):
    """
    Save a host configuration to the database
    
    Args:
        configuration: The Host_Configuration object
    """
    global postgres

    query = "INSERT INTO host_configurations (" + \
            "name,AMI,keyname,security_groups,instance_type,block_ebs_size," + \
            "block_ebs_type,iam_profile_name,user_data,user_data_base64," + \
            "subnet_id,spot_instance,spot_price,name_tag" + \
            ") VALUES (" + \
            "," + str(configuration.name) + \
            "," + str(configuration.AMI) + \
            "," + str(configuration.keyname) + \
            ", {" + ','.join([str(security_group) for security_group in configuration.security_groups)]) + "}" + \
            "," + str(configuration.instance_type) + \
            "," + str(configuration.block_ebs_size) + \
            "," + str(configuration.block_ebs_type) + \
            "," + str(configuration.iam_profile_name) + \
            "," + str(configuration.user_data) + \
            "," + str(b64encode(configuration.user_data)) + \
            ", {" + ','.join([str(subnet_id) for subnet_id in configuration.subnet_id)]) + "}" + \
            "," + str(configuration.spot_instance) + \
            "," + str(configuration.spot_price) + \
            "," + str(configuration.name_tag) + \
            "');"

    result = postgres.execute(query)

    if result == False:
        print "error creating host configuration. "
        print query
        return "{error: An error occured while attempting to create the host configuration}"
    else
        return result

def reserve_next_host_configuration_id():
    """Get the next host configuration id"""
    # 0.2.1: Not used
    global postgres
    query = "SELECT NEXTVAL(pg_get_serial_sequence('host_configurations', 'id'))"
    return postgres.execute(query)
      
class Host_Configuration:
    def __init__(self, columns=None, values):
        global postgres
        
        if columns == None:
            columns = postgres.host_configuration_columns
          
        for i in range(len(values)):
            setattr(self, columns[i][0], values[i])

        # Set the JSON representation
        setattr(self, "json", dumps(self.__dict__))
