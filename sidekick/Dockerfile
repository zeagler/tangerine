FROM alpine:latest
MAINTAINER zeagler

RUN apk add --no-cache --update \
            bash \
            bc \
            docker \
            jq \
            postgresql \
    && rm -rf /var/cache/apk/*

COPY sidekick.sh /sidekick.sh
CMD ["bash", "/sidekick.sh"]