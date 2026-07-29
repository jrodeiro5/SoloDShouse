---
title: Docker Compose Profiles
summary: Docker Compose profiles that define service groups with RAM targets, enabling selective service activation for different deployment scenarios.
topics: [architecture, deployment, docker, infrastructure]
---

# Docker Compose Profiles

Docker Compose profiles define service groups with RAM targets, enabling
selective service activation for different deployment scenarios. This approach
allows running minimal core stacks for development while supporting full
production deployments with all services.

The profile system is designed around resource constraints, with each profile
representing a specific workload type and RAM budget.

## Profile Definitions

### Core Profile

The `core` profile runs the foundational services:

```yaml
services:
  postgres:
    image: postgres:17
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}

  seaweedfs:
    image: christofu/seaweedfs:latest
    ports:
      - "8333:8333"
    volumes:
      - seaweedfs_data:/data

  hive-metastore:
    image: apache/hive:3.1.3
    ports:
      - "9083:9083"

  trino:
    image: trinodb/trino:latest
    ports:
      - "8080:8080"

  dagster:
    build: ./dagster
    ports:
      - "3000:3000"
    volumes:
      - dagster_data:/app/data
```

**RAM target**: ~2.8 GB
**Services**: PostgreSQL 17, SeaweedFS, Hive Metastore, Trino, Dagster

### ML Profile

The `ml` profile extends core with machine learning services:

```yaml
mlflow:
  image: mlflow/mlflow:latest
  ports:
    - "5000:5000"

bentoml:
  image: bentoml/bentoml:latest
  ports:
    - "5100:5100"
```

**RAM target**: ~3.3 GB (core + MLflow, BentoML)

### Agent Profile

The `agent` profile adds AI/agent services:

```yaml
deepagents:
  build: ./agents
  ports:
    - "8000:8000"

open-webui:
  image: ghcr.io/open-webui/open-webui:latest
  ports:
    - "3001:8080"

litellm:
  image: ghcr.io/berriai/litellm:latest
  ports:
    - "4000:4000"

fastapi-proxy:
  build: ./agents
  ports:
    - "8001:8001"

mem0:
  image: mem0ai/mem0:latest
  ports:
    - "6000:6000"

kotaemon:
  build: ./kotaemon
  ports:
    - "7000:7000"

tooluniverse:
  build: ./agents/tools
  ports:
    - "8002:8002"

garak:
  image: garak-ai/garak:latest
  ports:
    - "9000:9000"

agt:
  build: ./agt
  ports:
    - "9001:9001"
```

**RAM target**: ~5.4 GB (ml + deepagents, Open WebUI, LiteLLM, FastAPI proxy, mem0, kotaemon, ToolUniverse, garak, AGT)

### Observability Profile

The `observability` profile provides monitoring and alerting:

```yaml
langfuse:
  image: langfuse/langfuse:latest
  ports:
    - "3030:3000"

prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"

alertmanager:
  image: prom/alertmanager:latest
  ports:
    - "9093:9093"
```

**RAM target**: ~0.45 GB (Langfuse, Prometheus, Alertmanager)

### BI Profile

The `bi` profile enables business intelligence:

```yaml
evidence:
  build: ./evidence
  ports:
    - "3002:3000"

nginx-portal:
  image: nginx:latest
  ports:
    - "80:80"

astro-starlight:
  build: ./docs
  ports:
    - "4321:4321"
```

**RAM target**: ~0.4 GB (Evidence.dev, nginx portal, Astro Starlight)

### Full Profile

The `full` profile combines all services:

```bash
docker compose --profile full up -d
```

**RAM target**: ~6.6 GB (core + ml + agent + observability + bi + MongoDB + Adala)

### LLM Profiles

The LLM profiles add local inference capabilities:

#### LLM 7B Profile

```bash
docker compose --profile full --profile llm-7b up -d
```

**RAM target**: ~12.6 GB (full + llama.cpp 7B)

#### LLM 70B Profile

```bash
docker compose --profile full --profile llm-70b up -d
```

**RAM target**: ~56.6 GB (full + vLLM 70B)

### Spark Profile

The `+spark` profile adds on-demand Spark processing:

```bash
docker compose --profile full --profile spark up -d
```

**RAM overhead**: +4 GB

## Make Commands

The Makefile provides high-level commands for managing the stack:

