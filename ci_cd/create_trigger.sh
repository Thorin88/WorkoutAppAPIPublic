# !/bin/bash

# Dev:
# ./create_trigger.sh --environment-type dev

# Main:
# ./create_trigger.sh --environment-type main

# Functions

# End functions

set -e

while [[ $# -gt 0 ]]; do
  key="$1"

  # Parsing parameters in chunks of two, the option name and its value, then shifting the input
  # For parameters just requiring presence, only need to shift once, for example.
  case $key in
    # --trigger_name)
    #   TRIGGER_NAME="$2"
    #   shift
    #   shift
    #   ;;
    --environment-type)
      ENVIRONMENT_TYPE="$2"
      shift
      shift
      ;;
    *)
      echo "Did not recognise parameter: $1"
      # Could print a usage message
      exit 1
      ;;
  esac
done

# Check minimum arguements are provided
if [ -z "$ENVIRONMENT_TYPE" ]; then
  echo "Missing 1 or more required arguements"
  # Could print a usage message
  exit 1
fi

if [ $ENVIRONMENT_TYPE == "dev" -o $ENVIRONMENT_TYPE == "main" -o $ENVIRONMENT_TYPE == "staging" ]; then
    echo "Building trigger using environment type: $ENVIRONMENT_TYPE"
else
    echo "Unrecognised environment type: $ENVIRONMENT_TYPE"
    exit 1
fi

PROJECT=practice-project-thorin
SERVICE_ACCOUNT_NAME=sa-workout-app-api
GCP_DEPLOYMENT_NAME=workout-app-api
TRIGGER_NAME=workout-app-api-trigger

if [ $ENVIRONMENT_TYPE == "main" ]; then
    SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME
    GCP_DEPLOYMENT_NAME=$GCP_DEPLOYMENT_NAME
    TRIGGER_NAME=$TRIGGER_NAME
    BRANCH_PATTERN="^main$"
    ENV_VARS_FILE=./config/gcp.yaml
elif [ $ENVIRONMENT_TYPE == "dev" ]; then
    SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME-dev
    GCP_DEPLOYMENT_NAME=$GCP_DEPLOYMENT_NAME-dev
    TRIGGER_NAME=$TRIGGER_NAME-dev
    BRANCH_PATTERN="^dev$"
    ENV_VARS_FILE=./config/gcp-dev.yaml
elif [ $ENVIRONMENT_TYPE == "staging" ]; then
    SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME-staging
    GCP_DEPLOYMENT_NAME=$GCP_DEPLOYMENT_NAME-staging
    TRIGGER_NAME=$TRIGGER_NAME-staging
    BRANCH_PATTERN="^staging$"
    ENV_VARS_FILE=./config/gcp-staging.yaml
fi

# TODO -> Use this with IAM in the steps of the cloudbuild file
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_NAME@$PROJECT.iam.gserviceaccount.com

### IMPORTANT NOTE ###
# When in trial, it seems that the London region is not allowed as a trigger location.
TRIGGER_REGION=europe-west1

gcloud builds triggers create github \
    --name=$TRIGGER_NAME \
    --description="Builds and deploys the code from the matching branch whether a pull request is completed." \
    --region=$TRIGGER_REGION \
    --repo-name=WorkoutAppAPI \
    --repo-owner=Thorin88 \
    --pull-request-pattern=$BRANCH_PATTERN \
    --build-config=ci_cd/cloudbuild.yaml \
    --substitutions="_GCP_DEPLOYMENT_NAME"=$GCP_DEPLOYMENT_NAME,"_ENV_VARS_FILE"=$ENV_VARS_FILE,"_SERVICE_ACCOUNT_EMAIL"=$SERVICE_ACCOUNT_EMAIL

# Can also match pushes (branch_pattern) or tags. This code only checks merged PRs, checking the pattern against the base branch.
# --comment-control="COMMENTS_ENABLED" (default) means that a PR needs a specific comment on it before the build starts. Use "COMMENTS_DISABLED" if not desired. Can be useful
# to deal with comments on a PR, then building at the end, or as needed.