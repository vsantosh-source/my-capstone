# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install Streamlit and Python dependencies
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

WORKDIR /workspace