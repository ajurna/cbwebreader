FROM python:3.14-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
ENV PATH="${PATH}:/root/.local/bin"

RUN mkdir /src
RUN mkdir /static

WORKDIR /src



RUN  echo "deb http://ftp.uk.debian.org/debian trixie non-free non-free-firmware" > /etc/apt/sources.list.d/non-free.list

RUN apt update \
    && apt install -y npm cron unrar libmariadb-dev libpq-dev pkg-config swig curl

COPY . /src/

RUN uv sync --frozen --no-dev

RUN cd frontend \
    && npm install \
    && npm run build \
    && rm -r node_modules


RUN cat /src/cbreader/crontab >> /etc/crontab

EXPOSE 8000
