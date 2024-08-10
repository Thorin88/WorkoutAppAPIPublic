# Workout App API

This version of the code has been prepared for [Google's Gemini Competition](https://ai.google.dev/competition). This means that an AI powered element has been introduced into the application. The code is a little bit rough around the edges in places, due to this competition's deadline, but this will be smoothed out in following updates.

The API supports the Android app that I built [here](https://github.com/Thorin88/WorkoutAppPublic).

## Running the API

### Local

Requirements: Docker, GCP CLI

Since the API uses GCP to access Gemini, you will need to be logged into the GCP CLI for a GCP project, as the Docker build process will use your default credentials to gain access to Gemini.

You may need to change this part of the `docker-compose.yaml` file if your path to your default GCP credentials is different:

```
"$APPDATA/gcloud/application_default_credentials.json:/tmp/keys/credentials.json:ro"
```

to

```
YOUR_PATH_TO_GCP_DEFAULT_CREDENTIALS:/tmp/keys/credentials.json:ro"
```

Environment variables for this configuration are to be defined in the `config/local.yaml` file.

Depending on your Docker version, use either:

`docker-compose up --build --remove-orphans`

or

`docker compose up --build --remove-orphans`

This will setup up the API listening at `http://localhost:8080` by default.

### Cloud

The API can be deployed to GCP, but it is easiest to run/test locally as the API will need to refer to certain secrets and SQL instances in this case.

## Documentation

Please run the API locally and visit the url `http://localhost:8080/docs` in your browser. This page contains detailed information about the endpoints provided by this API.

## Summary of Features

Authentication for the app (custom built for learning purposes).

Creating workouts.

Retrieving created workouts.

Generating workouts via requests to Gemini.

Tracking completed workouts.

Editing workouts.