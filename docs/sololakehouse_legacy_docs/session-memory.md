# SoloDShouse — Session Memory & Decisions

> **Persistencia**: Este documento resume TODAS las decisiones y contexto de las sesiones de trabajo.
> **Última actualización**: 2026-06-07
> **Repo**: `/Users/jrodeiro/dev/master_ucm/SoloDShouse` (fork de github.com/jrodeiro5/SoloDShouse)
> **Máquina**: Mac Studio M4 Max, 64GB RAM, macOS 26.4

---

## Contexto

- **TFM** (Master UCM): Arquitectura de referencia para plataforma DS + IA agents sobre lakehouse local-first
- **Dominio**: ENTSO-E (energía eléctrica europea) + Open-Meteo (weather)
- **Evolución**: Fork de SoloLakehouse v2.5 (finanzas ECB/DAX → energía ENTSO-E)
- **Prioridad**: DS + ML + Agentes AI primero, lakehouse es la base
- **Idioma preferido**: El usuario escribe en español, responder en español
- **Principio rector**: Local-first, anti-cloud, minimizar recursos (RAM y €)

---

## Stack Completo (confirmado)

### Capa Lakehouse (Base)

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| PostgreSQL 17 + pgvector + PostGIS | DB + vectores + geo | ~300MB | 0 | Contenedor |
| SeaweedFS (o floci S3) | Object storage S3 | ~13-150MB | 0 | Contenedor/binario |
| Dagster (2 containers) | Orquestación | ~400MB | 0 | Contenedor |
| Hive Metastore | Catálogo Iceberg | ~400MB | 0 | Contenedor |
| Trino | Query engine federado | ~1.5GB | 0 | Contenedor |
| Iceberg | Table format | 0 | 0 | Lib Python |
| DuckDB | Queries locales | 0 | 0 | Lib Python (in-process) |
| dbt + MetricFlow | Transformaciones SQL + métricas | 0 | 0 | CLI Python |

### Capa ML

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| MLflow 3.x | Experiment tracking + model registry | ~300MB | 0 | Contenedor |
| XGBoost + LightGBM + scikit-learn | Modelos ML clásicos | 0 | 0 | Lib Python |
| BentoML | Serving modelos clásicos | ~200MB | 0 | Contenedor |

### Capa Agent + IA

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| deepagents | Agent harness sobre LangGraph | ~200MB | 0 | Contenedor |
| ToolUniverse | MCP tools científicos (1000+) | ~50MB | 0 | Lib Python |
| FastMCP | Framework MCP tools | 0 | 0 | Lib Python |
| Open WebUI | Chat UI | ~300MB | 0 | Contenedor |
| FastAPI proxy | OpenAI API → deepagents | ~50MB | 0 | Proceso Python |
| LlamaIndex | RAG orchestration | 0 | 0 | Lib Python |
| kotaemon | RAG UI (multi-user, citations, PDF) | ~1-2GB | 0 | Contenedor |
| mem0 | Memoria estructurada agentes | ~100MB | 0 | Contenedor |
| garak (NVIDIA) | LLM vulnerability scanner | 0 | 0 | CLI Python (audit only) |
| AGT (Microsoft) | Agent governance (policy enforcement) | ~50MB | 0 | Lib Python (middleware) |
| Adala | Data labeling agent | 0 | 0 | Lib Python |

### Capa LLM

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| LiteLLM | LLM gateway unificado | ~150MB | 0 | Contenedor |
| llama.cpp / vLLM | Inferencia LLM local | 0-55GB | 0 | On-demand |
| Groq API | LLM externo (VPS) | 0 | 0 (free tier) | API externo |

### Capa Observabilidad

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| Langfuse | LLM traces + eval + prompt mgmt | ~300MB | 0 | Contenedor |
| Prometheus + node_exporter | Métricas sistema | ~100MB | 0 | Contenedor |
| Alertmanager | Alert routing | ~50MB | 0 | Contenedor |
| Apprise (en deepagents) | Notificaciones (Telegram/Slack/WA) | 0 | 0 | Lib Python |
| 🔇 Grafana + Loki | Dashboards + logs (compose profile) | ~400MB | 0 | Contenedor |

> 🔇 = disponible como compose profile, NO en stack core. Reemplazado por Alertmanager + Apprise.

