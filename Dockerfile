FROM python:3.12-slim

# Install ffmpeg and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/
COPY run.py .
COPY README.md .

# Create downloads folder
RUN mkdir -p /app/downloads && chmod 777 /app/downloads

# Port configuration (supports HuggingFace Spaces 7860, Render $PORT, or default 5050)
ENV PORT=5050
EXPOSE 5050 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5050}"]
