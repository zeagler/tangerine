"""
This module has functions to scale Spot Fleet Requests and terminate
  EC2 instances.
"""
import boto3
import os

class Amazon():
    def __init__(self):
        setattr(self, "ec2_scale_limit", os.getenv('EC2_SCALE_LIMIT', 20))
        setattr(self, "spot_fleet_request", os.getenv('SPOT_FLEET_REQUEST_ID', ""))
        
        if self.spot_fleet_request:
            print "Connecting to Amazon EC2"
            setattr(self, "aws_enabled", True)
            setattr(self, "ec2", boto3.client('ec2'))
        else:
            print "SPOT_FLEET_REQUEST_ID is not set, Spot Request scaling will be disabled"
            setattr(self, "aws_enabled", False)

    def scale_spot_request(self, new_capacity):
        """
        Scale an Amazon EC2 Spot Fleet Request
        
        Args:
            new_capacity: The integer capacity you want to scale the request to
        """
        if self.aws_enabled:
            if new_capacity > self.ec2_scale_limit:
                new_capacity = self.ec2_scale_limit
            if new_capacity <= 0:
                new_capacity = 1
            
            request = self.ec2.modify_spot_fleet_request(
                SpotFleetRequestId=self.spot_fleet_request,
                TargetCapacity=new_capacity,
                ExcessCapacityTerminationPolicy='noTermination'
            )

            if request['Return'] is True:
                print "Spot Fleet scaled to " + str(new_capacity) + " spot instances"
            else:
                print "Failed to scale Spot Request"

    def get_target_capacity(self):
        """Return the current target capacity of the Spot Request"""
        if self.aws_enabled:
            response = self.ec2.describe_spot_fleet_requests(SpotFleetRequestIds=[self.spot_fleet_request])    
            return response['SpotFleetRequestConfigs'][0]['SpotFleetRequestConfig']['TargetCapacity']
        else:
            return None

    def get_instance_id_by_ip(self, private_ip):
        """Return the instance ID of an EC2 Instance with the provided private ip"""
        if self.aws_enabled:
            response = self.ec2.describe_instances(Filters=[{'Name': 'private-ip-address', 'Values': [private_ip]}])
            return response['Reservations'][0]['Instances'][0]['InstanceId']

    def terminate_instance(self, instance_id):
        """Terminate an EC2 instance"""
        if self.aws_enabled:
            print "Terminating EC2 Instance " + instance_id
            response = self.ec2.terminate_instances(InstanceIds=[instance_id])

    # TODO Create function to scale auto-scaling group (for non spot-instance)



