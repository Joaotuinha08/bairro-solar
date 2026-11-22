FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src:/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pytest.ini ARCHITECTURE.md ./
COPY src ./src
COPY simulador ./simulador
COPY evals ./evals
COPY tests ./tests

RUN mkdir -p /app/dados
