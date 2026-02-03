#!/bin/bash
# SOUNDTRACKER - Script de inicio rápido
# Ejecuta: ./start.sh

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║         🎬 SOUNDTRACKER 🎵            ║"
echo "  ║    Film Composers Encyclopedia        ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Detectar comando docker compose
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo -e "${YELLOW}Error: Docker Compose no está instalado${NC}"
    exit 1
fi

# Función para abrir navegador
open_browser() {
    local url="$1"
    echo -e "${GREEN}Abriendo navegador...${NC}"

    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" 2>/dev/null &
    elif command -v open >/dev/null 2>&1; then
        open "$url" &
    elif command -v start >/dev/null 2>&1; then
        start "$url" &
    elif [ -n "$BROWSER" ]; then
        "$BROWSER" "$url" &
    else
        echo -e "${YELLOW}No se pudo abrir el navegador automáticamente${NC}"
        echo -e "Abre manualmente: ${CYAN}$url${NC}"
    fi
}

# Verificar si ya está corriendo
if $COMPOSE ps 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✓ Servicios ya están corriendo${NC}"
    echo ""
    open_browser "http://localhost:3000"
    echo ""
    echo -e "${GREEN}Frontend:${NC}  http://localhost:3000"
    echo -e "${GREEN}API:${NC}       http://localhost:8000"
    echo -e "${GREEN}API Docs:${NC}  http://localhost:8000/docs"
    exit 0
fi

# Construir si es necesario
echo -e "${GREEN}Construyendo imágenes Docker...${NC}"
$COMPOSE build --quiet

# Iniciar servicios
echo -e "${GREEN}Iniciando servicios...${NC}"
$COMPOSE up -d

# Esperar a que los servicios estén listos
echo -e "${GREEN}Esperando a que los servicios estén listos...${NC}"
echo -n "  Backend: "
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo -n "  Frontend: "
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✓ SOUNDTRACKER está listo${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:3000"
echo -e "  ${CYAN}API:${NC}       http://localhost:8000"
echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8000/docs"
echo ""

# Abrir navegador
open_browser "http://localhost:3000"

echo -e "${YELLOW}Para detener: ${NC}$COMPOSE down"
echo ""
