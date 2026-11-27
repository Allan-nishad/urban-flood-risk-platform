FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    FLOODRISK_DB_PATH=/app/data/state/floodrisk_v8.db \
    FLOODRISK_BACKUP_DIR=/app/data/state/backups \
    FLOODRISK_MODEL_DIR=/app/models/v8_experimental \
    FLOODRISK_REFRESH_INTERVAL_S=1800

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY configs/ ./configs/
COPY models/ ./models/
COPY data/processed/ ./data/processed/
COPY reports/ ./reports/

RUN mkdir -p /app/data/state/backups && \
    adduser --disabled-password --gecos "" floodrisk && \
    chown -R floodrisk:floodrisk /app

USER floodrisk

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os, urllib.request, sys; p = os.environ.get('PORT', '8501'); r = urllib.request.urlopen(f'http://127.0.0.1:{p}/api/ready', timeout=4); sys.exit(0 if r.status == 200 else 1)"

CMD ["sh", "-c", "python -m floodrisk.dashboard.server --host 0.0.0.0 --port ${PORT:-8501}"]
