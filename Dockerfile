FROM alpine:latest
MAINTAINER zeagler

RUN apk add --no-cache --update \
            ca-certificates \
            gcc \
            musl-dev \
            postgresql-dev \
            python \
            python-dev \
            py-pip \
            tzdata \
    && pip install boto3 cattle cherrypy croniter mako psycopg2 pyyaml \
    && apk del --purge gcc musl-dev python-dev py-pip \
    && rm -rf /var/cache/apk/* \
    && rm -rf /root/.cache/pip
    
RUN mkdir /tangerine

COPY *.py README.md /tangerine/
COPY UI /tangerine/UI
CMD ["python", "tangerine.py"]
WORKDIR /tangerine