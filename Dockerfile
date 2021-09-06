# syntax=docker/dockerfile:1.2

ARG DEBIAN_FRONTEND=noninteractive

FROM python:3.9.7-slim-buster AS python-base

RUN groupadd --gid 1000 python && useradd --uid 1000 --gid python --shell /bin/bash --create-home python

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


FROM python-base AS python-requirements

RUN set -x; \
        if ! command -v curl > /dev/null; then \
            apt-get update; \
            apt-get install --no-install-recommends -y curl; \
            rm -rf /var/lib/apt/lists/*; \
        fi

ENV POETRY_VERSION=1.1.8 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    PIP_DEFAULT_TIMEOUT=100

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app/target

RUN set -ex && \
        pip3 install --no-cache-dir -U pip && \
        pip3 install --no-cache-dir -U setuptools wheel && \
        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py >get-poetry.py && \
        python3.9 get-poetry.py

COPY pyproject.toml poetry.lock ./

RUN poetry export --format=requirements.txt >requirements-prod.txt


FROM python-base AS titan

RUN --mount=from=python-requirements,src=/app/target,target=/app/target set -x && \
        pip3 install --no-cache-dir -U pip && \
        pip3 install --no-cache-dir -U setuptools wheel && \
        pip3 install --no-cache-dir -r target/requirements-prod.txt

COPY titan ./titan/

# ignore environment and always run on default port
# 'redis' and 'postgres' are expected at default ports 6379 and 5432 respectively.
EXPOSE 3001

USER python

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "3001", \
     "--log-config", "titan/log_config.json", \
     "titan.main:app"]
