# SOUNDTRACKER - Guía de Despliegue

**Versión**: 3.0 | **Actualizado**: 2026-02-03

## Requisitos

- Docker 20.10+ y Docker Compose v2
- 2GB RAM mínimo
- 5GB espacio en disco (incluye base de datos y assets)

## Despliegue Rápido

```bash
# Clonar repositorio
git clone <repo-url>
cd App

# Iniciar aplicación (build + up + abre navegador)
./start.sh

# Detener aplicación
./stop.sh
```

El script automáticamente:
1. Construye las imágenes Docker
2. Inicia los servicios
3. Verifica que estén saludables

## Despliegue Manual

### 1. Construir imágenes

```bash
docker compose build
```

### 2. Iniciar servicios

```bash
docker compose up -d
```

### 3. Verificar estado

```bash
# Ver estado de contenedores
docker compose ps

# Ver logs
docker compose logs -f

# Health check backend
curl http://localhost:8000/health

# Health check frontend
curl http://localhost:3000
```

## URLs de Acceso

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Aplicación web |
| Backend API | http://localhost:8000 | API REST |
| API Docs | http://localhost:8000/docs | Documentación OpenAPI |
| ReDoc | http://localhost:8000/redoc | Documentación alternativa |

## Configuración

### Variables de Entorno - Backend

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `data/soundtrackers.db` | Ruta a la base de datos SQLite |
| `ASSETS_PATH` | `outputs` | Ruta a los assets (posters, fotos) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Orígenes CORS permitidos |
| `DEBUG` | `false` | Modo debug |

### Variables de Entorno - Frontend

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_URL` | `http://localhost:8000` | URL del backend API |
| `NODE_ENV` | `production` | Entorno de Node.js |

## Volúmenes

Los datos persistentes se montan como volúmenes:

```yaml
volumes:
  - ./data:/app/data:rw        # Base de datos (lectura/escritura)
  - ./outputs:/app/outputs:ro  # Assets (solo lectura)
```

## Comandos Útiles

```bash
# Detener servicios
docker compose down

# Reiniciar un servicio
docker compose restart backend
docker compose restart frontend

# Ver logs de un servicio
docker compose logs -f backend
docker compose logs -f frontend

# Reconstruir sin caché
docker compose build --no-cache

# Limpiar todo (contenedores, redes, volúmenes)
docker compose down -v --rmi all
```

## Actualización

```bash
# Obtener últimos cambios
git pull origin main

# Reconstruir y reiniciar
docker compose down
docker compose build
docker compose up -d
```

## Solución de Problemas

### Backend no inicia

1. Verificar que la base de datos existe:
   ```bash
   ls -la data/soundtrackers.db
   ```

2. Ver logs del backend:
   ```bash
   docker compose logs backend
   ```

### Frontend no conecta al backend

1. Verificar que el backend está healthy:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verificar la variable `API_URL` en el frontend

### Errores de permisos

```bash
# Dar permisos a los directorios de datos
chmod -R 755 data/ outputs/
```

## Arquitectura

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│    Frontend     │────▶│    Backend      │
│   (Next.js)     │     │   (FastAPI)     │
│   Port 3000     │     │   Port 8000     │
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │                 │
                        │    SQLite DB    │
                        │  + FTS5 Search  │
                        │                 │
                        └─────────────────┘
```

## Scripts de Mantenimiento

```bash
# Actualizar países en base de datos desde master list
python scripts/update_countries.py

# Gestionar master list (sincronización)
python scripts/manage_master_list.py --sync-check

# Reconstruir base de datos desde Markdown
python scripts/build_database.py
```

## CI/CD

El proyecto incluye GitHub Actions (`.github/workflows/ci.yml`) que ejecuta:

1. **Backend**: Lint (ruff) + Tests (pytest)
2. **Frontend**: Lint (ESLint) + Type check + Tests (Jest) + Build
3. **Docker**: Verificación de build de imágenes

Los checks se ejecutan en cada push a `main` y en pull requests.

---

**Versión**: 3.0 | **Actualizado**: 2026-02-03
