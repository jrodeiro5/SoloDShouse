FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# mlflow's postgresql:// backend resolves to SQLAlchemy's psycopg (v3) dialect
# in this dependency set; psycopg2-binary alone crashes the server with
# "ModuleNotFoundError: No module named 'psycopg'" (healthcheck then fails).
RUN pip install --no-cache-dir mlflow==3.10.1 psycopg2-binary "psycopg[binary]" boto3

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
