# SOUNDTRACKER

> Enciclopedia automatizada de compositores de bandas sonoras de cine

---

## Descripción

SOUNDTRACKER es un sistema de investigación automatizada que genera perfiles completos de compositores de cine. Cada perfil incluye:

- **Biografía** completa traducida al español
- **Estilo musical** y características distintivas
- **Anécdotas y curiosidades**
- **Top 10 bandas sonoras** con ranking multi-criterio
- **Filmografía completa** con pósters locales
- **Premios y nominaciones** (Oscar, BAFTA, Grammy, etc.)
- **Fuentes externas** verificadas

## Estado del Proyecto

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Pipeline Python | ✅ v2.0 | Arquitectura modular refactorizada |
| Datos | ✅ 164 compositores | ~970 MB con pósters |
| Base de datos | ✅ Funcional | SQLite + FTS5 (5.88 MB) |
| Backend API | 🔜 Fase 3 | FastAPI |
| Frontend | 🔜 Fase 4-5 | Next.js + Tailwind |

## Instalación Rápida

### Requisitos
- Python 3.11+
- API Keys: TMDB (obligatoria), Perplexity (recomendada), YouTube (opcional)

### Setup

```bash
# Clonar y entrar al directorio
cd /path/to/SOUNDTRACKER/App

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar en modo desarrollo
pip install -e .
```

### Variables de Entorno

```bash
# Obligatorias
export TMDB_API_KEY="tu_clave_tmdb"
export PPLX_API_KEY="tu_clave_perplexity"

# Opcionales
export YOUTUBE_API_KEY="tu_clave_youtube"
export SPOTIFY_CLIENT_ID="..."
export SPOTIFY_CLIENT_SECRET="..."

# Configuración
export DOWNLOAD_POSTERS=1        # Descargar pósters localmente
export POSTER_WORKERS=8          # Workers concurrentes
export FILM_LIMIT=200            # Máximo películas por compositor
export START_INDEX=1             # Índice para reanudar batch
```

## Uso

### Generar Compositores (Pipeline Nuevo)

```bash
# Procesar todos los compositores
python scripts/generate_composers.py

# Procesar rango específico
python scripts/generate_composers.py --start 1 --end 10

# Procesar compositor individual
python scripts/generate_composers.py --name "John Williams"

# Dry run (sin escribir archivos)
python scripts/generate_composers.py --dry-run
```

### Construir Base de Datos

```bash
# Construir desde archivos Markdown
python scripts/build_database.py

# Reconstruir (drop + create)
python scripts/build_database.py --rebuild

# Verbose
python scripts/build_database.py -v
```

### Consultar Base de Datos

```bash
# Buscar compositor (FTS5)
sqlite3 data/soundtrackers.db "SELECT name FROM composers
  WHERE id IN (SELECT rowid FROM fts_composers WHERE fts_composers MATCH 'Star Wars');"

# Ver estadísticas
sqlite3 data/soundtrackers.db "SELECT * FROM v_composer_stats LIMIT 5;"

# Top premios
sqlite3 data/soundtrackers.db "SELECT composer_name, wins FROM v_awards_summary
  WHERE wins > 0 ORDER BY wins DESC LIMIT 10;"
```

### Actualizar Solo Top 10

```bash
python scripts/update_top10_youtube.py
```

## Estructura del Proyecto