```bash
make up              # Start core stack + init SeaweedFS buckets + Iceberg namespaces
make down            # Stop (data preserved under docker/data/)
make pipeline        # Run Dagster full_pipeline_job
make dagster-ui      # Open Dagster UI (http://localhost:3000)
make verify          # Health-check all services
make test            # Unit tests (pytest, no Docker needed)
make lint            # ruff
make typecheck       # mypy on ingestion/, transformations/, ml/, scripts/, dagster/
make clean           # Stop + delete docker/data/ + purge volumes
```

### Startup Sequence

The `make up` command executes the following sequence:

1. **Prepare data directories**: Creates bind mount directories under `docker/data/`
2. **Start PostgreSQL + SeaweedFS**: Initializes database and object storage
3. **Wait for Postgres**: Health-check loop (90 seconds)
4. **Bootstrap database**: Creates additional databases (MLflow, etc.)
5. **Build and start all services**: `docker compose up -d --build`
6. **Wait for all services**: Health-check loop
7. **Initialize SeaweedFS**: Creates buckets (solodshouse-data, etc.)
8. **Initialize Iceberg namespaces**: Creates bronze, silver, gold namespaces

```bash
prepare-data-dirs:
	@sh scripts/prepare-docker-data-dirs.sh

up: prepare-data-dirs
	$(DOCKER_COMPOSE) $(COMPOSE_STACK) up -d postgres seaweedfs
	$(MAKE) wait-postgres-ready
	$(MAKE) bootstrap-db
	$(DOCKER_COMPOSE) $(COMPOSE_STACK) up -d --build
	$(MAKE) wait
	sh scripts/init-seaweedfs.sh
	$(MAKE) init-iceberg
	@echo ""
	@echo "SoloDShouse is ready."
	@echo "  SeaweedFS S3:   http://localhost:8333"
	@echo "  Trino UI:       http://localhost:8080"
	@echo "  MLflow UI:      http://localhost:5000"
	@echo "  Dagster UI:     http://localhost:3000"
```

## Data Persistence

All runtime state persists under `docker/data/` as bind mounts:

- `docker/data/postgres/` — PostgreSQL data
- `docker/data/seaweedfs/` — SeaweedFS object storage
- `docker/data/dagster/` — Dagster state
- `docker/data/om-mysql/` — OpenMetadata MySQL data
- `docker/data/om-elasticsearch/` — OpenMetadata Elasticsearch data

This ensures data survives container restarts and enables `make clean` to
reset the stack without data loss.

## Service Endpoints

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | `postgresql://user:pass@localhost:5432/db` |
| SeaweedFS S3 | 8333 | `http://localhost:8333` |
| Hive Metastore | 9083 | `thrift://localhost:9083` |
| Trino | 8080 | `http://localhost:8080` |
| MLflow | 5000 | `http://localhost:5000` |
| Dagster | 3000 | `http://localhost:3000` |
| Open WebUI | 3001 | `http://localhost:3001` |
| LiteLLM | 4000 | `http://localhost:4000` |
| Langfuse | 3030 | `http://localhost:3030` |
| Prometheus | 9090 | `http://localhost:9090` |

## Environment Variables

Key environment variables loaded from `.env`:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — PostgreSQL credentials
- `OBJECT_STORE_ENDPOINT` — SeaweedFS S3 endpoint (default: `http://localhost:8333`)
- `OBJECT_STORE_ACCESS_KEY`, `OBJECT_STORE_SECRET_KEY` — S3 credentials
- `HIVE_METASTORE_URI` — Hive Metastore endpoint (default: `thrift://localhost:9083`)
- `WAREHOUSE_URI` — Iceberg warehouse URI (default: `s3a://solodshouse-data/warehouse/`)
- `SOLODSHOUSE_VAULT_KEY` — Fernet encryption key for connection secrets

## Hardware Targets

| Environment | Machine | RAM | Cost |
|-------------|---------|:---:|:----:|
| DEV | Mac Studio M4 Max | 64 GB | owned |

**Docker runtime (macOS):** OrbStack — replaces Docker Desktop. Faster on Apple Silicon, lower RAM overhead, native `docker` and `docker compose` CLI. Install: `brew install orbstack`.

## See Also

- [Ingestion Pipeline](ingestion-pipeline.md) — data flow
- [Dagster Orchestration](dagster-orchestration.md) — pipeline orchestration
- [Environment Variables](../reference/environment-variables.md) — all env vars
