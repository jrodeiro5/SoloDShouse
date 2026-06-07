# TFM — Contexto y Encuadre

**Trabajo Fin de Máster**: Master en Big Data, Data Science & Inteligencia Artificial  
**Universidad**: Universidad Complutense de Madrid (UCM)  
**Alumno**: jrodeiro5  
**Repo**: github.com/jrodeiro5/SoloDShouse

---

## Encuadre: IberGrid (Módulo 14)

El proyecto se enmarca como si fuera desarrollado para **IberGrid**, una empresa energética española ficticia inspirada en Red Eléctrica de España (REE). IberGrid necesita:

- Monitorizar la generación eléctrica por país (ENTSO-E) y correlacionarla con condiciones meteorológicas (Open-Meteo).
- Predecir la demanda y generación con modelos ML para optimizar el balance de red.
- Detectar anomalías en la generación (posibles fallos de planta o eventos extremos).
- Consultar datos históricos y en tiempo real mediante agentes de lenguaje natural.

Este encuadre convierte el TFM de un ejercicio técnico en un caso de uso industrial realista.

---

## Hipótesis de investigación

> ¿Es posible construir una plataforma de Data Science + AI completa (lakehouse, ML, agentes LLM) que corra íntegramente en hardware local asequible (Mac Studio M4 Max + VPS €5/mes), sin dependencias de cloud y con un coste mensual < €25?

**Variables**:
- Hardware objetivo: Mac Studio M4 Max (64 GB) para DEV, Hetzner CPX21 (4 GB) para STAGING
- Coste máximo cloud: €5/mes (solo VPS)
- Stack cubierto: 15 módulos del máster

---

## Contribuciones esperadas

1. Arquitectura medallión local-first (Bronze→Silver→Gold vía Iceberg)
2. Pipeline ML completo (XGBoost/LightGBM + LSTM) sobre datos ENTSO-E reales
3. Capa de agentes LLM con memoria estructurada (deepagents + mem0 + kotaemon)
4. Demostración de viabilidad en hardware local sin sorpresas de factura cloud

---

## Restricciones de diseño

| Restricción | Valor |
|-------------|-------|
| RAM DEV | 64 GB (Mac Studio M4 Max) |
| RAM STAGING | 4 GB (Hetzner CPX21) |
| Coste mensual máximo | €25 total (VPS + APIs) |
| LLM local (DEV) | llama.cpp / vLLM (hasta 70B) |
| LLM STAGING | Groq API (free tier) vía LiteLLM |
| Vendor lock-in | Cero — todo Open Source o self-hosted |

---

## Ver también

- `docs/solodshouse/tfm/module-coverage.md` — cobertura por módulo UCM
- `docs/solodshouse/tfm/architecture-guide.md` — guía técnica completa
- `docs/solodshouse/decisions/` — ADRs SDS-XXX
