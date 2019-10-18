# terrascript_011x

Steps to generate terraform codes (version <= 0.11.x) using python-terrascript to build infrastructure on AWS.

```
$ mkdir -p $HOME/repos
$ cd $HOME/repos
$ git clone git@github.com:dieple/builder_tools.git
$ git clone git@github.com:dieple/terrascript_011x.git
$ cd $HOME/repos/builder_tools
$ # Modify run_builder.sh to meet your env
$ ./run_builder.sh
$ # Once inside docker image...
$ cd /repos/terrascript_011x (inside docker image)
$ # Modify build.py and run_build.sh to meet your need
$ #run_build.sh to build resources on AWS. Note that account must match that defined in vars/aws_accounts.yaml

```
