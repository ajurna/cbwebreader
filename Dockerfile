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

RUN apt install -y software-properties-common \
    && apt install -y npm cron unrar \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt -y auto-remove

COPY . /src/

WORKDIR /src/frontend

RUN npm install
RUN npm run build
WORKDIR /src


RUN cat /src/cbreader/crontab >> /etc/cron.daily/cbreader

EXPOSE 8000
