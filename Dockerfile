FROM python:3-alpine3.14

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

COPY requirements.txt /src
COPY package.json /src
COPY package-lock.json /src

RUN apk add --no-cache --virtual .build-deps gcc build-base g++ cmake make postgresql-dev mariadb-dev mariadb-connector-c-dev mupdf-dev python3-dev freetype-dev libffi-dev jbig2dec-dev jpeg-dev openjpeg-dev harfbuzz-dev npm\
    && apk add --no-cache tini bash unrar dcron python3 mariadb-connector-c jpeg postgresql-libs jbig2dec jpeg openjpeg harfbuzz mupdf postgresql-client\
    && npm install \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apk del .build-deps

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000
