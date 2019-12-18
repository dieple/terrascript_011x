import os
import copy

from terrascript import *
from s3_data import *
from utils import *
from tags import *
from process_bastion import *
from process_codepipeline import *
from process_efs import *
from process_eks import *
from setup_input_kwargs import *
from process_iam_roles import *
from process_iam_system_user import *

from pathlib import Path
from functools import reduce

import settings


def generate_module(inargs, module_name, module_built_by_terrascript):

    ts = Terrascript()
    # moduleName = os.path.basename(__file__).split('.')[0]
    args = setup_filepath(inargs, module_name)

    aws_account_data, p_data, src_data, backend_data, mod_data = get_yaml_input(args)

    environment = settings.environment
    region = settings.region


    if module_name == "s3_tfstate_backend":
        ts, label, label_kwargs = generate_terraform_backend_provider_and_label(args, ts, add_backend=False)
    else:
        ts, label, label_kwargs = generate_terraform_backend_provider_and_label(args, ts)

    # setup key words arguments input parameters...
    input_kwargs = setup_input_kwargs(module_name, args, ts, label, label_kwargs, backend_data, src_data, mod_data, aws_account_data, module_built_by_terrascript)

    # generate terraform codes to invoke opensource/in-house terraform modules
    module_name_ = module(name_=module_name, **input_kwargs)
    ts.add(module_name_)

    if not args['tfdestroy']:
        # generate module outputs
        for field in mod_data[environment]['module']['outputs']:
            ts.add(output(field, value="{0}module.{1}.{2}{3}".format("${", module_name, field, "}")))


    # empty cicd cache bucket first for successful tfrun deletion
    # if module_name == 'codepipeline_umsl':
    #     if args['tfdestroy']:
    #         # empty cicd cache bucket first for successful tfrun
    #         bucket, key = get_remote_state_bucket_and_key(backend_data, module_name, module_built_by_terrascript)
    #         bucket_data = parse_s3_remote_data(bucket, key, '/tmp/cicd_pipeline_bucket_data_terraform.tfstate')
    #         artifact_bucket_name = bucket_data['modules'][1]['resources']['aws_s3_bucket.default']['primary']['id']
    #         # print("artifact_bucket_name = {0}".format(artifact_bucket_name))
    #         empty_s3_bucket(artifact_bucket_name)

    # run terraform init, terraform plan & terrform apply on the generated codes
    tfrun (ts, args)

    # EKS ~/.kube/config post install config
    if module_name == 'eks':
        eks_post_install_config(args, backend_data, src_data, module_built_by_terrascript)
