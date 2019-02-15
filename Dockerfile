FROM python:3-alpine
ENV PYTHONUNBUFFERED 1
RUN apk update
RUN apk add --no-cache tini bash unrar dcron postgresql-dev
RUN mkdir /src
WORKDIR /src
RUN apk add --no-cache --virtual .build-deps mariadb-dev build-base \
    && pip install pipenv \
    && pipenv install --system \
    && apk add --virtual .runtime-deps mariadb-connector-c-dev mariadb-connector-c \
    && apk del .build-deps
ADD . /src/
RUN cat /src/cbreader/crontab >> /etc/crontabs/root