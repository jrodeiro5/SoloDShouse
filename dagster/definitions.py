"""Dagster definitions for SoloDShouse AI energy cost domain."""

from __future__ import annotations

import os
import sys

from dagster import AssetSelection, Definitions, ScheduleDefinition, define_asset_job

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from assets import (  # noqa: E402
    cloud_pricing_bronze,
    cloud_pricing_silver,
    cloud_pricing_silver_min_rows_check,
    mlperf_bronze,
    mlperf_freshness_sensor,
    mlperf_silver,
    mlperf_silver_min_rows_check,
)
from resources import IcebergCatalogResource, PipelineConfigResource  # noqa: E402

bronze_assets = [mlperf_bronze, cloud_pricing_bronze]
silver_assets = [mlperf_silver, cloud_pricing_silver]
all_assets = [*bronze_assets, *silver_assets]

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

defs = Definitions(
    assets=all_assets,
    asset_checks=[mlperf_silver_min_rows_check, cloud_pricing_silver_min_rows_check],
    jobs=[full_pipeline_job, bronze_only_job],
    schedules=[daily_pipeline_schedule],
    sensors=[mlperf_freshness_sensor],
    resources={
        "pipeline_config": PipelineConfigResource(),
        "iceberg_catalog": IcebergCatalogResource(),
    },
)
