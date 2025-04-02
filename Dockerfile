FROM python:3.13-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN mkdir /src
RUN mkdir /static

WORKDIR /src

COPY . /src/


RUN apt update \
    && apt install -y software-properties-common \
    && apt-add-repository non-free \
    && apt update \
    && apt install -y npm cron unrar libmariadb-dev libpq-dev \
    && uv sync \
    && cd frontend \
    && npm install \
    && npm run build \
    && apt remove -y npm software-properties-common \
    && rm -r node_modules \
    && apt -y auto-remove \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

RUN cat /src/cbreader/crontab >> /etc/cron.daily/cbreader

EXPOSE 8000
