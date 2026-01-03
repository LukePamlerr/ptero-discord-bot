# ===========================================
# Pterodactyl Discord Bot - Dockerfile
# ===========================================

# Use Python 3.11 slim image for smaller size and better security
FROM python:3.11-slim

# Set environment variables for better performance and security
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies with security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        postgresql-client \
        curl \
        git \
        ca-certificates \
        tzdata \
        && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r bot && \
    useradd -r -g bot -m -u 1000 bot && \
    mkdir -p /app/logs /app/data /app/backups /app/temp && \
    chown -R bot:bot /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copy application files with proper ownership
COPY --chown=bot:bot . .

# Set permissions for security
RUN chmod +x /app/scripts/*.py 2>/dev/null || true && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs /app/data /app/backups /app/temp

# Switch to non-root user
USER bot

# Create additional directories as non-root user
RUN mkdir -p /app/logs /app/data /app/backups /app/temp

# Health check endpoint with improved reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port for web interface
EXPOSE 8080

# Set labels for better container management
LABEL maintainer="Pterodactyl Discord Bot Team" \
      version="1.0.0" \
      description="Advanced Discord bot for Pterodactyl panel management with monitoring, analytics, and automation" \
      org.opencontainers.image.source="https://github.com/your-repo/ptero-discord-bot" \
      org.opencontainers.image.documentation="https://github.com/your-repo/ptero-discord-bot/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"

# Add metadata for Pterodactyl compatibility
LABEL pterodactyl.image.name="ptero-discord-bot" \
      pterodactyl.image.version="1.0.0" \
      pterodactyl.image.description="Pterodactyl Discord Bot Container" \
      pterodactyl.image.url="https://github.com/your-repo/ptero-discord-bot"

# Default command with health check
CMD ["python", "bot.py"]
