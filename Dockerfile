# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 bot && \
    mkdir -p /app/logs /app/data && \
    chown -R bot:bot /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set ownership
RUN chown -R bot:bot /app

# Switch to non-root user
USER bot

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Set labels for Pterodactyl
LABEL maintainer="Pterodactyl Discord Bot Team" \
      version="1.0.0" \
      description="Advanced Discord bot for Pterodactyl panel management" \
      org.opencontainers.image.source="https://github.com/your-repo/ptero-discord-bot"

# Run the application
CMD ["python", "bot.py"]
