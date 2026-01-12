FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    httpx==0.25.2 \
    websockets==12.0 \
    PyJWT==2.8.0 \
    python-multipart==0.0.6 \
    python-docx==1.1.0 \
    PyPDF2==3.0.1 \
    striprtf==0.0.26 \
    pandas==2.1.3 \
    openpyxl==3.1.2 \
    xlrd==2.0.1 \
    bcrypt==4.1.1 \
    ollama>=0.4.0 \
    aiohttp>=3.9.0

# Copy all Python modules
COPY config.py .
COPY auth.py .
COPY models.py .
COPY documents.py .
COPY ai_providers.py .
COPY ollama_setup.py .
COPY server.py .
COPY static/ ./static/

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8765

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
