from __future__ import annotations

import os
import uuid
from pathlib import Path

import boto3
import pytest
from botocore.config import Config

from ingestion.iceberg_io import get_catalog


def load_dotenv_if_present() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


@pytest.fixture(scope="session")
def s3_client():
    load_dotenv_if_present()
    endpoint = os.environ.get("OBJECT_STORE_ENDPOINT", "http://localhost:8333")
    access_key = os.environ.get("S3_ACCESS_KEY", os.environ.get("OBJECT_STORE_ACCESS_KEY", "solodshouse"))
    secret_key = os.environ.get("S3_SECRET_KEY", os.environ.get("OBJECT_STORE_SECRET_KEY", "solodshouse123"))

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    try:
        client.list_buckets()
    except Exception as exc:
        pytest.skip(f"SeaweedFS S3 unreachable for integration tests: {exc}")
    return client


@pytest.fixture(scope="session")
def iceberg_catalog():
    load_dotenv_if_present()
    try:
        catalog = get_catalog()
        catalog.list_namespaces()
        return catalog
    except Exception as exc:
        pytest.skip(f"Iceberg catalog unreachable for integration tests: {exc}")


@pytest.fixture(scope="session")
def test_bucket(s3_client) -> str:
    bucket_name = f"solodshouse-test-{uuid.uuid4().hex[:8]}"
    s3_client.create_bucket(Bucket=bucket_name)
    try:
        yield bucket_name
    finally:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get("Contents", []):
                s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
        s3_client.delete_bucket(Bucket=bucket_name)
