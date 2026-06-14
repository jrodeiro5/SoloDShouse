FROM python:3.12-slim

RUN pip install fastapi uvicorn

COPY agents/ /app/agents/
WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "agents.deepagents_proxy:app", "--host", "0.0.0.0", "--port", "8000"]
