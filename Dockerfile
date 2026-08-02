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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Render requires host 0.0.0.0
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]