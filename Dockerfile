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
    && apk add --virtual .runtime-deps mariadb-connector-c-dev mariadb-connector-c

RUN apk add gcc g++ cmake make mupdf-dev freetype-dev
ARG MUPDF=1.18.0
RUN ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h \
    && ln -s /usr/include/freetype2/freetype/ /usr/include/freetype \
    && wget -c -q https://www.mupdf.com/downloads/archive/mupdf-${MUPDF}-source.tar.gz \
    && tar xf mupdf-${MUPDF}-source.tar.gz \
    && cd mupdf-${MUPDF}-source \
    && make HAVE_X11=no HAVE_GLUT=no shared=yes prefix=/usr/local install \
    && cd .. \
    && rm -rf *.tar.gz mupdf-${MUPDF}-source

RUN pip install --upgrade pip

RUN pip install PyMuPDF==1.18.12

COPY requirements.txt /src

RUN pip install -r requirements.txt

RUN apk del .build-deps

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /src

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/crontabs/root

EXPOSE 8000


