# syntax=docker/dockerfile:1
FROM --platform=$TARGETPLATFORM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/hf_cache \
    TRANSFORMERS_CACHE=/hf_cache

WORKDIR /app
RUN mkdir -p $HF_HOME && chmod 777 $HF_HOME

# Dependências de sistema para torch CPU
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 bash curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Instala torch CPU na versão solicitada e depois as demais deps
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8001 8002

# Basic healthcheck hitting both services (requires curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 CMD bash -lc "curl -fsS http://127.0.0.1:8001/ >/dev/null && curl -fsS http://127.0.0.1:8002/healthz >/dev/null || exit 1"

CMD ["./start.sh"]
