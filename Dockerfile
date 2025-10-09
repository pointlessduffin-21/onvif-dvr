FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (ffmpeg for stream conversion)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production \
    DATABASE_PATH=/data/onvif_viewer.db

# Precompile bytecode to verify syntax at build time
RUN python -m compileall .

EXPOSE 8821

CMD ["gunicorn", "--bind", "0.0.0.0:8821", "app:app"]
