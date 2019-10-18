import os
import argparse
import sys
import inspect
import logging

from terrascript import *
from python_terraform import *

# realpath() will make your script run, even if you symlink it :)
build_dir = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if build_dir not in sys.path:
    sys.path.insert(0, build_dir)

# include utils or lib modules from a subfolder
for include_dir in ["utils", "vars", "modules", "generated"]:
    build_subdir = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], include_dir)))
    if build_subdir not in sys.path:
        sys.path.insert(0, build_subdir)


from generate_module import *
import settings


LOGLEVEL = os.getenv('LOG_LEVEL', 'INFO').strip()
logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)


def process_arguments():
    parser = argparse.ArgumentParser()
    optional = parser._action_groups.pop()

    required = parser.add_argument_group('Required arguments')
    required.add_argument('-a', '--account', help='Account name to target the build', required=True)
    required.add_argument('-e', '--environment', help='Environment to build the resources', required=True)
    required.add_argument('-c', '--cicd', help='Running in CI/CD mode?', required=True, default=False)
    required.add_argument('-p', '--profile', help='Profile to use with aws-vault', required=True)

    optional.add_argument('-l', '--trace', help='Run terraform with TF_LOG=TRACE?', required=False, default=False)
    optional.add_argument('-v', '--varfiles', help='List of Vars file names', default=['./vars/aws_accounts.yaml', './vars/providers.yaml', './vars/source.yaml', './vars/backend.yaml'])
    optional.add_argument('-t', '--tfapply', help='Run terraform apply?', required=False, default=False)
    optional.add_argument('-d', '--tfdestroy', help='Run terraform destroy?', required=False, default=False)
    optional.add_argument('-r', '--region', help='Build region', required=False, default="eu-west-1")
    # optional.add_argument('-g', '--generate', help='Terraform generated path', required=False, default='/repos/ts-generate')
    optional.add_argument('-k', '--eksTags', default=False, help='Create VPC EKS tags')
    #parser._action_groups.append(optional)
    return parser.parse_args()


def get_modules_to_run(environment, build_file):

    src = YAML(typ='safe')

    # aws_accounts
    with open(build_file) as f:
        modules_to_run_json = src.load(f)

    modules_to_run_data = modules_to_run_json[environment]

    return modules_to_run_data


if __name__ == '__main__':

    inargs = process_arguments()

    # initialise some global variables
    settings.init(inargs)
    environment = settings.environment

    if inargs.tfdestroy:
        modules_to_run_data = get_modules_to_run(environment, './vars/destroy.yaml')
        action = "******************** Destroying"
    else:
        action = "******************** Building"
        modules_to_run_data = get_modules_to_run(environment, './vars/build.yaml')


    for module_, build_flag_ in modules_to_run_data.items():
      if build_flag_ == True: # only build when we see the word true in the yaml file (any other words is false)
        print("{0} module: ******************** {1}...".format(action, module_))

        if environment == 'dataops_dev' and module_ == 'vpc':
            module_built_by_terrascript = False
        else:
            module_built_by_terrascript = True

        generate_module(inargs, module_, module_built_by_terrascript)

    # display in HCL
    #json2hcl < /tmp/s3/main.tf.json


