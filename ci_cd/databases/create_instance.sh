# !/bin/bash

gcloud sql instances create practice-databases \
    --database-version=POSTGRES_15 \
    --region=europe-west2 \
    --tier=TIER \
    --edition=ENTERPRISE_PLUS
