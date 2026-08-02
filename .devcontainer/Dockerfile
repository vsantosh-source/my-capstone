# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install Streamlit and Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /workspace