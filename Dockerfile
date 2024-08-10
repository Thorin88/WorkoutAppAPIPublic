FROM python:3.11.9-slim

# Separate lines to make it easier to debug
RUN apt-get update
# Required for non-binary install of psycopg2
RUN apt-get -y install libpq-dev gcc
RUN pip install --upgrade pip

# Moved after these RUNs to ensure that changes to this file don't cause the RUN layer caches to be invalidated
COPY ./config/requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

EXPOSE $PORT
CMD exec gunicorn --bind :$PORT --worker-class uvicorn.workers.UvicornWorker -c /config/gunicorn.conf.py app:app