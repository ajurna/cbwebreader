FROM alpine:latest

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
RUN apk add gcc g++ cmake make mupdf-dev freetype-dev
RUN ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h \
    && ln -s /usr/include/freetype2/freetype/ /usr/include/freetype \
    && wget -c -q https://www.mupdf.com/downloads/archive/mupdf-${MUPDF}-source.tar.gz \
    && tar xf mupdf-${MUPDF}-source.tar.gz \
    && cd mupdf-${MUPDF}-source \
    && make HAVE_X11=no HAVE_GLUT=no shared=yes prefix=/usr/local install \
    && cd .. \
    && rm -rf *.tar.gz mupdf-${MUPDF}-source


COPY requirements.txt /src

RUN apk add --no-cache --virtual .build-deps build-base postgresql-dev mariadb-dev mariadb-connector-c-dev postgresql-libs musl-dev python3-dev freetype-dev libffi-dev \
    && apk add --no-cache  tini bash unrar dcron python3 py3-pip mariadb-connector-c py3-wheel jpeg-dev postgresql-libs \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apk del .build-deps

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /src

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000