```
App/
├── src/soundtracker/             # Paquete Python principal
│   ├── __init__.py               # Exports principales
│   ├── config.py                 # Settings (Pydantic)
│   ├── models.py                 # Dataclasses (Film, Award, ComposerInfo)
│   ├── logging_config.py         # Logging estructurado
│   ├── pipeline.py               # Orquestación del pipeline
│   ├── api_clients/              # Clientes de APIs externas
│   │   ├── base.py               # BaseClient con retry/timeout
│   │   ├── tmdb.py               # TMDB API
│   │   ├── wikipedia.py          # Wikipedia API
│   │   ├── wikidata.py           # Wikidata SPARQL
│   │   ├── youtube.py            # YouTube Data API
│   │   ├── spotify.py            # Spotify API
│   │   └── search.py             # Perplexity/Google/DDG
│   ├── services/                 # Servicios de negocio
│   │   ├── biography.py          # Biografía, estilo, anécdotas
│   │   ├── filmography.py        # Filmografía completa
│   │   ├── top10.py              # Selección Top 10
│   │   ├── awards.py             # Premios
│   │   ├── posters.py            # Descarga de pósters
│   │   └── translator.py         # Traducción
│   ├── generators/               # Generadores de output
│   │   └── markdown.py           # MarkdownGenerator
│   ├── cache/                    # Sistema de caché
│   │   └── file_cache.py         # FileCache thread-safe
│   └── utils/                    # Utilidades
│       ├── text.py               # Funciones de texto
│       └── urls.py               # Funciones de URLs
├── scripts/                      # Scripts CLI
│   ├── generate_composers.py     # Pipeline CLI (<100 líneas)
│   ├── build_database.py         # ETL a SQLite
│   ├── schema.sql                # DDL de la base de datos
│   ├── etl/                      # Módulo ETL
│   │   └── parser.py             # Parser de Markdown
│   ├── manage_master_list.py     # Gestión master list
│   └── update_top10_youtube.py   # Actualización Top 10
├── data/                         # Base de datos
│   └── soundtrackers.db          # SQLite + FTS5 (5.88 MB)
├── outputs/                      # Datos generados
│   ├── NNN_nombre_compositor.md  # Perfiles en Markdown
│   ├── NNN_nombre_compositor/    # Carpetas con pósters
│   └── composers_master_list.md  # Lista maestra
├── tests/                        # Tests
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_utils.py
│   └── test_generators.py
├── pyproject.toml                # Configuración del proyecto
├── TASKS.md                      # Lista de tareas (291 tareas)
└── README.md                     # Este archivo
```

## Base de Datos

La base de datos SQLite incluye:

| Tabla | Descripción |
|-------|-------------|
| `composers` | Datos principales de compositores |
| `films` | Filmografía con pósters y rankings |
| `awards` | Premios y nominaciones |
| `sources` | Fuentes externas y snippets |
| `notes` | Notas adicionales |
| `fts_composers` | FTS5 para búsqueda full-text |

### Vistas

| Vista | Descripción |
|-------|-------------|
| `v_composer_stats` | Estadísticas por compositor |
| `v_top10_films` | Top 10 con info de compositor |
| `v_awards_summary` | Resumen de premios |

### Estadísticas Actuales

| Métrica | Valor |
|---------|-------|
| Compositores | 164 |
| Películas | 11,778 |
| Top 10 Films | 1,531 |
| Premios | 1,769 |
| Victorias | 874 |
| Fuentes | 3,926 |

## Fuentes de Datos

| Fuente | Uso |
|--------|-----|
| TMDB | Filmografía, pósters, títulos en español, popularidad |
| Wikipedia ES/EN | Biografía, secciones, foto |
| Wikidata | Filmografía, premios |
| Perplexity | Búsqueda de Top 10 |
| Google Search | Fallback de búsqueda |
| YouTube | Views para ranking |
| Spotify | Popularidad (opcional) |

## Plan de Desarrollo

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 0 | ✅ Completada | Preparación y configuración |
| Fase 1 | ✅ Completada | Refactorización Python modular |
| Fase 2 | ✅ Completada | Base de datos SQLite + FTS5 |
| Fase 3 | 🔜 Pendiente | Backend API con FastAPI |
| Fase 4 | 🔜 Pendiente | Frontend base con Next.js |
| Fase 5 | 🔜 Pendiente | Frontend avanzado |
| Fase 6 | 🔜 Pendiente | Deploy y CI/CD |

Ver `TASKS.md` para el checklist detallado (291 tareas).

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_models.py -v
pytest tests/test_cache.py -v

# Con cobertura
pytest tests/ --cov=soundtracker
```

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `README.md` | Guía de inicio rápido |
| `TASKS.md` | **Lista de tareas con checklist** (291 tareas) |
| `AGENTS.md` | Protocolo para agentes IA |
| `CONVENTIONS.md` | Estándares de código Python |
| `CONVENTIONS_FRONTEND.md` | Estándares de frontend |
| `DEVELOPMENT_PLAN.md` | Roadmap técnico |

## Stack Tecnológico

### Actual (Fases 0-2)
- **Python 3.11+** con type hints
- **Pydantic** para configuración y validación
- **SQLite** con FTS5 para búsqueda full-text
- **APIs**: TMDB, Wikipedia, Wikidata, YouTube, Perplexity

### Planificado (Fases 3-6)
- **Backend**: FastAPI + SQLite
- **Frontend**: Next.js 14 + Tailwind + shadcn/ui
- **i18n**: ES (principal), EN (secundario)

## Contribuir

1. Lee `AGENTS.md` para entender el protocolo del proyecto
2. Sigue los estándares en `CONVENTIONS.md`
3. Usa commits convencionales: `feat(scope): description`

## Licencia

Proyecto privado.

---

**Versión**: 2.0 | **Actualizado**: 2026-02-03
