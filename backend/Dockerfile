# building stage
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for building wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates  && \
    rm -rf /var/lib/apt/lists/*

# install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual env
RUN uv sync --frozen --no-install-project

# runtime stage
FROM python:3.11-slim

WORKDIR /app

# Minimal runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Activate venv
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
