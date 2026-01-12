# =============================================================================
# Nora AI Gateway - Linux Private Server Edition
# Optimized for Linux with health checks and minimal footprint
# =============================================================================
FROM python:3.11-slim-bookworm

LABEL maintainer="Nora AI"
LABEL description="Nora AI Gateway - Linux Private Server"

WORKDIR /app

# Install system dependencies for document processing and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    httpx==0.27.0 \
    websockets==13.0 \
    PyJWT==2.9.0 \
    python-multipart==0.0.9 \
    python-docx==1.1.2 \
    PyPDF2==3.0.1 \
    striprtf==0.0.26 \
    pandas==2.2.0 \
    openpyxl==3.1.5 \
    xlrd==2.0.1 \
    bcrypt==4.2.0 \
    ollama>=0.4.0 \
    aiohttp>=3.10.0 \
    sse-starlette>=2.0.0

# Copy all Python modules
COPY config.py .
COPY auth.py .
COPY models.py .
COPY documents.py .
COPY ai_providers.py .
COPY ollama_setup.py .
COPY server.py .
COPY static/ ./static/

# Create directories
RUN mkdir -p /app/uploads /app/company_info

# Non-root user for security
RUN useradd -m -u 1000 nora && \
    chown -R nora:nora /app
USER nora

EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
