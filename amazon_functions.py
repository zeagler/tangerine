"""
This module has functions to scale Spot Fleet Requests and terminate
  EC2 instances.
"""
from boto3 import client
from os import getenv, environ
from settings import Amazon as options

class Amazon():
    def __init__(self):
        if self.enabled():
            setattr(self, "ec2", client('ec2'))
            print "Connected to Amazon EC2"
        else:
            print "Spot Request scaling is disabled"

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
                print "Spot Fleet scaled to " + str(new_capacity) + " spot instances"
            else:
                print "Failed to scale Spot Request"

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
            print "Terminating EC2 Instance " + instance_id
            response = self.ec2.terminate_instances(InstanceIds=[instance_id])

    def enabled(self):
        return options['ENABLED']
      
    def scale_limit(self):
        return options['EC2_SCALE_LIMIT']
      
    def spot_fleet_request_id(self):
        return options['SPOT_FLEET_REQUEST_ID']

    # TODO Create function to scale auto-scaling group (for non spot-instance)



