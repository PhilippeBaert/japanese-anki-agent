#!/bin/bash
set -e

# Copy default config if not exists (for first-run)
if [ ! -f /app/config/anki_config.json ]; then
    echo "Initializing default configuration..."
    cp /app/config/anki_config.json.default /app/config/anki_config.json
fi

# Create log directory
mkdir -p /var/log/supervisor

# Execute the main command
exec "$@"
