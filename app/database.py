"""
Base should be imported by any files which want to access the DB
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from os import getenv

from .utils.database_connection import generate_db_url

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

DB_TYPE = getenv('DB_TYPE')
ENV = getenv('ENV')

db_url = generate_db_url(DB_TYPE)

SQLALCHEMY_DATABASE_URL = db_url

# Using binds to ensure DB usage is always deliberate
SQLALCHEMY_BINDS = {
    "core_db": db_url
}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # TODO -> Pass more parameters here, or in session
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()