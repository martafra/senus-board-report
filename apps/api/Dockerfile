FROM python:3.11-slim

WORKDIR /app

# Build context is the repo root (see docker-compose.yml / render deploy), so both apps/api and
# data/ can be copied into the same image: production has no bind mount to supply data/ the way
# local docker-compose does, so the real extracted facts need to be baked in.
COPY apps/api /app
RUN pip install --no-cache-dir -e .

COPY data /data
ENV DATA_DIR=/data

EXPOSE 8000

# Migrate, seed the demo user and load the real data on every boot. All three are additive/
# idempotent by design (see scripts/ingest.py and scripts/seed_user.py), so re-running them on an
# already-populated database is a safe no-op, not a risk. This is what makes the container
# self-seeding: a platform with no shell access (e.g. Render's free tier) still ends up with a
# fully populated database after the first deploy, with no manual step required.
CMD alembic upgrade head && \
    python scripts/seed_user.py && \
    python scripts/ingest.py load /data/extracted/senus_information_document.json && \
    python scripts/ingest.py load /data/extracted/senus_hy2026_results.json && \
    python scripts/ingest.py load /data/extracted/senus_adf_audited_fy2025.json && \
    python scripts/ingest.py model-monthly && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
