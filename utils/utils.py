import yaml
import os
import sys
import copy
import settings

from simplecrypt import encrypt, decrypt
from base64 import b64encode, b64decode
from getpass import getpass

from terrascript import *
from ruamel.yaml import YAML
from s3_data import *



def get_value(listOfDicts, key):
  for subVal in listOfDicts:
    if key in subVal:
      return subVal[key]

def is_empty(chk_data):
  if chk_data:
    return False
  else:
    return True

def get_aws_account_id(aws_account_ids, args):
  # cipher = str.encode(aws_account_ids['account_ids'][args['account']])
  # plaintext_account_id = decrypt(args['profile'], cipher)
  # return plaintext_account_id
  return aws_account_ids['account_ids'][args['account']]


def get_vars(ymlfile, *args):

  with open(ymlfile, 'r') as f:
    invar = yaml.load(f)

    # get top section
    section = args[0]

    # check if Vars file has Environment
    #if not invar.has_key(section):
    if section not in invar:
      print("Environment or top section '{0}' key is missing".format(section))
      quit()

    # get values
    argList = list(args) # convert tuple to list
    argList.pop(0) # remove Environment from list

    # create lookup path
    parsepath = "invar['" + section + "']"

    for arg in argList:
      parsepath = parsepath + "['" + arg + "']"

    return eval(parsepath)

  f.close()



def get_yaml_input(inargs):

  src = YAML(typ='safe')

  # aws_accounts
  with open(inargs['varfiles'][0]) as fa:
    account_data = src.load(fa)

  # providers
  with open(inargs['varfiles'][1]) as fp:
    prov_data = src.load(fp)

  # sourcepath
  with open(inargs['varfiles'][2]) as fsrc:
    src_data = src.load(fsrc)

  # backend
  with open(inargs['varfiles'][3]) as bksrc:
    backend_data = src.load(bksrc)

  # modulepath
  with open(inargs['varfiles'][4]) as fmod:
    mod_data = src.load(fmod)

  return account_data, prov_data, src_data, backend_data, mod_data


def get_label(src_data, mod_data):

  environment = settings.environment

  # tags and label
  label_kwargs = {}
  label_kwargs["source"] = src_data[environment]['source']['label']
  for k,v in mod_data[environment]['module']['tag_label'].items():
    label_kwargs[k] = v

  if is_empty(label_kwargs["attributes"]):
    label_kwargs["attributes"] = [label_kwargs["project"]]

  label = module("label", **label_kwargs)

  return label, label_kwargs


def setup_filepath(inargs, moduleName):

  # setup arguments
  args = copy.deepcopy(vars(inargs))
  moduleVarFile = './vars/' + moduleName + '.yaml'

  args['varfiles'].append(moduleVarFile)
  args['module'] = moduleName
  args['generated'] =  './generated/' + moduleName + '/' + args['environment']

  return args



def generate_terraform_backend_provider_and_label(inargs, ts, add_backend=True):

  backend_data_dict = {}
  terraform_data_dict = {}
  providers_data_dict = {}

  environment = settings.environment
  module_name = inargs['module']

  aws_account_data, p_data, src_data, backend_data, mod_data = get_yaml_input(inargs)

  account_id = aws_account_data['account_ids'][inargs['account']]

  # backend
  backend_data_dict["bucket"] = backend_data[environment]['terraform']['backend']['bucket']
  backend_data_dict["encrypt"] = backend_data[environment]['terraform']['backend']['encrypt']
  backend_data_dict["dynamodb_table"] = backend_data[environment]['terraform']['backend']['dynamodb_table']
  backend_data_dict["region"] = p_data[environment]['provider']['aws']['region']

  # always in this format: infrastructure/<module>/<environment>/terraform.tfstate
  backend_data_dict["key"] = "infrastructure/{0}/{1}/terraform.tfstate".format(module_name, environment)

  if inargs['cicd'].lower() == 'true':
    backend_data_dict["role_arn"] = "arn:aws:iam::{0}:role/cd".format(account_id)

  # providers
  terraform_data_dict["required_version"] = backend_data[environment]['terraform']['required_version']

  providers_data_dict["allowed_account_ids"] = [account_id]
  providers_data_dict["region"] = p_data[environment]['provider']['aws']['region']
  providers_data_dict["version"] = p_data[environment]['provider']['aws']['version']

  s3_backend = backend("s3", **backend_data_dict)

  if add_backend:
    ts.add(terraform(required_version=terraform_data_dict['required_version'], backend=s3_backend))
  else:
    ts.add(terraform(required_version=terraform_data_dict['required_version']))

  ts.add(provider('aws', **providers_data_dict))
  # TODO: add the rest of providers here.

  label, label_kwargs = get_label(src_data, mod_data)
  ts.add(label)

  return ts, label, label_kwargs



