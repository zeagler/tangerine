"""
This module has functions to scale Spot Fleet Requests and terminate
  EC2 instances.
"""
from base64 import b64encode
from boto3 import client
from settings import settings

class Amazon():
    def __init__(self):
        if self.enabled():
            setattr(self, "ec2", client('ec2'))
            print("Connected to Amazon EC2")
        else:
            print("Spot Request scaling is disabled")

    def scale_spot_request(self, new_capacity):
        """
        Scale an Amazon EC2 Spot Fleet Request
        
        Args:
            new_capacity: The integer capacity you want to scale the request to
        """
        if self.enabled():
            if new_capacity > self.scale_limit():
                new_capacity = self.scale_limit()
            if new_capacity <= 0:
                new_capacity = 1
            
            request = self.ec2.modify_spot_fleet_request(
                SpotFleetRequestId=self.spot_fleet_request_id(),
                TargetCapacity=new_capacity,
                ExcessCapacityTerminationPolicy='noTermination'
            )

            if request['Return'] is True:
                print("Spot Fleet scaled to " + str(new_capacity) + " spot instances")
            else:
                print("Failed to scale Spot Request")

    def get_target_capacity(self):
        """Return the current target capacity of the Spot Request"""
        if self.enabled():
            response = self.ec2.describe_spot_fleet_requests(SpotFleetRequestIds=[self.spot_fleet_request_id()])    
            return response['SpotFleetRequestConfigs'][0]['SpotFleetRequestConfig']['TargetCapacity']
        else:
            return "disabled"

    def get_instance_id_by_ip(self, private_ip):
        """Return the instance ID of an EC2 Instance with the provided private ip"""
        if self.enabled():
            response = self.ec2.describe_instances(Filters=[{'Name': 'private-ip-address', 'Values': [private_ip]}])
            return response['Reservations'][0]['Instances'][0]['InstanceId']

    def terminate_instance(self, instance_id):
        """Terminate an EC2 instance"""
        if self.enabled():
            print("Terminating EC2 Instance " + instance_id)
            response = self.ec2.terminate_instances(InstanceIds=[instance_id])

    def enabled(self):
        return settings['ec2_scaling_enabled'] == "true"
      
    def scale_limit(self):
        return int(settings['ec2_scale_limit'])
      
    def spot_fleet_request_id(self):
        return settings['spot_fleet_request_id']
      
    def create_instance(self, profile):
        """
        Create a single EC2 instance
        
        Args:
            profile: The Tangerine instance profile to use when provisioning the EC2 instance

        Returns:
            The instance id of the created instance if on-demand
            The spot request id if spot instance
        """
        # TODO: Add a tag for the instance profile name and host id
        if self.enabled():
            if profile.spot_instance == True:
                response = create_spot_instance(profile)
                if response:
                    sir_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
                    if sir_id:
                        #TODO: Log spot instance request in postgres database
                        #      Monitor request until an instance is started
                      
                        #      Tag the instance on creation
                        #tag_instance(response['Instances'][0]['InstanceId'], "Name", profile.name_tag)
                        return sir_id
            else:
                response = create_on_demand_instance(profile)
                if response:
                    instance_id = response['Instances'][0]['InstanceId']
                    if instance_id:
                        tag_instance(instance_id, "Name", profile.name_tag)
                        return instance_id

    def create_spot_instance(self, profile):
        """
        Create a single EC2 spot instance
        
        Args:
            profile: The Tangerine instance profile to use when provisioning the EC2 instance

        Returns:
            The response of the spot instance request
        """
        # TODO: determine the subnet/AZ with the lowest cost
        if self.enabled():
            return ec2.request_spot_instances(
                DryRun=False,
                SpotPrice=profile.spot_price,
                InstanceCount=1,
                Type='one-time',
                LaunchSpecification={
                    'ImageId': profile.AMI,
                    'KeyName': profile.keyname,
                    'SecurityGroupIds': profile.security_groups,
                    'UserData': b64encode(profile.user_data),
                    'InstanceType': profile.instance_type,
                    'BlockDeviceMappings': [
                        {
                            'VirtualName': 'ebs0',
                            'DeviceName': '/dev/sda1',
                            'Ebs': {
                                'VolumeSize': profile.block_ebs_size,
                                'DeleteOnTermination': True,
                                'VolumeType': profile.block_ebs_type,
                            },
                        },
                    ],
                    'SubnetId': profile.subnet_id,
                    'IamInstanceProfile': {
                        'Name': profile.iam_profile_name
                    },
                    'EbsOptimized': False,
                    'Monitoring': {
                        'Enabled': False
                    },
                }
            )

    def create_on_demand_instance(self, profile):
        """
        Create a single on-demand EC2 instance
        
        Args:
            profile: The Tangerine instance profile to use when provisioning the EC2 instance
        """
        if self.enabled():
            return ec2.run_instances(
                DryRun=False,
                ImageId=profile.AMI,
                MinCount=1,
                MaxCount=1,
                KeyName=profile.keyname,
                SecurityGroupIds=profile.security_groups,
                UserData=profile.user_data,
                InstanceType=profile.instance_type,
                BlockDeviceMappings=[
                    {
                        'VirtualName': 'ebs0',
                        'DeviceName': '/dev/sda1',
                        'Ebs': {
                            'VolumeSize': profile.block_ebs_size,
                            'DeleteOnTermination': True,
                            'VolumeType': profile.block_ebs_type
                        },
                    },
                ],
                Monitoring={
                    'Enabled': False
                },
                SubnetId=profile.subnet_id,
                DisableApiTermination=False,
                InstanceInitiatedShutdownBehavior='stop',
                IamInstanceProfile={
                    'Name': profile.iam_profile_name
                },
                EbsOptimized=False
            )

    def tag_instance(self, instance_id, tag_key, tag_val):
        """
        Add a tag to an EC2 instance
        
        Args:
            instance_id: An string array of ids of the EC2 instances to add the tag to
            tag_key: The tag key
            tag_val: The tag value
        """
        if self.enabled():
            return ec2.create_tags(
                DryRun=False,
                Resources=[
                    instance_id,
                ],
                Tags=[
                    {
                        'Key': tag_key,
                        'Value': tag_val
                    },
                ]
            )