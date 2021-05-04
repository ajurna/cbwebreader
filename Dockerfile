FROM python:3-alpine

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir /src
RUN mkdir /static

WORKDIR /src

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk update
RUN apk add --no-cache tini bash unrar dcron postgresql-dev gcc python3-dev musl-dev libffi-dev jpeg-dev

RUN apk add --no-cache --virtual .build-deps mariadb-dev build-base \
    && apk add --virtual .runtime-deps mariadb-connector-c-dev mariadb-connector-c \
    && apk del .build-deps

RUN pip install --upgrade pip

COPY requirements.txt /src

RUN pip install -r requirements.txt

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /src

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000


