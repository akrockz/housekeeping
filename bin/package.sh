#!/bin/bash

set -e

echo "core-housekeeping package script running."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" # this script's directory
STAGING="${DIR}/../_staging"
echo "STAGING=${STAGING}"

# Setup, cleanup.
cd $DIR
mkdir -p $STAGING # files dir for lambdas
rm -rf $STAGING/*

# Copy deployspec and CFN templates into staging folder.
cp -pr $DIR/../*.yaml $STAGING/

# Package lambdas into files subfolder of staging .
# TODO write bash to iterate directories when we have more than 1 lambda.

cd $DIR/../lambdas/clean_log_groups
zip --symlinks -r9 $STAGING/clean_log_groups.zip *
cd $DIR/../lambdas/unrestricted_Access_sg_list
zip --symlinks -r9 $STAGING/trusted-advisor-sg-details.zip *
echo "core-housekeeping unrestricted_Access_sg_list package step complete, run.sh can be executed now."

cd $DIR/../lambdas/getting_volumes_details
zip --symlinks -r9 $STAGING/getting_volumes_details.zip *
echo "core-housekeeping package step complete, run.sh can be executed now."
