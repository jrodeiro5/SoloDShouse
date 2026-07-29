---
title: Agent Proxy
summary: FastAPI proxy that translates OpenAI-compatible API requests into deepagents (LangGraph) calls, routing LLM requests through LiteLLM gateway.
topics: [architecture, agents, api, proxy]
---

# Agent Proxy

The Agent Proxy is a FastAPI application that translates OpenAI-compatible API
requests into deepagents (LangGraph) calls, routing LLM requests through the
LiteLLM gateway. This proxy enables standard OpenAI SDK clients to interact
with SoloDShouse's agent infrastructure.

The proxy currently serves as a minimal stub that demonstrates the request
translation pattern, with the actual LangGraph integration to be implemented.

## Architecture

The proxy sits between OpenAI-compatible API clients and the deepagents
infrastructure:

```
OpenAI SDK Client → FastAPI Proxy → LiteLLM Gateway → deepagents (LangGraph)
```

The proxy handles:
- Authentication via LiteLLM API keys
- Request parsing and validation
- Response formatting to OpenAI-compatible format
- Health monitoring

## API Endpoints

### Health Check

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Returns service status for monitoring and load balancer health checks.

### Chat Completions

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    _check_auth(request)
    body = await request.json()
    return JSONResponse(
        content={
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "deepagents"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "[deepagents stub — implement LangGraph integration]",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    )
```

The `/v1/chat/completions` endpoint:
1. Validates authentication
2. Parses the request body
3. Returns a formatted OpenAI-compatible response
4. Currently returns a stub message indicating LangGraph integration is pending

### Model Listing

```python
@app.get("/v1/models")
async def list_models() -> JSONResponse:
    return JSONResponse(
        content={
            "object": "list",
            "data": [{"id": "deepagents", "object": "model", "created": int(time.time())}],
        }
    )
```

Returns the available models (currently only `deepagents`).

## Authentication

The proxy validates requests using LiteLLM API keys:

```python
def _check_auth(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    expected = os.environ.get("LITELLM_API_KEY", "")
    if not auth or (expected and auth != f"Bearer {expected}"):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
```

Authentication requires:
- `Authorization: Bearer {LITELLM_API_KEY}` header
- `LITELLM_API_KEY` environment variable must be set

If no API key is configured, authentication is bypassed (development mode).

## Configuration

The proxy reads configuration from environment variables:

- `LITELLM_BASE_URL` — LiteLLM gateway endpoint (default: `http://litellm:4000`)
- `LITELLM_API_KEY` — API key for authentication

## Error Handling

The proxy handles several error scenarios:

- **Missing API key**: Authentication bypassed in development mode
- **Invalid API key**: Returns 401 Unauthorized
- **Malformed requests**: FastAPI returns 422 Unprocessable Entity
- **Internal errors**: FastAPI returns 500 Internal Server Error

## Integration with DeepAgents

The proxy is designed to integrate with deepagents, a LangGraph-based agent
harness. The current implementation returns a stub message, but the intended
flow is:

1. Parse the chat completion request
2. Extract conversation history and user messages
3. Route through deepagents LangGraph workflow
4. Format the response as OpenAI-compatible chat completion
5. Return to the client

This integration will enable natural language queries over Gold layer data
via MCP tools, as specified in SDS-024.

## See Also

- [Collector Pattern](../concepts/collector-pattern.md) — data ingestion
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Docker Compose Profiles](docker-compose-profiles.md) — service deployment
