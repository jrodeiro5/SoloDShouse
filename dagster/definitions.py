"""Dagster definitions for SoloDShouse — auto-discovered from registry (SDS-043)."""

from __future__ import annotations

import os
import sys

from dagster import AssetSelection, Definitions, ScheduleDefinition, define_asset_job

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from assets import (  # noqa: E402
    all_assets,
    bronze_assets,
    make_silver_checks,
    mlperf_freshness_sensor,
)
from resources import IcebergCatalogResource, PipelineConfigResource  # noqa: E402

full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    selection=AssetSelection.assets(*all_assets),
)

bronze_only_job = define_asset_job(
    name="bronze_only_job",
    selection=AssetSelection.assets(*bronze_assets),
)

daily_pipeline_schedule = ScheduleDefinition(
    name="daily_pipeline_schedule",
    job=full_pipeline_job,
    cron_schedule="0 7 * * *",
    execution_timezone="UTC",
)

_silver_checks = make_silver_checks()

defs = Definitions(
    assets=all_assets,
    asset_checks=_silver_checks,
    jobs=[full_pipeline_job, bronze_only_job],
    schedules=[daily_pipeline_schedule],
    sensors=[mlperf_freshness_sensor],
    resources={
        "pipeline_config": PipelineConfigResource(),
        "iceberg_catalog": IcebergCatalogResource(),
    },
)
