# ----------------------------
# Stage 1: builder
# ----------------------------
# syntax=docker/dockerfile:1

FROM python:3.10-slim

# --- Minimal runtime & faster installs ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Optional: if you use GCS in prod, keep this runtime lib small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker layer cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (FastAPI app lives under app/)
COPY app /app/app
# (Optional) copy tests into image if you’ll run them inside the container
COPY tests /app/tests

# Security: run as non-root
RUN useradd -m appuser
USER appuser

# Cloud Run listens on 8080; expose for local clarity
EXPOSE 8080

# Healthcheck (optional; Cloud Run has its own, but this helps locally)
# HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1

# Start FastAPI with uvicorn, hardcoded to 8080 as requested
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
