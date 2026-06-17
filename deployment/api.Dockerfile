FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api ./api
COPY common ./common

RUN pip install --no-cache-dir ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

