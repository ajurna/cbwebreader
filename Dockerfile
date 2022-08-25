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

COPY . /src/

RUN apt install -y npm cron unrar \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && cd frontend \
    && npm install \
    && npm run build \
    && rm -r node_modules \
    && apt -y auto-remove

WORKDIR /src

RUN cat /src/cbreader/crontab >> /etc/cron.daily/cbreader

EXPOSE 8000
