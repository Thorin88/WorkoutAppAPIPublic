#!/bin/bash

PROJECT=practice-project-thorin
SERVICE_ACCOUNT_NAME=sa-workout-app-api-dev

gcloud run deploy workout-app-api-dev \
  --source=. \
  --env-vars-file=./config/gcp-dev.yaml \
  --region=europe-west2 \
  --project=$PROJECT \
  --cpu=1 \
  --concurrency=3 \
  --service-account=$SERVICE_ACCOUNT_NAME@$PROJECT.iam.gserviceaccount.com \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=1 \
  --allow-unauthenticated \
  --set-cloudsql-instances=$PROJECT:europe-west2:practice-databases

  # --no-allow-unauthenticated \
  # --add-cloudsql-instances=$PROJECT:europe-west2:practice-databases

# Note the artifact registry will be filled with images, which cost money to store.
# Deploying from source requires an Artifact Registry Docker repository to store built containers. A repository named [cloud-run-source-deploy] in region [europe-west2] will be created.
# This command is equivalent to running `gcloud builds submit --tag [IMAGE] .` and `gcloud run deploy workout-app-api --image [IMAGE]`