### Capa BI / Docs / Catalogación

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| Evidence.dev | BI principal (markdown-first) | ~200MB | 0 | Contenedor |
| dbt docs + MetricFlow | Catálogo datos + métricas declarativas | 0 | 0 | CLI Python |
| Astro Starlight | Docs site | ~200MB | 0 | Node + build estático |
| Portal web (nginx) | Hub central de servicios | ~10MB | 0 | Contenedor |

### Capa Datos / Infra adicional

| Componente | Rol | RAM (cont.) | €/mes | Tipo |
|------------|-----|:-----------:|:-----:|------|
| MongoDB | NoSQL (UCM mod 5) | ~300MB | 0 | Contenedor |
| Spark | Big data processing (UCM mod 11, on-demand) | ~4GB | 0 | Compose profile |
| DeepSeek-OCR | OCR documentos (si hay PDFs) | 0 (GPU) | 0 | On-demand |

---

## Costes por Perfil Docker Compose

### DEV — Mac Studio M4 Max (64GB RAM, local)

| Perfil | Servicios | RAM total | €/mes |
|--------|----------|:---------:|:-----:|
| **core** | PG+pgvector+PostGIS, SeaweedFS/floci, Dagster, Hive, Trino, DuckDB | ~2.8GB | 0 |
| **ml** | core + MLflow, BentoML | ~3.3GB | 0 |
| **agent** | ml + deepagents, Open WebUI, LiteLLM, FastAPI proxy, mem0, ToolUniverse+FastMCP, kotaemon, garak, AGT | ~5.4GB | 0 |
| **observabilidad** | Langfuse, Prometheus, Alertmanager | ~0.45GB | 0 |
| **bi** | Evidence.dev, nginx portal, Astro Starlight | ~0.4GB | 0 |
| **full (sin LLM)** | core+ml+agent+obs+bi+MongoDB+Adala | **~6.6GB** | 0 |
| **llm-7b** | full + llama.cpp 7B | **~12.6GB** | 0 |
| **llm-70b** | full + vLLM 70B | **~56.6GB** | 0 |
| **+spark** | + Spark on-demand | **+4GB** | 0 |

### STAGING — Hetzner CPX21 (4GB RAM, ~€5/mes)

| Despliegue | Servicios | RAM | €/mes |
|-----------|----------|:---:|:-----:|
| **VPS mínimo** | PG+pgvector, SeaweedFS, Dagster, LiteLLM, DeepSeek-OCR off | ~2GB | €5.01 |
| **LLM** | Groq API free / OpenAI / túnel SSH a Mac | 0 | 0-€20 |
| **Total VPS** | — | ~2GB | **€5-25/mes** |

### Costes Externos (APIs)

| Servicio | Uso | €/mes estimado |
|---------|-----|:-------------:|
| Groq API | LLM inference (VPS) | €0 (free tier) |
| ENTSO-E API | Datos energía europea | €0 (gratuito) |
| Open-Meteo API | Datos weather | €0 (gratuito, 10K calls/día) |
| OpenAI API (fallback) | LLM si Groq cae | €5-20 |
| Hetzner CPX21 | VPS staging | €5.01 |
| Dominio DNS | solodshouse.example.com | €1-2 |
| **Total mensual** | — | **~€6-27/mes** |

### Costes Onetime (Setup)

| Concepto | € |
|---------|:-:|
| Mac Studio M4 Max (64GB) | ya comprado |
| Hetzner CPX21 setup | €0 (sin fee) |
| Dominio | €10-15/año |

---

## Decisiones Firmadas (2026-06-07)

1. **Evidence.dev = BI principal** — No Lightdash. No Metabase. Superset eliminado completamente.
2. **OpenMetadata eliminado** — Reemplazado por dbt docs + MetricFlow + Adala. Ahorra ~1.5GB.
3. **Adala añadido** — Data labeling agent para calidad de datos.
4. **Trino se queda** — Query engine federado (ADR-002). DuckDB complementa para queries locales.
5. **Hive Metastore se queda** — Necesario para Trino (catálogo Iceberg).
6. **MinIO → SeaweedFS** (o floci S3) — ADR-019 dice "deferir", pero fork es post-v2.5.
7. **Ollama eliminado** — Se usa llama.cpp o vLLM para inferencia local. LiteLLM rutea.
8. **Observabilidad reducida** — Prometheus + node_exporter + Alertmanager (no Grafana/Loki en core). Langfuse para LLM traces.
9. **Superset eliminado** — Evidence.dev cubre BI + SQL. Trino tiene SQL CLI propio.
10. **Alertas vía deepagents + Apprise** — Notificaciones a Telegram/Slack/WA sin servicio extra.
11. **garak (NVIDIA)** — LLM vulnerability scanner. Audit antes de production.
12. **AGT (Microsoft)** — Agent governance toolkit. Policy enforcement en tool calls.
13. **FastMCP** — Framework estándar para MCP tools del lakehouse.
14. **kotaemon** — RAG UI sobre LlamaIndex (multi-user, citations, PDF viewer).
15. **deepagents sobre deer-flow/agno** — Más ligero (200MB vs 1-4GB), ya integrado con stack analítico.

