FROM rancher/agent:v1.0.2
MAINTAINER zeagler

RUN apt-get update
RUN apt-get build-dep -y python-psycopg2
RUN pip install psycopg2
RUN mkdir /task-scheduler

COPY *.py README.md /task-scheduler/
ENTRYPOINT python /task-scheduler/main.py