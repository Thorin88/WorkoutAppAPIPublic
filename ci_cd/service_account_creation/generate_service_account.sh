# !/bin/bash

# Dev:
# ./generate_service_account.sh --service-account-name sa-workout-app-api-dev --environment-type dev

# Main:
# ./generate_service_account.sh --service-account-name sa-workout-app-api --environment-type main

# Functions

check_service_account_exists() {
    local service_account_email=$1
    local result=$(gcloud iam service-accounts list --format="value(email)" --filter="email:$service_account_email")

    if [[ -n "$result" ]]; then
        return 0  # Service account exists
    else
        return 1  # Service account does not exist
    fi
}

# Function to delete a service account
delete_service_account() {
    local service_account_email=$1
    # Can use --quiet to require no user input
    gcloud iam service-accounts delete $service_account_email
    echo "Service account '$service_account_email' deleted successfully."
}

# End functions

set -e

PROJECT="practice-project-thorin"

while [[ $# -gt 0 ]]; do
  key="$1"

  # Parsing parameters in chunks of two, the option name and its value, then shifting the input
  # For parameters just requiring presence, only need to shift once, for example.
  case $key in
    --service-account-name)
      SERVICE_ACCOUNT_NAME="$2"
      shift
      shift
      ;;
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
if [ -z "$SERVICE_ACCOUNT_NAME" ] || [ -z "$ENVIRONMENT_TYPE" ]; then
  echo "Missing 1 or more required arguements"
  # Could print a usage message
  exit 1
fi

# Commands often want this as the identifier of the service account
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_NAME@$PROJECT.iam.gserviceaccount.com

# Most of these commands require very high rights to run

if check_service_account_exists "$SERVICE_ACCOUNT_EMAIL"; then
    delete_service_account "$SERVICE_ACCOUNT_EMAIL"
else
    echo "Service account '$SERVICE_ACCOUNT_EMAIL' does not exist."
fi

gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
  --description="Hosts the backend API for the Workout App" \
  --display-name="$SERVICE_ACCOUNT_NAME" \
  --project="$PROJECT"

# Other roles: "roles/aiplatform.user" "roles/ml.developer"
ROLES=("roles/cloudsql.client" "roles/cloudsql.editor")

for role in "${ROLES[@]}"; do
  echo "Attempting to grant role: $role"
  gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:$SERVICE_ACCOUNT_EMAIL --role=$role --condition=None
done

# Give access to require secrets; secret names can be found from GCP
if [ $ENVIRONMENT_TYPE = main ]; then
  echo "Using main secrets"
  SECRETS=("practice-databases-workout-app-api-user-credentials" "workout-app-api-jwt-key")
elif [ $ENVIRONMENT_TYPE = dev ]; then
  echo "Using dev secrets"
  SECRETS=("practice-databases-workout-app-api-user-dev-credentials" "workout-app-api-jwt-key")
fi

for secret in "${SECRETS[@]}"; do
  echo "Attempting to grant access to secret: $secret"
  gcloud secrets add-iam-policy-binding $secret --member=serviceAccount:$SERVICE_ACCOUNT_EMAIL --role="roles/secretmanager.secretAccessor"
done

# Bucket permissions, granted in a slightly different way
BUCKET_PERMS=("roles/storage.legacyObjectReader")
BUCKETS=("test-bucket-ppt")

for perm in "${BUCKET_PERMS[@]}"; do
  for bucket in "${BUCKETS[@]}"; do
    echo "Attempting to grant bucket permision: $perm, to bucket $bucket"
    gsutil iam ch "serviceAccount:$SERVICE_ACCOUNT_EMAIL:$perm" "gs://$bucket"
  done
done