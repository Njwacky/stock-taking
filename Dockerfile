# Multi-stage build for Django Stock Management System
# Stage 1: Build stage
FROM mcr.microsoft.com/devcontainers/python:3.9 as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 2: Production stage
FROM mcr.microsoft.com/devcontainers/python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies needed for runtime
RUN apt-get update && apt-get install -y \
    libpq5 \
    libffi-dev \
    libssl-dev \
    zlib1g \
    libjpeg62-turbo \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directories
RUN mkdir -p /app /app/static /app/media /app/logs

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Copy entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN chown -R appuser:appuser /app

# Create static files directory and set permissions
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app/staticfiles
RUN mkdir -p /app/mediafiles && chown -R appuser:appuser /app/mediafiles

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check (removed - will be handled by docker-compose)
# Note: collectstatic will be run in entrypoint to ensure proper permissions

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--reload", "app_conf.wsgi:application"]
