FROM python:3

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

RUN apt update
RUN apt install -y software-properties-common
RUN apt-add-repository non-free
RUN apt update

COPY requirements.txt /src
COPY package.json /src
COPY package-lock.json /src

#RUN apt install -y  build-essential postgresql libmariadb-dev libmupdf-dev python3-dev libfreetype-dev libffi-dev libjbig2dec0-dev libjpeg-dev libharfbuzz-dev npm\
#    && apt install tini bash unrar python3 mariadb-connector-c jpeg postgresql-libs jbig2dec jpeg openjpeg harfbuzz mupdf postgresql-client\
#    && npm install \
#    && pip install --upgrade pip \
#    && pip install -r requirements.txt \
#    && apt remove build-essential postgresql-dev mariadb-dev mariadb-connector-c-dev mupdf-dev python3-dev freetype-dev libffi-dev jbig2dec-dev jpeg-dev openjpeg-dev harfbuzz-dev npm

RUN apt install -y software-properties-common \
    && apt install -y npm cron unrar \
    && npm install \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt remove -y npm \
    && apt -y auto-remove

COPY entrypoint.sh /src

COPY . /src/

RUN cat /src/cbreader/crontab >> /etc/cron.daily/cbreader

EXPOSE 8000
