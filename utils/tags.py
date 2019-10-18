import boto3
from collections import MutableMapping



def create_eks_tags(cluster_name, vpc_id, private_subnets, public_subnets):

    keyName = "kubernetes.io/cluster/{0}".format(cluster_name)
    ec2 = boto3.client('ec2')

    ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': keyName, 'Value': 'shared'}])
    ec2.create_tags(Resources=private_subnets, Tags=[{'Key': keyName, 'Value': 'shared'}, {'Key': 'kubernetes.io/role/internal-elb', 'Value': '1'}])
    ec2.create_tags(Resources=public_subnets, Tags=[{'Key': keyName, 'Value': 'shared'}, {'Key': 'kubernetes.io/role/elb', 'Value': '1'}, {'Key': 'kubernetes.io/role/alb-ingress', 'Value': ''}])


def merge_tags(dictionary1, dictionary2):
    output = {}
    for item, value in dictionary1.iteritems():
        if dictionary2.has_key(item):
            if isinstance(dictionary2[item], dict):
                output[item] = combineDicts(value, dictionary2.pop(item))
        else:
            output[item] = value
    for item, value in dictionary2.iteritems():
        output[item] = value
    return output