## Pendiente de Decidir

1. **Feast** — Feature store. Propuesto en doc original.
2. **Marimo** — Notebooks reactivos. Propuesto en doc original.
3. **Evidently AI** — Drift monitoring. Propuesto en doc original.
4. **Contexto empresa (UCM mod 14)** — ¿Framing como "IberGrid" o partner real?
5. **Spark profile** — ¿Docker Compose profile on-demand o alternativas?
6. **dbt-spark vs dbt-duckdb** — ADR-016 propuso dbt-spark. ¿dbt-duckdb más ligero?
7. **Observabilidad: Grafana/Loki** — ¿Profile opcional o eliminado definitivamente?
8. **graphiti vs mem0** — Agente memoria: ¿mem0 (simple) o graphiti (KG temporal, requiere Neo4j)?
9. **SQLMesh** — ¿Evaluar como reemplazo de dbt-core? Técnicamente superior pero metrics layer = prototype.
10. **turbovec** — ¿Evaluar como compresión vectorial sobre pgvector? 16x compresión pero no es DB.
11. **OpenSandbox** — ¿Sandbox para agentes? Complementario a deepagents.
12. **gepa** — ¿Optimización de prompts/parámetros? Baja prioridad.
13. **Supabase** — ¿Reemplaza PG+auth+storage+pgvector? Evaluar vs self-hosted PG.

---

## Repos Evaluados — Todas las sesiones

### ✅ Confirmados en stack

| Repo | ★ | Rol en stack |
|------|---|-------------|
| SoloLakehouse | — | Fork base |
| deepagents | 24k | Agent harness sobre LangGraph |
| Open WebUI | 140k | Chat UI |
| ToolUniverse | 1.4k | MCP tools científicos |
| SeaweedFS | — | Object storage S3-compatible |
| litellm | — | LLM gateway |
| Evidence.dev | — | BI principal |
| dbt + MetricFlow | — | Transformaciones + métricas |
| Adala | — | Data labeling agent |
| kotaemon | 25.4k | RAG UI sobre LlamaIndex |
| garak (NVIDIA) | 8k | LLM security scanner |
| AGT (Microsoft) | 4.1k | Agent governance toolkit |
| FastMCP (PrefectHQ) | — | MCP framework estándar |

### ✅ Librerías Python (no contenedores)

| Librería | Rol |
|---------|-----|
| DuckDB | Queries locales |
| LlamaIndex | RAG orchestration |
| mem0 | Memoria agentes |
| Apprise | Notificaciones multi-canal |
| Pydantic v2 | Validación |
| structlog | Logging estructurado |
| XGBoost + LightGBM | Modelos ML |
| scikit-learn | Pipelines ML |
| pyiceberg | I/O Iceberg |
| pgvector | Vectores en PostgreSQL |
| PostGIS | Extension espacial |

### ❌ Rechazados (con razón)

