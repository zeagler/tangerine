FROM rancher/agent:v1.0.2
MAINTAINER zeagler

RUN apt-get update
RUN apt-get build-dep -y python-psycopg2
RUN pip install psycopg2 boto3
RUN mkdir /tangerine

COPY *.py README.md /tangerine/
ENTRYPOINT python /tangerine/tangerine.py