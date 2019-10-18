# terrascript_011x

Steps to generate terraform codes (version <= 0.11.x) using python-terrascript to build infrastructure on AWS.

# Introduction

### Contents

1. [Background](#Background)
1. [Pre-requisites](#Prerequisites)
1. [Use K9s To Explore Kubernetes](#Use-K9s-To-Explore-Kubernetes)


## Scope

This document describes how to use this tool to build AWS resources, such as 
* VPC 
* IAMs
* Security Groups
* Lambda functions
* Codebuild/Pipeline
* EKS
* and so on.  

This tool can be built on any accounts/environments in DRY code concept.

## Background

#### DataOps AWS Accounts

* __dev__ - used for infrastructure testing
* __staging__ - used to host dev and test environments
* __prod__ - used to host the production environment

#### Reference Repos

1. https://github.com/dieple/builder_tools.git <<< builder tools
1. https://github.com/dieple/terraform-modules-011x.git <<< terraform repo


## Prerequisites

#### General 

1. mkdir -p $HOME/{repos,.aws,.kube, .ssh, .terraform.d/plugin-cache} on your host machine
1. cd $HOME/repos
1. git clone git@github.com:dieple/builder_tools.git
1. git clone git@github.com:dieple/terrascript_011x.git
1. AWS Vault profiles setup 
1. Ability to run the [builder_tools](https://github.com/dieple/builder_tools.git) Docker image

#### AWS Vault Profiles 

Ensure the following `aws-vault` profiles have been added to your machine before trying
to use the `builder_tools` Docker image. Run the following commands in your terminal 
and follow prompts to supply valid access keys for your organisation IAM user.

* ```aws-vault add dataops-dev``` <<< required for infra testing
* ```aws-vault add dataops-staging``` <<< required to admin DataOps dev & test environments
* ```aws-vault add dataops-prod-admin``` <<< required if you want to admin production infra

#### Builder Tools

To interact with DataOps AWS accounts and EKS clusters, it is recommended to use the 
`builder_tools` Docker image so we all use a consistent toolchain.

---

### Start the Builder Tools Docker Image

Note - the `builder_tools` container mounts a local directory 
containing your source code to `/repos`, which we use further below! 

Windows users, see the [builder-tools](https://github.com/dieple/builder_tools#option-1---create-your-own-launch-script) 
repo documentation to understand how to mount your host machine path into (1) WSL and then into (2) 
your `builder_tools` Docker container.
 
```bash
$ cd $HOME/repos/builder_tools  # <<< cd to your clone of the builder_tools repo...
$ users/<your user>-run_builder.sh <aws-vault-profile-name>  # <<< use the aws-vault profile of choice here e.g. 'dataops-staging' or another one found in your `~/.aws/config` file
$ # enter prompts for access keys, secret & MFA token
```

This puts you inside the Docker image with a toolchain and AWS access tokens to continue below...


### Access EKS (Post EKS module installation)

Setup config file `~/.kube/config` so you can use `kubectl` command-line tool as follows:

```bash
$ aws eks list-clusters  
# JSON is output...
# Note the EKS cluster name for use in the next command.
# For example, from the sample below, we grab string 'og8-staging-eks-dataops'
$ aws eks update-kubeconfig --name <cluster-name-from-above> --alias <dev|staging|prod>  
# Choose a simple alias name above!
```

Sample output from command `aws eks list-clusters`:
```json
{
    "clusters": [
        "og8-staging-eks-dataops"
    ]
}
```

Next, to test that the kube context imported successfully, run the following:

```bash
$ kubectl config get-contexts  
```

This should list metadata for all configured Kubernetes clusters,
including the one that you just imported with the alias name that you used.
There is a `*` against the CURRENT context.  

Next, set your kube config file to use the EKS cluster that you want to interact with. 
This is not required if you just imported the config above as it will be set as the current default.

You can also use this command if you just want to switch between administering 
EKS in different environments/accounts.

```bash
$ kubectl config use-context <alias from above>  # <<< use a context name shown in the output of get-contexts above
``` 

Test that you can talk to the EKS cluster by listing available namespaces as follows:

```bash
$ kubectl get ns  # <<< ns is short for namespaces
```

This should list entries like `kube-system` and `default` along with any others created by developers etc.


---

### Use K9s To Explore Kubernetes

`k9s` is an open-source tool that wraps up the `kubectl` CLI tool and Kubernetes API into a visual terminal app.
By default it uses your current `~/.kube/config` context. 

```bash
$ k9s  # <<< launch k9s using your current context; or...
$ k9s --context <an alias in your ~/.kube/config file>  # <<< use an alternative context without having to switch 
```

The tool is quite simple and you can view the available keyboard shortcuts at the top of the screen.

__Examples__

* Use cursor keys to __navigate__
* Hit enter to __select__
* Hit escape to __go back__ 
* Type `:ns`  <<< __view namespaces__
* Type `:po`  <<< __view pods__ in the current namespace
* Cursor up/down to choose a pod, then hit `s` to __ssh to it__
* Cursor up/down to choose a pod, then hit `y` to view its __YAML definition__
* Cursor up/down to choose a pod, then hit `l` to view its __logs__
 
