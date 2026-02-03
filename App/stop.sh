#!/bin/bash
# SOUNDTRACKER - Script de parada
# Ejecuta: ./stop.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Detectar comando docker compose
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

echo "Deteniendo SOUNDTRACKER..."
$COMPOSE down

echo "✓ Servicios detenidos"
