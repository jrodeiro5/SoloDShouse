# SDS-030: Dominio ENTSO-E reemplaza ECB/DAX

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloLakehouse fue construido para datos financieros: tipos de interes del ECB (European Central Bank) y precios de acciones del DAX. SoloDShouse pivotiza hacia energia: datos de ENTSO-E (European Network of Transmission System Operators for Electricity).

Este cambio de dominio es fundamental y afecta: los colectores de datos (ingestion/collectors/), los schemas de datos (ingestion/schema/), la logica de transformacion (transformations/), los modelos de ML (ml/), y el feature engineering.

## Decision

Se reemplaza toda la logica de dominio ECB/DAX con datos de energia ENTSO-E.

La API de ENTSO-E Transparency Platform proporciona: day-ahead prices, generation forecasts, load data, cross-border flows, capacity data — todo gratuito, sin API keys necesarias. Los datos meteorologicos provienen de la API de Open-Meteo (gratuita, 10K llamadas/dia). Se necesitan nuevos colectores, schemas Pydantic, y transformaciones. Los nombres de tablas Iceberg cambian: bronze.ecb_rates → bronze.entso_e_day_ahead, etc.

## Rationale

- **Datos abiertos:** ENTSO-E proporciona datos de mercado electrico europeo de forma gratuita y sin registro complejo. Esto alinea con el principio anti-cloud y zero-cost de SoloDShouse.
- **Relevancia para ML + AI:** Los datos de energia tienen patrones temporales claros (estacionalidad, weather-dependent) que son ideales para modelos de forecasting y para demostrar capacidades de ML en un TFM.
- **No requiere API keys:** A diferencia de muchas fuentes financieras (Bloomberg, Refinitiv), ENTSO-E no requiere credenciales de pago. Esto simplifica el despliegue y la reproducibilidad.
- **Weather correlation:** La correlacion entre datos meteorologicos (temperatura, radiacion solar, velocidad del viento) y datos de energia (demand, generation renewable) permite feature engineering rico y modelos hibridos.

## Consequences

- **Positivas:** Datos reales, abiertos, y relevantes para el sector energetico europeo. Patrones temporales fuertes adecuados para forecasting. Sin costes de API ni barreras de acceso.
- **Negativas:** Requiere reescribir todos los colectores y schemas. La logica de transformacion financiera (rendimientos, volatilidad, ratios) no aplica a datos de energia. Los modelos de ML deben reentrenarse desde cero con nuevos features.

## Alternatives Considered

- **Mantener ECB/DAX y anadir ENTSO-E:** Rechazado porque complica el TFM con dos dominios. Un TFM debe tener alcance definido y manejable. El pivot completo mantiene el foco.
- **Usar datos de energia de otra fuente (EIA, OpenEI):** Rechazado porque ENTSO-E es el estandar europeo y los datos estan en unidades y formatos consistentes para el mercado europeo. Open-Meteo complementa perfectamente con datos meteorologicos europeos.
- **Datos sinteticos:** Rechazado porque un TFM de Master debe demostrar capacidad de trabajar con datos reales del mundo. Los datos sinteticos no tienen valor academico para este nivel.
