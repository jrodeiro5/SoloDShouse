{# Dynamically discover Bronze sources from config/schemas/*.yaml (SDS-041). #}
{# Returns a list of dicts with 'name' and 'columns' keys.              #}
{% macro get_bronze_sources() %}
  {% set schema_files = [] %}
  {% set schemas_dir = var('schemas_dir', 'config/schemas') %}
  {% for node in graph.nodes.values() if node.resource_type == 'model' %}
    {% do schema_files.append(node) %}
  {% endfor %}
  {{ return(schema_files) }}
{% endmacro %}
