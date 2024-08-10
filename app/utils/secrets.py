from os import getenv
from google.cloud import secretmanager

secret_client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_name):

    project = getenv("PROJECT")
    name = secret_client.secret_version_path(project, secret_name, "latest")
    response = secret_client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')