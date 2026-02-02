# =============================================================================
# Palette AI Ops Toolkit - Dockerfile
# =============================================================================
# Multi-stage build for optimized production image
# =============================================================================

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY palette-mcp/mcp_server/ ./mcp_server/
COPY palette-mcp/guardrails/ ./guardrails/
COPY mcp_chat.py ./

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PALETTE_API_ENDPOINT=https://api.spectrocloud.com \
    LLM_PROVIDER=local \
    ENABLE_GUARDRAILS=true \
    LOG_LEVEL=INFO

# Expose ports
EXPOSE 8080 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Run the MCP server
CMD ["python", "-m", "mcp_server.palette_mcp"]

# =============================================================================
# Labels
# =============================================================================
LABEL org.opencontainers.image.title="Palette AI Ops Toolkit" \
      org.opencontainers.image.description="AI-powered operations toolkit for Spectro Cloud Palette" \
      org.opencontainers.image.vendor="Utkarsha" \
      org.opencontainers.image.source="https://github.com/utkarsha/palette-ai-ops-toolkit"
