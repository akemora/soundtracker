# SOUNDTRACKER

> Enciclopedia de Compositores de Bandas Sonoras

---

## Descripción

SOUNDTRACKER es una enciclopedia web de compositores de bandas sonoras con datos generados automáticamente mediante pipelines de IA. Cada perfil incluye:

- **Biografía** completa traducida al español
- **Estilo musical** y características distintivas
- **Anécdotas y curiosidades**
- **Top 10 bandas sonoras** con ranking multi-criterio
- **Filmografía completa** con pósters locales
- **Premios y nominaciones** (Oscar, BAFTA, Grammy, etc.)
- **País de origen** de cada compositor
- **Fuentes externas** verificadas

## Estado del Proyecto

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Pipeline Python | ⚠️ En transición | Script monolítico + pipeline modular (`App/src/soundtracker/`) |
| Datos | ✅ Generados | 142 compositores en `App/outputs/` (~4.3 GB, sin tests/OLD) |
| Base de datos | ✅ Generada | SQLite + FTS5 (`App/data/soundtrackers.db`) |
| Backend API | ✅ Implementado | FastAPI presente (pendiente de validación reciente) |
| Frontend | ✅ Implementado | Next.js 14 presente (pendiente de validación reciente) |
| Docker | ✅ Configurado | Multi-stage builds + Compose |
| CI/CD | ⚠️ Configurado | Workflows existentes (no verificados en esta actualización) |
| Music Crawler | ✅ Módulo CLI | Submódulo independiente (integración pendiente) |

## Estado Actual (2026-02-05)

- Se movieron los documentos de gobernanza al root del repo y los módulos apuntan a ellos.
- El pipeline convive en dos rutas: `scripts/create_composer_files.py` (monolítico) y `src/soundtracker/` (modular).
- Se añadió control de cambios por compositor (`control_changes.md`) y control general (`control_composers.md`).
- El batch controller existe y escribe progreso en `outputs/batch_last_index.txt`.
- El módulo `Music Crawler` está incluido como CLI independiente; integración con SOUNDTRACKER pendiente.

## Inicio Rápido

### Con Docker (Recomendado)

```bash
# Iniciar la aplicación
./start.sh

# Detener
./stop.sh
```

Esto construye las imágenes Docker, inicia los servicios y abre el navegador en http://localhost:3000

### URLs de Acceso

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Características del Frontend

- **Diseño responsivo** con Tailwind CSS
- **Tema claro/oscuro** automático
- **Internacionalización** (ES/EN)
- **Búsqueda FTS5** con autocompletado
- **Filtros** por década y premios
- **Galerías de pósters** optimizadas
- **Nombres estilizados**: Nombre blanco + Apellidos rojos

## Stack Tecnológico

### Backend
- **Python 3.12** con FastAPI
- **SQLite** con FTS5 para búsqueda full-text
- **Pydantic** para validación

### Frontend
- **Next.js 14** con App Router
- **TypeScript** estricto
- **Tailwind CSS** + **shadcn/ui**
- **next-intl** para i18n

### Infraestructura
- **Docker** multi-stage builds
- **Docker Compose** para orquestación
- **GitHub Actions** para CI/CD

## Scripts Disponibles

### Gestión de Datos

```bash
# Generar compositores (pipeline)
python scripts/generate_composers.py --name "Nombre Compositor"

# Construir base de datos desde Markdown
python scripts/build_database.py

# Actualizar países desde master list
python scripts/update_countries.py

# Gestionar master list
# --sync-check: valida consistencia entre master list y outputs
# --add/--remove/--rename: operaciones CRUD
# --rebuild-index: reconstruye desde outputs
# --renumber: reordena por año de nacimiento
python scripts/manage_master_list.py --sync-check
python scripts/manage_master_list.py --sync-check --json
python scripts/manage_master_list.py --add "Nombre" --birth 1980 --country Spain
python scripts/manage_master_list.py --add "Nombre" --birth 1980 --country Spain --generate
python scripts/manage_master_list.py --remove 053 --archive
python scripts/manage_master_list.py --remove 053 --permanent
python scripts/manage_master_list.py --rename 053 "Nuevo Nombre"
python scripts/manage_master_list.py --rebuild-index
python scripts/manage_master_list.py --renumber
```

### Docker

```bash
# Iniciar servicios
./start.sh

# Detener servicios
./stop.sh

# Reconstruir
docker compose build --no-cache
docker compose up -d
```

## Estructura del Proyecto

```
App/
├── backend/                  # API FastAPI
│   ├── app/
│   │   ├── main.py          # Aplicación principal
│   │   ├── config.py        # Configuración
│   │   ├── database.py      # Conexión SQLite
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/        # Lógica de negocio
│   │   └── routers/         # Endpoints API
│   ├── tests/               # Tests pytest
│   └── Dockerfile
├── frontend/                 # Next.js App
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # API client, types
│   │   └── i18n/            # Internacionalización
│   ├── messages/            # Traducciones ES/EN
│   └── Dockerfile
├── src/soundtracker/        # Pipeline Python
├── scripts/                 # Scripts CLI
├── data/                    # Base de datos SQLite
├── outputs/                 # Datos generados (Markdown + pósters)
├── docker-compose.yml       # Orquestación Docker
├── start.sh                 # Script de inicio rápido
└── stop.sh                  # Script de parada
```

## Base de Datos

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `composers` | 164 | Datos principales + país |
| `films` | 11,778 | Filmografía con pósters |
| `awards` | 1,769 | Premios y nominaciones |
| `sources` | 3,926 | Fuentes externas |
| `fts_composers` | - | Índice FTS5 para búsqueda |

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `README.md` | Guía de inicio rápido |
| `DEPLOY.md` | Guía de despliegue Docker |
| `TASKS.md` | Lista de tareas con checklist |
| `CONVENTIONS.md` | Estándares de código Python |
| `CONVENTIONS_FRONTEND.md` | Estándares de frontend |
| `AGENTS.md` | Protocolo para agentes IA |

## Contribuir

1. Lee `AGENTS.md` para entender el protocolo del proyecto
2. Sigue los estándares en `CONVENTIONS.md`
3. Usa commits convencionales: `feat(scope): description`

## Licencia

Proyecto privado.

---

**Versión**: 3.0 | **Actualizado**: 2026-02-03
