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

ARG MUPDF=1.18.0

COPY requirements.txt /src

RUN apk add --no-cache --virtual .build-deps gcc build-base g++ cmake make postgresql-dev mariadb-dev mariadb-connector-c-dev musl-dev mupdf-dev python3-dev freetype-dev libffi-dev \
    && apk add --no-cache  tini bash unrar dcron python3 mariadb-connector-c jpeg-dev postgresql-libs \
    && ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h \
    && ln -s /usr/include/freetype2/freetype/ /usr/include/freetype \
    && wget -c -q https://www.mupdf.com/downloads/archive/mupdf-${MUPDF}-source.tar.gz \
    && tar xf mupdf-${MUPDF}-source.tar.gz \
    && cd mupdf-${MUPDF}-source \
    && make HAVE_X11=no HAVE_GLUT=no shared=yes prefix=/usr/local install \
    && cd .. \
    && rm -rf *.tar.gz mupdf-${MUPDF}-source \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apk del .build-deps

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /src

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000
