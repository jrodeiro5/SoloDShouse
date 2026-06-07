# SDS-027: FastMCP como framework MCP

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita una forma estandar de exponer herramientas del lakehouse (query Trino, leer tablas Iceberg, ejecutar modelos dbt) a los agentes de IA. MCP (Model Context Protocol) es el estandar emergente para integracion de herramientas con LLMs.

FastMCP (de PrefectHQ) proporciona: definiciones declarativas de herramientas, validacion Pydantic, y generacion de schemas compatibles con OpenAI.

## Decision

FastMCP se adopta como el framework MCP para la integracion de herramientas del lakehouse.

FastMCP es una libreria Python (0 MB de overhead de container). Expone: herramienta de query Trino, herramienta de scan Iceberg, herramienta de ejecucion dbt, y herramienta de lookup de experimentos MLflow. Se integra con el sistema de tool calling de deepagents (SDS-024).

## Rationale

- **Estandar emergente:** MCP es el protocolo que Anthropic y otros actores estan promoviendo para que los LLMs descubran y usen herramientas externas. Adoptarlo ahora previene reescritura futura.
- **Declarative:** Las herramientas se definen como funciones Python con docstrings y tipos Pydantic. FastMCP genera automaticamente el schema JSON que los LLMs necesitan para entender que hace cada herramienta.
- **0 overhead:** Es una libreria Python. No requiere container adicional ni servicio persistente. Se importa en el codigo del agente.
- **Integracion con deepagents:** deepagents soporta tool calling via funciones Python. FastMCP proporciona la capa de estandarizacion MCP sobre esas funciones.

## Consequences

- **Positivas:** Los agentes descubren herramientas del lakehouse via protocolo estandar. La validacion Pydantic previene errores de tipo en los parametros de las herramientas. Los schemas son compatibles con cualquier cliente MCP.
- **Negativas:** MCP es un estandar joven y en evolucion. La API puede cambiar. FastMCP es un proyecto relativamente nuevo (PrefectHQ) con menos madurez que frameworks como FastAPI.

## Alternatives Considered

- **Funciones Python directas:** Rechazado porque, aunque funciona con deepagents, no proporciona estandarizacion. Cada herramienta tendria un formato ad-hoc y no seria reusable por otros agentes o clientes.
- **OpenAPI + FastAPI:** Rechazado porque, aunque estandar, es mas orientado a APIs REST que a la integracion LLM-tool. MCP esta disenado especificamente para el contexto de LLMs.
- **LangChain Tools:** Rechazado porque introduce dependencia de LangChain, que se ha evitado deliberadamente en todo el stack (SDS-025).
