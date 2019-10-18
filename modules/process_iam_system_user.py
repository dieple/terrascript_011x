import json
import boto3

import settings

from utils import *


# setup some dynamic required fields
def process_iam_system_user(inargs, input_kwargs, label, aws_account_data):

  region = settings.region

  # reset for each new run - import deepcopy is required here as
  # it's global variable between subsequent runs
  data_policy = copy.deepcopy(settings.DATA_POLICY)

  account_id = aws_account_data['account_ids'][inargs['account']]

  stmt_length = len(input_kwargs["actions_allow"])

  # setting up the data_policy json:
  for ind in range(stmt_length):
    data_policy['Statement'][ind]['Action'] = input_kwargs["actions_allow"][ind]
    # replaces AWS_REGION and ACCOUNT_ID in the resources_allow
    input_kwargs["resources_allow"][ind] = [r.replace('AWS_REGION', region).replace('ACCOUNT_ID', account_id) for r in input_kwargs["resources_allow"][ind]]
    data_policy['Statement'][ind]['Resource'] = input_kwargs["resources_allow"][ind]

  # now delete any remaining place holder statements
  for ind in range(9, stmt_length-1, -1):
    del data_policy['Statement'][ind]

  # if user not supplied then use the generated label
  if is_empty(input_kwargs["user_id"]):
    input_kwargs["user_id"] = label.id

  input_kwargs["policy"] = json.dumps(data_policy)

  # delete the processed input fields:
  del input_kwargs["actions_allow"]
  del input_kwargs["resources_allow"]
  del input_kwargs["actions_deny"]

  return input_kwargs
