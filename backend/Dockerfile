# ────────────────────────────────────────────────
# Stage 1 – base: shared system deps
# ────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# GDAL/GEOS for rasterio + GeoAlchemy2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency manifest
COPY pyproject.toml .

# ────────────────────────────────────────────────
# Stage 2 – dev: hot-reload, dev deps included
# ────────────────────────────────────────────────
FROM base AS dev

# Install all deps including dev extras
RUN uv pip install --system -e ".[dev]"

# App source is mounted as a volume at runtime — do not COPY here
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ────────────────────────────────────────────────
# Stage 3 – prod: no dev deps, source baked in
# ────────────────────────────────────────────────
FROM base AS prod

# Install production deps only
RUN uv pip install --system -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
