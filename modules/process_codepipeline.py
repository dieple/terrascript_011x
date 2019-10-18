import json
import boto3

import settings

from utils import *


# setup some dynamic required fields
def process_codepipeline(ts, input_kwargs, label, aws_account_data, src_data, backend_data, module_built_by_terrascript):

  region = settings.region
  environment = settings.environment
  vpc_built_by_terrascript = backend_data[environment]['vpc_built_by_terrascript']

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

  security_groups = [ data_core_security_group.efs_access_sg,
                      data_core_security_group.eks_worker_sg,
                      data_core_security_group.eks_cluster_sg,
                      data_core_security_group.rds_access_sg,
                      data_core_security_group.codebuild_access_sg ]

  # EKS cluster name and eks_kubectl_role_arn data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "eks", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_eks']
  remote_data_kwargs["region"] = region
  data_eks = module(name_="data_eks", **remote_data_kwargs)
  ts.add(data_eks)

  # IAM role codebuild data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_codebuild", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_codebuild']
  remote_data_kwargs["region"] = region
  data_iam_role_codebuild = module(name_="data_iam_role_codebuild", **remote_data_kwargs)
  ts.add(data_iam_role_codebuild)

  # IAM role codepipeline data:
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "iam_role_codepipeline", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_iam_role_codepipeline']
  remote_data_kwargs["region"] = region
  data_iam_role_codepipeline = module(name_="data_iam_role_codepipeline", **remote_data_kwargs)
  ts.add(data_iam_role_codepipeline)

  # artifact_store_bucket_name (codepipeline_s3_bucket.yaml)
  remote_data_kwargs = {}
  remote_data_kwargs["bucket"], remote_data_kwargs["key"] = get_remote_state_bucket_and_key(backend_data, "codepipeline_s3_bucket", module_built_by_terrascript)
  remote_data_kwargs["source"] = src_data[environment]['source']['data_codepipeline_s3_bucket']
  remote_data_kwargs["region"] = region
  data_codepipeline_s3_bucket = module(name_="data_codepipeline_s3_bucket", **remote_data_kwargs)
  ts.add(data_codepipeline_s3_bucket)

  # input_kwargs["tags"] = label.tags
  input_kwargs["vpc_id"] = data_vpc.vpc_id
  input_kwargs["subnets"] = data_vpc.private_subnets
  input_kwargs["security_group_ids"] = security_groups
  input_kwargs["eks_cluster_name"] = data_eks.cluster_id if is_empty(input_kwargs["eks_cluster_name"]) else input_kwargs["eks_cluster_name"]
  input_kwargs["eks_kubectl_role_arn"] = data_eks.worker_iam_role_arn if is_empty(input_kwargs["eks_kubectl_role_arn"]) else input_kwargs["eks_kubectl_role_arn"]
  input_kwargs["codebuild_service_policy_arn"] = data_iam_role_codebuild.policy if is_empty(input_kwargs["codebuild_service_policy_arn"]) else input_kwargs["codebuild_service_policy_arn"]
  input_kwargs["codebuild_service_role_arn"] = data_iam_role_codebuild.arn if is_empty(input_kwargs["codebuild_service_role_arn"]) else input_kwargs["codebuild_service_role_arn"]
  input_kwargs["codepipeline_role_arn"] = data_iam_role_codepipeline.arn if is_empty(input_kwargs["codepipeline_role_arn"]) else input_kwargs["codepipeline_role_arn"]
  input_kwargs["artifact_store_bucket_name"] = data_codepipeline_s3_bucket.bucket_id if is_empty(input_kwargs["artifact_store_bucket_name"]) else input_kwargs["artifact_store_bucket_name"]

  return input_kwargs