| Repo | ★ | Razón rechazo |
|------|---|---------------|
| NAO | 1.2k | TypeScript backend |
| kubetorch | 1.2k | Requiere K8s |
| AutoScientists | 548 | 1 commit, biomedical |
| mini-swe-agent | 5k | SWE-bench, no energy |
| autoswagger | 1.9k | API security, off-domain |
| autodistill | 2.7k | CV, abandonado |
| MinIO | — | Archivado Abr 2026 |
| quarkdown | 15.4k | Formato .qd propietario |
| Lightdash | — | Evidence.dev cubre necesidades |
| OpenMetadata | — | Eliminado: dbt docs + MetricFlow + Adala |
| Superset | — | Eliminado: Evidence.dev + Trino SQL |
| Grafana | — | Eliminado de core: Alertmanager + Apprise suficiente |
| Loki | — | Eliminado de core: Langfuse para LLM traces suficiente |
| Zabbix | 6k | 4-8GB RAM, overkill para local-first |
| n8n | — | 300MB, deepagents + Apprise cubren alertas |
| Hermes (NousResearch) | 185k | 1-4GB, solo capa entrega notificaciones |
| OpenClaw | — | 1-4GB, solo capa entrega notificaciones |
| InsForge | — | No es monitoring, es backend-as-a-service para AI |
| iii | 17.7k | Orquestación, no alerting |
| MiroFish | — | Simulación social, no monitoring |
| deer-flow | 70.6k | 16GB RAM, deepagents más ligero e integrado |
| agno | 25k+ | AgentOS platform, más pesado que deepagents |
| OpenHands | 50k+ | AI coding agent, no para producción |
| Robyn | 7.2k | Web framework. FastAPI ecosystem data >> velocidad bruta |
| trustgraph | 2.1k | Overkill (Cassandra+Qdrant+Pulsar). graphiti más ligero |
| nn-zero-to-hero | — | Curso educativo, no herramienta |

### ⚠️ Evaluación posterior

| Repo | ★ | Razón |
|------|---|-------|
| floci S3 | — | 13MB vs 150MB SeaweedFS. Test Iceberg compat primero |
| Supabase | 80k+ | Podría reemplazar PG+auth+storage+pgvector pero añade dependencia |
| SQLMesh | 3.1k | Arquitectura superior a dbt pero MetricFlow no production-ready |
| turbovec | 5.3k | 16x compresión vectorial. Evaluar si pgvector RAM es problema |
| OpenSandbox | 2.4k | Sandbox para agentes. Complementario a deepagents |
| graphiti | — | KG temporal para agentes. Evaluar vs mem0 |
| gepa | — | Prompt optimizer. Baja prioridad |
| DeepSeek-OCR | 23.2k | OCR para PDFs ENTSO-E. GPU required |
| Feast | — | Feature store. Pendiente de evaluar |
| Marimo | — | Notebooks reactivos. Pendiente de evaluar |
| Evidently AI | — | Drift monitoring. Pendiente de evaluar |

---

## Deployment Architecture

```
DEV (Mac Studio M4 Max, 64GB, local)
  docker compose -f docker-compose.mac.yml up    # Full stack
  LLM: llama.cpp / vLLM local

CI (GitHub Actions)
  build → ghcr.io/jrodeiro5/solodshouse-*
  test → pytest + ruff + mypy

STAGING (Hetzner CPX21, 4GB, ~€5/mes)
  docker compose -f docker-compose.vps.yml up -d
  LLM: Groq API free / OpenAI / túnel SSH a Mac
  URL: https://solodshouse.example.com
```

### Perfiles Docker Compose (actualizado)

| Perfil | Servicios | RAM |
|--------|----------|:---:|
| core | PG+pgvector+PostGIS, SeaweedFS, Dagster, Hive, Trino | ~2.8GB |
| ml | core + MLflow, BentoML | ~3.3GB |
| agent | ml + deepagents, Open WebUI, LiteLLM, FastAPI proxy, mem0, ToolUniverse+FastMCP, kotaemon, garak, AGT | ~5.4GB |
| observabilidad | Langfuse, Prometheus, Alertmanager | ~0.45GB |
| bi | Evidence.dev, nginx portal, Astro Starlight | ~0.4GB |
| **full (sin LLM)** | core+ml+agent+obs+bi+MongoDB+Adala | **~6.6GB** |
| llm-7b | full + llama.cpp (7B) | **~12.6GB** |
| llm-70b | full + vLLM (70B) | **~56.6GB** |
| +spark | Spark on-demand | **+4GB** |

---

## UCM Module Coverage

| # | Module | How | Status |
|:-:|--------|-----|:------:|
| 1 | Business Intelligence | Evidence.dev + Open WebUI chat | ✅ |
| 2 | SQL | DuckDB + dbt + Trino | ✅ |
| 3 | Tableau | Tableau Desktop connected to DuckDB/PG | ⚠️ |
| 4 | Python Programming | Full stack Python | ✅ |
| 5 | NoSQL Databases | MongoDB + pgvector (vectors) | ✅ |
| 6 | Statistics | Time-series stats, profiling, hypothesis tests | ✅ |
| 7 | Data Mining | Anomaly detection, clustering | ✅ |
| 8 | Machine Learning | XGBoost/LightGBM scikit-learn | ✅ |
| 9 | Data Visualization | Evidence.dev + Open WebUI charts | ✅ |
| 10 | DL/CNN/RNN/LLMs | LSTM forecasting + llama.cpp/vLLM | ✅ |
| 11 | Spark | PySpark on-demand | ✅ |
| 12 | Big Data Tech | Iceberg + Spark + SeaweedFS | ✅ |
| 13 | Model Productivization | MLflow → BentoML → monitoring (Langfuse) | ✅ |
| 14 | Master's Thesis Context | Energy company use case | ⚠️ |
| 15 | Applied Data Science | End-to-end ENTSO-E → lakehouse → ML → agent | ✅ |

