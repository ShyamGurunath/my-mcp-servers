# -------- Stage 1: Builder with uv for dependency resolution --------
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.14 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked

COPY ./src .

EXPOSE 8050

CMD ["uv", "run", "memory_retainer/server.py"]
