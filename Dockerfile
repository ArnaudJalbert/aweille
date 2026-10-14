FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    AWEILLE_DB_PATH=/data/aweille.sqlite3

COPY pyproject.toml uv.lock .python-version ./
COPY packages/aweille/pyproject.toml packages/aweille/
COPY packages/aweille/src packages/aweille/src
RUN uv sync --locked --no-dev --no-editable --package aweille --no-cache

USER 1000:1000
EXPOSE 8000
CMD ["uvicorn", "aweille.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
