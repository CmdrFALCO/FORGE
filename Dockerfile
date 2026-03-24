# Stage 1: base — core FORGE install without heavy ML deps
FROM python:3.11-slim AS base

WORKDIR /app

# System deps for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy only what's needed for pip install
COPY pyproject.toml README.md ./
COPY forge/ forge/

# Install FORGE in editable mode — core + gui deps (no torch, no scipy, no pybamm)
RUN pip install --no-cache-dir -e ".[gui]"

# CPU-only torch for surrogate inference (~170MB) + scipy for batch/LHS
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir scipy

# Stage 2: app — final image
FROM base AS app

WORKDIR /app

# Streamlit config — disable telemetry, set headless
RUN mkdir -p /root/.streamlit && \
    echo '[server]\nheadless = true\nenableCORS = false\n\n[browser]\ngatherUsageStats = false' > /root/.streamlit/config.toml

EXPOSE 8501 8000

CMD ["bash"]
