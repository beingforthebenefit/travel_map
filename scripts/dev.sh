#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit it to add your API keys."
fi

docker compose up --build "$@"
