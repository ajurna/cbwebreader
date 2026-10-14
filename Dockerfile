# ---------------------------------------------------------------------------
# Frontend build stage
# ---------------------------------------------------------------------------
FROM node:22-slim AS frontend

WORKDIR /src

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# unrar lives in the non-free component; resolve the codename from the base image
# instead of hardcoding it.
RUN . /etc/os-release \
    && echo "deb http://deb.debian.org/debian ${VERSION_CODENAME} non-free non-free-firmware" \
        > /etc/apt/sources.list.d/non-free.list \
    && apt update \
    && apt install -y --no-install-recommends cron unrar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Lockfiles first so dependency installation is cached independently of the source.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . /src/
COPY --from=frontend /src/dist /src/frontend/dist
COPY --from=frontend /src/webpack-stats.json /src/frontend/webpack-stats.json

RUN mkdir -p /static /media

RUN cat /src/cbreader/crontab >> /etc/crontab

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["sh", "entrypoint.sh"]
