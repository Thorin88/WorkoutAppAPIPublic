from dotenv import load_dotenv
from os import getenv

from .utils.database_connection import generate_db_url

# Important: app.db cannot be imported until this file is imported.

load_dotenv()

class Config(object):

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # Specified in the environment file, indicates which database connection to try and establish.
    DB_TYPE = getenv('DB_TYPE')
    # Used within the code base to restrict certain behaviour based on the development mode
    ENV = getenv('ENV')

    db_url = generate_db_url(DB_TYPE)

    # Using binds to ensure DB usage is always deliberate
    SQLALCHEMY_BINDS = {
        "core_db": db_url
    }

# Can have a base Config, and then additional ones which setup other variables on top of the base Config.
class DevConfig(Config):
    def __init__(self):
        super().__init__()
        print("API environment setup uising DevConfig")

class DebugConfig(Config):
    def __init__(self):
        super().__init__()
        print("API environment setup uising DebugConfig")