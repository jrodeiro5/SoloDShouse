# SDS-023: Ollama eliminado — llama.cpp/vLLM + LiteLLM

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloLakehouse v2.5 no tenia componente de inferencia LLM. SoloDShouse anade un LLM local para flujos de trabajo de agentes. Ollama es la opcion popular (1M+ stars en GitHub) pero introduce overhead innecesario: un daemon siempre activo, ~300MB de RAM base mas el modelo cargado, y gestion de modelos limitada.

Para un stack que prioriza minimizar RAM y coste, un daemon siempre activo es una carga inaceptable. Se necesita un modelo de inferencia on-demand que consuma 0 RAM cuando no se use.

## Decision

Se utiliza llama.cpp para inferencia LLM local (modelos 7B, on-demand) y vLLM para modelos grandes (70B, cuando la RAM lo permita). LiteLLM actua como gateway unificado, enrutando peticiones a llama.cpp/vLLM localmente o a la API de Groq (free tier) en el VPS.

Ollama no se incluye en ninguna modalidad. llama.cpp se ejecuta on-demand (0 RAM cuando esta inactivo). vLLM esta disponible como perfil de Docker Compose. LiteLLM (~150MB) normaliza la API al formato compatible con OpenAI.

## Rationale

- **0 RAM idle:** llama.cpp se ejecuta como proceso efimero. Cuando termina la inferencia, libera toda la RAM. Esto es critico en un entorno con 4GB de RAM (Hetzner CPX21).
- **Control granular:** llama.cpp permite especificar exactamente cuantas capas del modelo cargar en GPU/CPU, quantizacion, y parametros de inferencia. Ollama oculta estos detalles.
- **Gateway unificado:** LiteLLM proporciona una API OpenAI-compatible que abstrae si el backend es llama.cpp local, vLLM local, o Groq API remota. Los agentes usan un unico cliente OpenAI.
- **vLLM para escalado:** Cuando el Mac Studio M4 Max (64GB) ejecuta el stack localmente, vLLM puede servir modelos 70B con throughput optimo. En el VPS, vLLM no se activa.

## Consequences

- **Positivas:** Eliminacion de ~300MB de daemon siempre activo. Inferencia on-demand libera RAM inmediatamente. LiteLLM permite cambiar entre local y remoto (Groq) sin modificar codigo de agentes.
- **Negativas:** llama.cpp requiere descargar modelos manualmente (GGUF). No hay gestion automatica de modelos como en Ollama. vLLM requiere GPU o mucha RAM para modelos grandes.

## Alternatives Considered

- **Ollama (status quo popular):** Rechazado por daemon siempre activo, overhead de RAM, y falta de control granular sobre quantizacion y offload.
- **Text Generation Inference (HuggingFace):** Rechazado porque, aunque eficiente, esta optimizado para servidores GPU y su overhead de container es mayor que llama.cpp para uso esporadico.
- **Solo API remota (Groq/OpenRouter):** Rechazado porque viola el principio local-first. Se usa Groq como fallback en VPS, no como opcion principal.
