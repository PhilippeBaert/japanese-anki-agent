# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for layer caching
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./

# Set the API URL for production build (internal container communication)
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

RUN npm run build

# ============================================
# Stage 2: Production Runtime
# ============================================
FROM python:3.11-slim AS production

# Install Node.js for Next.js runtime and supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Backend Setup ----
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/

# ---- Frontend Setup ----
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/next.config.js ./frontend/

# ---- Config Setup ----
# Create config directory - will be mounted as volume
RUN mkdir -p /app/config
COPY config/anki_config.json /app/config/anki_config.json.default

# ---- Supervisor Configuration ----
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ---- Startup Script ----
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONFIG_PATH=/app/config/anki_config.json \
    NEXT_PUBLIC_API_URL=http://localhost:8000

# Expose the frontend port (Unraid will map this)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
