CREATE DATABASE hive_metastore;
CREATE DATABASE mlflow;
CREATE DATABASE dagster_storage;

\c postgres
CREATE EXTENSION IF NOT EXISTS vector;
-- No postgis: pgvector/pgvector:pg17 does not ship it, and this line aborts
-- fresh initdb (docker-entrypoint exit 3). Tracked in task.md "Add PostGIS extension".
