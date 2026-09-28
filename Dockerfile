FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app backend/app
COPY backend/scripts backend/scripts
COPY config config
COPY data/sample data/sample
COPY data/zones.geojson data/zones.geojson

# Train the bundled, explicitly synthetic baseline at image build time so the
# service can become healthy without retraining on each restart.
RUN python -c "from app.services.runtime import get_runtime; get_runtime()"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