def get_remote_data_bucket(backend_data, module_built_by_terrascript=True):

  environment = settings.environment

  if module_built_by_terrascript:
    remote_bucket = backend_data[environment]['terraform']['backend']['bucket']
  else:
    remote_bucket = backend_data[environment]['terraform']['remote_data']['bucket']

  return remote_bucket


def get_remote_state_bucket_and_key(backend_data, remote_module, module_built_by_terrascript=True):

  environment = settings.environment

  remote_module_bucket = get_remote_data_bucket(backend_data, module_built_by_terrascript)

  if module_built_by_terrascript:
    remote_module_key = "infrastructure/{0}/{1}/terraform.tfstate".format(remote_module, environment)
  else:
    remote_module_key = 'infrastructure/terraform.tfstate'

  return remote_module_bucket, remote_module_key



def tfrun(terrascript, args):

  gen_path = args['generated']
  os.system("mkdir -p {0}".format(gen_path))
  os.system("rm -rf {0}/.terraform".format(gen_path))
  file = open("{0}/main.tf.json".format(gen_path), "w")
  file.write(terrascript.dump())
  file.close()

  tf_cmd = "terraform init && terraform plan -out=tfplan.txt"

  if args['tfdestroy']:
    tf_cmd = tf_cmd + " -destroy"

  # Richard commented use of aws-vault to try using scripts/assume-role.sh instead.
  # TODO: remove this commented block if we don't hit nested session errors.
  if args['trace']:
    if args['awsvault'] == True:
      # Assume roles using aws-vault
      tfplan = "cd {0} && unset AWS_VAULT && export TF_LOG=TRACE && aws-vault exec {1} -- {2}".format(gen_path, args['profile'], tf_cmd)
      tfapply = "cd {0} && unset AWS_VAULT && export TF_LOG=TRACE && aws-vault exec {1}  -- terraform apply tfplan.txt".format(gen_path, args['profile'])
    else:
      tfplan = "cd {0} && export TF_LOG=TRACE && {1}".format(gen_path, tf_cmd)
      tfapply = "cd {0} && export TF_LOG=TRACE && terraform apply tfplan.txt".format(gen_path)
  else:
    if args['awsvault'] == True:
      tfplan = "cd {0} && unset AWS_VAULT && aws-vault exec {1} -- {2}".format(gen_path, args['profile'], tf_cmd)
      tfapply = "cd {0} && unset AWS_VAULT && aws-vault exec {1}  -- terraform apply tfplan.txt".format(gen_path, args['profile'])
    else:
      tfplan = "cd {0} && {1}".format(gen_path, tf_cmd)
      tfapply = "cd {0} && terraform apply tfplan.txt".format(gen_path)

  # if args['trace']:
  #     tfplan = "cd {0} && unset AWS_VAULT && export TF_LOG=TRACE && . assume-role.sh {1} && {2}".format(gen_path, args['profile'], tf_cmd)
  #     tfapply = "cd {0} && unset AWS_VAULT && export TF_LOG=TRACE && . assume-role.sh {1} && terraform apply tfplan.txt".format(gen_path, args['profile'])
  # else:
  #     tfplan = "cd {0} && unset AWS_VAULT && . assume-role.sh {1} && {2}".format(gen_path, args['profile'], tf_cmd)
  #     tfapply = "cd {0} && unset AWS_VAULT && . assume-role.sh {1} && terraform apply tfplan.txt".format(gen_path, args['profile'])

  os.system(tfplan)

  if args['tfapply']:
    os.system(tfapply)
