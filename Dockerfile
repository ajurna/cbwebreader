FROM python:3-alpine

ENV PYTHONUNBUFFERED 1

RUN apk update
RUN apk add --no-cache tini bash unrar dcron postgresql-dev gcc python3-dev musl-dev

RUN apk add --no-cache --virtual .build-deps mariadb-dev build-base \
    && pip install pipenv \
    && apk add --virtual .runtime-deps mariadb-connector-c-dev mariadb-connector-c \
    && apk del .build-deps

RUN mkdir /src

WORKDIR /src

ADD Pipfile /src
ADD Pipfile.lock /src

RUN pipenv install --deploy --dev --ignore-pipfile --system

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000


