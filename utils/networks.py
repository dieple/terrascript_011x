import boto3

from pprint import *
from utils import *


def get_vpc_id(region, tag_filter):

	ec2 = boto3.resource('ec2', region_name=region)
	client = boto3.client('ec2')

	vpc_tag_filter = [{'Name' : 'tag:Name','Values' : [tag_filter]}]
	vpc_id =  client.describe_vpcs(DryRun=False, Filters=vpc_tag_filter)['Vpcs'][0]['VpcId']

	return vpc_id


# retrieving either public, private or all subnets
def get_subnets (vpc_id, region, subnet_type, exclude_private_az=None):

	ec2 = boto3.client("ec2", region_name=region)
	vpc = ec2.describe_vpcs(VpcIds=[vpc_id])

	subnets = ec2.describe_subnets(Filters=[{ 'Name': 'vpc-id', 'Values': [vpc_id]}])
	# pprint("subnets: {0}\n".format(subnets))

	subnetIds = []
	if subnet_type == 'all':
		subnetIds = [x['SubnetId'] for x in subnets['Subnets']]
	elif subnet_type == 'public':
		subnetIds = [x['SubnetId'] for x in subnets['Subnets'] if x['MapPublicIpOnLaunch']==True]
	elif subnet_type == 'private' and exclude_private_az is None:
		subnetIds = [x['SubnetId'] for x in subnets['Subnets'] if x['MapPublicIpOnLaunch']==False]
	elif subnet_type == 'private' and exclude_private_az is not None:
		subnetIds = [x['SubnetId'] for x in subnets['Subnets'] if x['MapPublicIpOnLaunch']==False and x['AvailabilityZone'] != exclude_private_az]

	# print("subnetIds: {0}\n".format(subnetIds))
	return subnetIds


def get_availability_zones(region):
	ec2 = boto3.client("ec2", region_name=region)
	try:
		availability_zones = ec2.describe_availablity_zones()
		return [az["ZoneName"]
						for az in availability_zones["AvailabilityZones"]]
	except Exception:
		return ["eu-west-1a", "eu-west-1b", "eu-west-1c"]