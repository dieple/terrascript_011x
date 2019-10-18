import os
import copy

import json
import boto3

from utils import *
from s3_data import *
from tags import *
from process_bastion import *
from process_codepipeline import *
from process_efs import *
from process_eks import *
from process_iam_roles import *
from process_iam_system_user import *

import settings

# setup some dynamic required fields
def setup_input_kwargs(module_name, args, ts, label, label_kwargs, backend_data, src_data, mod_data, aws_account_data, module_built_by_terrascript):

    region = settings.region
    environment = settings.environment
    iam_role_list = settings.iam_role_list
    lambda_function_list = settings.lambda_function_list
    vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']

    input_kwargs = {}
    remote_data_kwargs = {}

    # module param inputs dynamically generated from input yaml file
    for k, v in mod_data[environment]['module']['inputs'].items():
        input_kwargs[k] = v

    # check if 'name' (key exists) and not populated in the yaml
    # then use the label.id field instead
    if 'name' in input_kwargs:
        if is_empty(input_kwargs["name"]):
            input_kwargs["name"] = label.id

    if 'tags' in input_kwargs:
        if is_empty(input_kwargs["tags"]):
            input_kwargs["tags"] = label.tags

    if 'region' in input_kwargs:
        if is_empty(input_kwargs["region"]):
            input_kwargs["region"] = region

    # some terraform modules has "tag labels" as part of the input parameters!
    if 'include_tag_label_' in input_kwargs:
        if input_kwargs["include_tag_label_"]:
            input_kwargs["name"] = label_kwargs["name"]
            input_kwargs["namespace"] = label_kwargs["namespace"]
            input_kwargs["stage"] = label_kwargs["stage"]
            input_kwargs["attributes"] = label_kwargs["attributes"]
            if 'project' in input_kwargs:
                input_kwargs["project"] = label_kwargs["project"]
            if 'cost_centre' in input_kwargs:
                input_kwargs["cost_centre"] = label_kwargs["cost_centre"]

        del input_kwargs["include_tag_label_"]


    if module_name == "ssh_key_pair":
        # input_kwargs["tags"] = label.tags
        if is_empty(input_kwargs["key_name"]):
            input_kwargs["key_name"] = label.id

    elif module_name == "vpc_peering_to_transit":
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
        data_vpc = module(name_="data_vpc", **remote_data_kwargs)
        ts.add(data_vpc)
        input_kwargs["requestor_vpc_id"] = data_vpc.vpc_id
        input_kwargs["requestor_private_subnets"] = data_vpc.private_subnets
        input_kwargs["requestor_private_route_table_ids"] = data_vpc.private_route_table_ids

    elif module_name == "core_security_group":
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
        data_vpc = module(name_="data_vpc", **remote_data_kwargs)
        ts.add(data_vpc)
        input_kwargs["vpc_id"] = data_vpc.vpc_id
        input_kwargs["vpc_cidr_block"] = [data_vpc.vpc_cidr]

    elif module_name == "bastion":
        input_kwargs = process_bastion(ts, input_kwargs, label, aws_account_data, src_data, backend_data, environment, module_built_by_terrascript)

    elif module_name == "rds_cluster_aurora":
        # vpc remote data
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", vpc_built_by_terrascript)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
        data_vpc = module(name_="data_vpc", **remote_data_kwargs)
        ts.add(data_vpc)

        # iam role remote data:
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "eks_iam_roles", module_built_by_terrascript)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_roles']
        data_iam_roles = module(name_="data_iam_roles", **remote_data_kwargs)
        ts.add(data_iam_roles)

        # core security group remote data:
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "core_security_group", module_built_by_terrascript)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_core_security_group']
        data_core_security_group = module(name_="data_core_security_group", **remote_data_kwargs)
        ts.add(data_core_security_group)

        input_kwargs["vpc_id"] = data_vpc.vpc_id
        input_kwargs["subnets"] = data_vpc.private_subnets
        input_kwargs["vpc_security_group_ids"] = data_core_security_group.rds_access_sg
        input_kwargs["monitoring_role_arn"] = data_iam_roles.rds_monitoring_arn

    elif module_name == 'ec2_instance':
        device_name = get_value(input_kwargs["ebs_block_device"], "device_name")
        input_kwargs["device_name"] = device_name

    elif module_name == 'efs':
        input_kwargs = process_efs(ts, args, label, aws_account_data, src_data, backend_data, input_kwargs, module_built_by_terrascript)

    elif module_name == 'eks':
        input_kwargs = process_eks(ts, input_kwargs, label, aws_account_data, src_data, backend_data, module_built_by_terrascript)

    elif module_name == 'codepipeline':
        input_kwargs = process_codepipeline(ts, input_kwargs, label, aws_account_data, src_data, backend_data, module_built_by_terrascript)

    elif module_name == 'iam_system_user':
        input_kwargs = process_iam_system_user(args, input_kwargs, label, aws_account_data)

    elif module_name == 'iam_role_eks_worker':
        if is_empty(input_kwargs["role_name"]):
            input_kwargs["role_name"] = label.id

    elif module_name == 'iam_role_efs_provisioner':
        if is_empty(input_kwargs["role_name"]):
            input_kwargs["role_name"] = label.id

        if is_empty(input_kwargs["eks_worker_role_name"]):
            # eks worker iam role remote data:
            remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_eks_worker", module_built_by_terrascript)
            remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_eks_worker']
            data_iam_role_eks_worker = module(name_="data_iam_role_eks_worker", **remote_data_kwargs)
            ts.add(data_iam_role_eks_worker)
            input_kwargs["eks_worker_role_name"] = data_iam_role_eks_worker.name


    elif module_name in iam_role_list:
        input_kwargs = process_iam_roles(args, input_kwargs, label, aws_account_data)

    elif module_name in lambda_function_list:
        if not args['tfdestroy'] and args['tfapply']:
            # if the lamba role arn is not passed in use the default lambda common role instead
            if is_empty(input_kwargs["role_arn"]):
                remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_lambda_common", module_built_by_terrascript)
                remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_lambda_common']
                data_iam_role_lambda_common = module(name_="data_iam_role_lambda_common", **remote_data_kwargs)
                ts.add(data_iam_role_lambda_common)
                input_kwargs["role_arn"] = data_iam_role_lambda_common.role_arn

    elif module_name == 'codepipeline_umsl':
        remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "vpc", environment)
        remote_data_kwargs["source"] = src_data[environment]['source']['data_vpc']
        data_vpc = module(name_="data_vpc", **remote_data_kwargs)
        ts.add(data_vpc)

    input_kwargs["source"] = src_data[environment]['source'][module_name]
    # print("input_kwargs: --- {0} ---\n".format(input_kwargs))
    return input_kwargs

