import json
import boto3

import settings

from utils import *


# setup some dynamic required fields
def process_efs(ts, args, label, aws_account_data, src_data, backend_data, input_kwargs, module_built_by_terrascript):

  environment = settings.environment
  region = settings.region
  vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']
  region = args['region']

  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
  data_vpc = module(name_="data_vpc", **remote_data_kwargs)
  ts.add(data_vpc)

  # core security group remote data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "core_security_group", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_core_security_group']
  remote_data_kwargs["region"] = region
  data_core_security_group = module(name_="data_core_security_group", **remote_data_kwargs)
  ts.add(data_core_security_group)

  if vpc_built_by_terrascript:
    remote_data_kwargs = {}
    remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "route53_zone_and_records", module_built_by_terrascript)
    remote_data_kwargs["source"] = src_data[environment]['source']['data_route53_zone_and_records']
    remote_data_kwargs["region"] = region
    data_route53_zone_and_records = module(name_="data_route53_zone_and_records", **remote_data_kwargs)
    ts.add(data_route53_zone_and_records)

    zone_id = data_route53_zone_and_records.zone_id
    input_kwargs["availability_zones"] = data_vpc.azs
  else:
    zone_id = data_vpc.aws_zone_id
    input_kwargs["availability_zones"] = data_vpc.availability_zones


  security_groups = [ data_core_security_group.efs_access_sg,
                      data_core_security_group.eks_worker_sg,
                      data_core_security_group.eks_cluster_sg,
                      data_core_security_group.rds_access_sg,
                      data_core_security_group.codebuild_access_sg ]


  input_kwargs["tags"] = label.tags
  input_kwargs["dns_name"] = label.id
  input_kwargs["aws_region"] = region
  input_kwargs["vpc_id"] = data_vpc.vpc_id
  input_kwargs["zone_id"] = zone_id
  input_kwargs["security_groups"] = security_groups
  input_kwargs["subnets"] = data_vpc.private_subnets


  # print ("input_kwargs: {0}\n".format(input_kwargs))
  return input_kwargs

