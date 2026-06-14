{# Generic data quality test — validates row count is above threshold. #}
{% test min_rows(model, min_rows=1) %}
  SELECT COUNT(*) AS row_count FROM {{ model }}
  HAVING COUNT(*) < {{ min_rows }}
{% endtest %}


{# Generic data quality test — validates column completeness above threshold. #}
{% test completeness(model, column_name, threshold=0.9) %}
  SELECT
    COUNT(*) AS total,
    COUNT({{ column_name }}) AS filled,
    (COUNT({{ column_name }}) * 1.0 / COUNT(*)) AS completeness_pct
  FROM {{ model }}
  HAVING (COUNT({{ column_name }}) * 1.0 / COUNT(*)) < {{ threshold }}
{% endtest %}