---

## Hechos Críticos (no olvidar NUNCA)

- MinIO ARCHIVADO Abr 2026 → SeaweedFS/floci procede
- SoloDShouse = fork de SoloLakehouse v2.5, NO proyecto nuevo
- Dominio = ENTSO-E (energía), NO ECB/DAX (finanzas)
- deepagents NO expone API OpenAI-compatible → necesita FastAPI proxy
- Ollama eliminado → llama.cpp/vLLM o APIs externas vía LiteLLM
- VPS solo 4GB RAM → no LLM local
- Hetzner CPX21 = €4.51/mes + €0.50 IPv4 = ~€5/mes
- ADRs 001-020 ya existen en `docs/decisions/`
- ADR-019 "defer SeaweedFS" → fork es post-v2.5, migración procede
- ADR-002 "no DuckDB" → añadimos como complemento LOCAL (no reemplazo)
- ADR-007 (v3 = K8s) → choca con local-first, necesario ADR nuevo
- ADR-014 (OpenMetadata default) → eliminado, necesario ADR nuevo
- ADR-016 (Spark+dbt-spark) → on-demand profile + dbt-duckdb
- El usuario escribe en ESPAÑOL → responder en español
- Principio rector: local-first, anti-cloud, minimizar recursos
- Observabilidad reducida: Prometheus + Alertmanager + Apprise (no Grafana/Loki en core)
- Superset eliminado: Evidence.dev + Trino SQL cubre BI
- OpenMetadata eliminado: dbt docs + MetricFlow + Adala

## Gaps: Decisions vs Repo Reality

| Decisión | Estado en Repo | Acción necesaria |
|----------|---------------|-----------------|
| SeaweedFS/floci reemplaza MinIO | docker-compose.yml usa MinIO | Nuevo compose, migrar config |
| DuckDB complementa Trino | No existe | Nuevo servicio/config |
| dbt-core + MetricFlow | No existe | Nuevo componente |
| Adala | No existe | Nuevo componente |
| Evidence.dev | No existe, Superset es BI actual | Nuevo servicio |
| Superset eliminado | Parte del default stack | Remover de default |
| OpenMetadata eliminado | Parte del default stack | Remover, ADR nuevo |
| pgvector en PostgreSQL | PG17 sin extension | Añadir extensión |
| PostGIS en PostgreSQL | No existe | Añadir extensión |
| MongoDB | No existe | Nuevo servicio |
| Spark on-demand | No existe | Compose profile |
| deepagents + FastAPI proxy | No existe | Nuevo componente Python |
| Open WebUI | No existe | Nuevo servicio |
| LiteLLM | No existe | Nuevo servicio |
| Langfuse | No existe | Nuevo servicio |
| Prometheus + Alertmanager | No existe | Nuevo compose |
| llama.cpp / vLLM | No existe | Compose profile |
| kotaemon | No existe | Nuevo servicio |
| garak | No existe | CLI audit |
| AGT (Microsoft) | No existe | Lib Python |
| FastMCP | No existe | Lib Python |
| Adala | No existe | Lib Python |
| Apprise (en deepagents) | No existe | Lib Python |
| ENTSO-E collectors | Solo ECB/DAX | Nuevos collectors |
| Portal nginx | No existe | Nuevo servicio |
| Astro Starlight docs | No existe | Nuevo sitio |
| ADR-007 (K8s v3) | Existe | ADR nuevo: local-first |
| ADR-002 (no DuckDB) | Existe | ADR nuevo: DuckDB complemento |
| ADR-014 (OpenMetadata) | Existe | ADR nuevo: eliminado |
| ADR-016 (Spark+dbt-spark) | Existe | ADR nuevo: on-demand + dbt-duckdb |
| Domain pivot (ENTSO-E) | Código = ECB/DAX | Nuevos collectors, schemas, transformations |