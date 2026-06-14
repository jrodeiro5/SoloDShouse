{# Generic staging model — reads any DuckDB table passed via --vars (SDS-041). #}
{# Usage: dbt run --select stg_generic --vars '{"source_table": "bronze_mlperf"}' #}

SELECT
  *
FROM {{ var('source_table', 'no_table_specified') }}
