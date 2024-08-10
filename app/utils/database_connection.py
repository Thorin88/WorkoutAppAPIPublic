import sqlalchemy as sa
from os import getenv

from .secrets import get_secret

class UnknownDatabaseType(Exception):
    pass

def generate_db_url(db_type: str, port=None) -> str:

    project = getenv("PROJECT")
    location = getenv("LOCATION")
    cloud_db_instance_name = getenv("CLOUD_DB_INSTANCE_NAME")

    cloud_db_credentials_secret_name = getenv("CLOUD_DB_CREDENTIALS_SECRET_NAME")
    # All DBs are in the same instance, need another variable if this is not the case.
    cloud_db_name = getenv("CLOUD_DB_NAME")

    db_port = getenv('DB_PORT')

    if db_type == "local":

        local_db_port = getenv('LOCAL_DB_PORT')
        local_db_name = getenv('LOCAL_DB_NAME')
        # For local use, user and password is ok to be known. In GCP DB cases, these two fields will be extracted via the
        # secrets API.
        local_db_user = getenv('LOCAL_DB_USER')
        local_db_password = getenv('LOCAL_DB_PASSWORD')

        db_url = f"postgresql://{local_db_user}:{local_db_password}@host.docker.internal:{local_db_port}/{local_db_name}"

    elif db_type == "cloud_run":

        # Endpart is the connection name provided on GCP
        db_url = f"postgresql://{get_secret(cloud_db_credentials_secret_name)}@localhost/{cloud_db_name}?host=/cloudsql/{project}:{location}:{cloud_db_instance_name}"

    # TODO -> Connection to GCP based DBs from local runs
    elif db_type == "cloud_local":

        db_url = f"postgresql://{get_secret(cloud_db_credentials_secret_name)}@host.docker.internal:{db_port}/{cloud_db_name}"
        
    else:
        raise UnknownDatabaseType(f"Unknown database type: {db_type}")
        
    return db_url