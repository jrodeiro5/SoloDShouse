"""Dagster resources for SoloDShouse orchestration."""

from __future__ import annotations

import os

from dagster import ConfigurableResource
from storage_config import get_storage_config

DEFAULT_STORAGE_CONFIG = get_storage_config()


class IcebergCatalogResource(ConfigurableResource):
    """Configurable pyiceberg HiveCatalog resource for all medallion writes."""

    hive_metastore_uri: str = os.environ.get(
        "HIVE_METASTORE_URI", "thrift://localhost:9083"
    )
    warehouse: str = DEFAULT_STORAGE_CONFIG.warehouse_uri.replace("s3a://", "s3://")
    s3_endpoint: str = os.environ.get("OBJECT_STORE_ENDPOINT", "http://localhost:8333")
    access_key: str = os.environ.get(
        "S3_ACCESS_KEY", os.environ.get("OBJECT_STORE_ACCESS_KEY", "solodshouse")
    )
    secret_key: str = os.environ.get(
        "S3_SECRET_KEY", os.environ.get("OBJECT_STORE_SECRET_KEY", "solodshouse123")
    )

    def get_catalog(self):  # type: ignore[return]
        from ingestion.iceberg_io import get_catalog

        return get_catalog(
            uri=self.hive_metastore_uri,
            warehouse=self.warehouse,
            s3_endpoint=self.s3_endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )


class PipelineConfigResource(ConfigurableResource):
    """Pipeline runtime config resource."""

    bucket: str = DEFAULT_STORAGE_CONFIG.data_bucket
    audit_bucket: str = DEFAULT_STORAGE_CONFIG.audit_bucket
    mlflow_artifact_bucket: str = DEFAULT_STORAGE_CONFIG.mlflow_artifact_bucket
    mlflow_artifact_root: str = DEFAULT_STORAGE_CONFIG.mlflow_artifact_root
    warehouse_uri: str = DEFAULT_STORAGE_CONFIG.warehouse_uri
    mlflow_tracking_uri: str = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    trino_url: str = os.environ.get("TRINO_URL", "http://localhost:8080")
