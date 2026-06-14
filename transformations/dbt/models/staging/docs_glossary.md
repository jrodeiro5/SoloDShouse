# SoloDShouse Business Glossary (SDS-041)
#
# Domain-agnostic data governance — define your business terms here.
# Each term links to the technical dictionary via dbt docs blocks.
#
# Pattern:
#   {% docs term_name %}
#   Business definition of the term. What it means, who owns it,
#   how it's calculated, and what data assets map to it.
#   {% enddocs %}
#
# Usage in schema.yml:
#   description: '{{ doc("term_name") }}'

{% docs data_domain %}
A logical grouping of data assets by business function or nature.
Domains define ownership boundaries and access control scopes.
{% enddocs %}

{% docs data_owner %}
The business role accountable for data quality, definition,
and access policy within a domain. Maps to UCM governance roles:
Data Owner (accountable) + Data Steward (operational).
{% enddocs %}

{% docs data_lineage %}
The end-to-end trace of data from source system through
transformations to consumption. Enabled in SoloDShouse via
Dagster asset dependencies and dbt model ref() graph.
{% enddocs %}

{% docs bronze_layer %}
Raw ingested data — immutable, append-only, partitioned by
_ingestion_timestamp. Stored in Apache Iceberg under iceberg.bronze.*
{% enddocs %}

{% docs silver_layer %}
Cleaned and typed data — full overwrite per pipeline run.
Deduplicated, type-cast, derived fields added.
Stored in Apache Iceberg under iceberg.silver.*
{% enddocs %}

{% docs gold_layer %}
ML-ready feature matrix — dbt transforms Silver into analytics-optimized
models. Queryable via DuckDB and Trino.
{% enddocs %}

{% docs data_quality %}
Measurable properties of data fitness for use: completeness,
freshness, uniqueness, validity. Enforced via dbt tests.
{% enddocs %}

{% docs pii_classification %}
Personal Identifiable Information classification levels:
public, internal, confidential, restricted (GDPR/CCPA).
Applied via dbt meta tags on columns and models.
{% enddocs %}
