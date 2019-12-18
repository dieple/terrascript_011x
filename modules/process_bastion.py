import json
import boto3

import settings

from utils import *


# setup some dynamic required fields
def process_bastion(ts, input_kwargs, label, aws_account_data, src_data, backend_data, module_built_by_terrascript):

  environment = settings.environment
  region = settings.region
  vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']

  # vpc remote data
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
  data_vpc = module(name_="data_vpc", **remote_data_kwargs)
  ts.add(data_vpc)

  if vpc_built_by_terrascript:
    # route53 zone and records data:
    remote_data_kwargs = {}
    remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "route53_zone_and_records", module_built_by_terrascript)
    remote_data_kwargs["source"] = src_data[environment]['source']['data_route53_zone_and_records']
    remote_data_kwargs["region"] = region
    data_route53_zone_and_records = module(name_="data_route53_zone_and_records", **remote_data_kwargs)
    ts.add(data_route53_zone_and_records)

    # ssh key pair remote data:
    remote_data_kwargs = {}
    remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "ssh_key_pair", module_built_by_terrascript)
    remote_data_kwargs["source"] = src_data[environment]['source']['data_ssh_key_pair']
    remote_data_kwargs["region"] = region
    data_ssh_key_pair = module(name_="data_ssh_key_pair", **remote_data_kwargs)
    ts.add(data_ssh_key_pair)

    zone_id = data_route53_zone_and_records.zone_id
    key_name = data_ssh_key_pair.key_name
  else:
    zone_id = data_vpc.zone_id
    key_name = data_vpc.key_name

  # input_kwargs["tags"] = label.tags
  input_kwargs["key_name"] = key_name
  input_kwargs["zone_id"] = zone_id
  input_kwargs["vpc_id"] = data_vpc.vpc_id
  input_kwargs["public_subnets"] = data_vpc.public_subnets
  input_kwargs["environment"] = environment

  # if bastion_name is not enter then use the generate label.id instead
  if is_empty(input_kwargs["bastion_name"]):
    input_kwargs["bastion_name"] = label.id

  # print ("input_kwargs: {0}".format(input_kwargs))
  return input_kwargs

