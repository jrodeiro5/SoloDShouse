"""FastAPI proxy — OpenAI-compatible API → deepagents (SDS-024).

Translates /v1/chat/completions requests into deepagents (LangGraph) calls,
routing LLM requests through LiteLLM gateway.

Minimal stub — extend with real deepagents integration.
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="SoloDShouse Agent Proxy", version="0.1.0")

LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://litellm:4000")
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
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


@app.get("/v1/models")
async def list_models() -> JSONResponse:
    return JSONResponse(
        content={
            "object": "list",
            "data": [{"id": "deepagents", "object": "model", "created": int(time.time())}],
        }
    )
