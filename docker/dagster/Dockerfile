FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl libgomp1 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements-dagster.txt ./
# SQLAlchemy 2.1 resolves postgresql:// to its psycopg (v3) dialect, which
# dagster-postgres 0.29 does not support: webserver/daemon crash-loop on
# start with "psycopg.OperationalError: the connection is closed". Pin 2.0
# so the URL resolves to psycopg2 (installed via dagster-postgres).
RUN pip install --no-cache-dir -r requirements-dagster.txt "sqlalchemy<2.1" && pip install --no-cache-dir -e .

COPY ingestion ./ingestion
COPY transformations ./transformations
COPY ml ./ml
COPY connections ./connections
COPY scripts ./scripts
COPY dagster ./dagster
COPY storage_config.py ./storage_config.py

ENV PYTHONPATH=/app
EXPOSE 3000

CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-w", "/app/dagster/workspace.yaml"]
