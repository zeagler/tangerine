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
    && pip install boto3 cattle psycopg2 web.py \
    && apk del --purge gcc musl-dev python-dev py-pip \
    && rm -rf /var/cache/apk/* \
    && rm -rf /root/.cache/pip
    
RUN mkdir /tangerine

COPY *.py README.md /tangerine/
COPY static /tangerine/static
CMD ["python", "tangerine.py"]
WORKDIR /tangerine