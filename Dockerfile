# Root Dockerfile for Render
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (optional, needed for some data libraries)
RUN apt-get update && \
    apt-get install -y \
        libgl1 \
        libglx-mesa0 \
        libsm6 \
        libxrender1 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . .

EXPOSE 8501

# Render requires host 0.0.0.0
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501"]
