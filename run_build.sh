#!/usr/bin/env bash
#python3 ./build.py --account dataops_dev \
#                   --cicd false \
#                   --environment dataops_dev \
#                   --profile dataops-dev \
#                   --tfapply true \
#                   --eksTags true \
#                   -region "eu-west-1"

# to destroy modules uncomment below
#python3 ./build.py -a dataops_dev -c false -e dataops_dev -p dataops-dev -t true -k true -r "eu-west-1" -d true


# to build modules
python3 ./build.py \
  -a platform_testing \
  -c false \
  -e platform_testing \
  -p platform-testing \
  -t true \
  -k true \
  -w true \
  -r "eu-west-1"
