import json
import boto3

import settings

from utils import *
from networks import *
from tags import *

from pathlib import Path
from functools import reduce


# setup some dynamic required fields
def process_eks(ts, input_kwargs, label, aws_account_data, src_data, backend_data, module_built_by_terrascript):

  region = settings.region
  environment =  settings.environment
  vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']

  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
  data_vpc = module(name_="data_vpc", **remote_data_kwargs)
  ts.add(data_vpc)

  # iam role remote data:

  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_eks_worker", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_eks_worker']
  remote_data_kwargs["region"] = region
  data_iam_role_eks_worker= module(name_="data_iam_role_eks_worker", **remote_data_kwargs)
  ts.add(data_iam_role_eks_worker)

  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_eks_cluster", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_eks_cluster']
  remote_data_kwargs["region"] = region
  data_iam_role_eks_cluster= module(name_="data_iam_role_eks_cluster", **remote_data_kwargs)
  ts.add(data_iam_role_eks_cluster)

  # core security group remote data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "core_security_group", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_core_security_group']
  remote_data_kwargs["region"] = region
  data_core_security_group = module(name_="data_core_security_group", **remote_data_kwargs)
  ts.add(data_core_security_group)

  # efs remote data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "efs", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_efs']
  remote_data_kwargs["region"] = region
  data_efs = module(name_="data_efs", **remote_data_kwargs)
  ts.add(data_efs)


  if is_empty(input_kwargs["cluster_name"]):
    input_kwargs["cluster_name"] = label.id

  input_kwargs["tags"] = label.tags
  input_kwargs["efs_dns"] = data_efs.dns_name
  input_kwargs["iam_instance_profile_name"] = data_iam_role_eks_worker.profile_name
  input_kwargs["vpc_id"] = data_vpc.vpc_id
  input_kwargs["worker_security_group_id"] = data_core_security_group.eks_worker_sg
  input_kwargs["cluster_security_group_id"] = data_core_security_group.eks_cluster_sg
  input_kwargs["cluster_iam_role_name"] = data_iam_role_eks_cluster.name

  # since terrascript object (ts), is a runtime evaluation object model, we have to resort to boto3
  # to fetch networking upfront for manipulations of below:
  tag_filter = input_kwargs["vpc_tag_filter"]
  filtered_vpc_id = get_vpc_id(region, tag_filter)

  all_subnets = get_subnets(filtered_vpc_id, region, 'all')
  public_subnets = get_subnets(filtered_vpc_id, region, 'public')

  if vpc_built_by_terrascript:
    # key_pair remote data:
    remote_data_kwargs = {}
    remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "ssh_key_pair", module_built_by_terrascript)
    remote_data_kwargs["source"] = src_data[environment]['source']['data_ssh_key_pair']
    remote_data_kwargs["region"] = region
    data_ssh_key_pair = module(name_="data_ssh_key_pair", **remote_data_kwargs)
    ts.add(data_ssh_key_pair)

    input_kwargs["key_name"] = data_ssh_key_pair.key_name
    input_kwargs["ssh_cidr_block"] = [data_vpc.vpc_cidr_block] + input_kwargs["ssh_cidr_block"]

    private_subnets = get_subnets(filtered_vpc_id, region, 'private')

  else:
    input_kwargs["key_name"] = data_vpc.key_name
    input_kwargs["ssh_cidr_block"] = [data_vpc.vpc_cidr] + input_kwargs["ssh_cidr_block"]

    # transit is not setup correctly for azc - so workers in "eu-west-1c" cannot connect to EKS cluster
    private_subnets = get_subnets(filtered_vpc_id, region, 'private', 'eu-west-1c')

  input_kwargs["private_subnets"] = private_subnets
  input_kwargs["subnets"] = all_subnets

  del input_kwargs["vpc_tag_filter"]
  # print ("input_kwargs: {0}\n".format(input_kwargs))
  return input_kwargs


# post kubectl config
def eks_post_install_config(args, backend_data, src_data, module_built_by_terrascript=True):

  environment = settings.environment
  vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']

  if not args['tfdestroy'] and args['tfapply']:

    bucket, key = get_remote_state_bucket_and_key(backend_data, "eks", module_built_by_terrascript)
    eks_outputs = parse_s3_remote_data(bucket, key, '/tmp/eks_terraform.tfstate')

    bucket, key = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
    vpc_outputs = parse_s3_remote_data(bucket, key, '/tmp/vpc_terraform.tfstate')

    home = str(Path.home())
    cm_config_file = home + "/.kube/aws-auth-cm-{0}.yaml".format(environment)
    kube_config_file = home + "/.kube/config-{0}".format(environment)

    bucket, key = get_remote_state_bucket_and_key(backend_data, "iam_role_eks_worker", module_built_by_terrascript)
    data_iam_role_eks_worker = parse_s3_remote_data(bucket, key, '/tmp/iam_role_eks_worker_terraform.tfstate')

    worker_iam_role_arn = data_iam_role_eks_worker['modules'][0]['outputs']['arn']['value']
    kubeconfig_filename = eks_outputs['modules'][0]['outputs']['kubeconfig_filename']['value']
    config_map_aws_auth_filename = eks_outputs['modules'][0]['outputs']['config_map_aws_auth_filename']['value']
    cluster_id = eks_outputs['modules'][0]['outputs']['cluste' \
                                                      'r_id']['value']

    vpc_id = vpc_outputs['modules'][0]['outputs']['vpc_id']['value']
    private_subnets = vpc_outputs['modules'][0]['outputs']['private_subnets']['value']
    public_subnets = vpc_outputs['modules'][0]['outputs']['public_subnets']['value']

    os.system("cp {0} {1} && cp {2} {3}".format(config_map_aws_auth_filename, cm_config_file, kubeconfig_filename, kube_config_file))

    # aws-vault exec dataops-stage -- aws eks --region eu-west-1 update-kubeconfig --name og8-staging-eks-dataops \
    # --role-arn arn:aws:iam::561276803310:role/developers --alias eks-stage
    os.system("aws eks --region {0} update-kubeconfig --name {1} --alias eks-{2}".format("eu-west-1", cluster_id, environment))

    os.system("kubectl apply -f {0} --kubeconfig {1}".format(cm_config_file, kube_config_file))

    if args['eksTags']:
      create_eks_tags(cluster_id, vpc_id, private_subnets, public_subnets)
