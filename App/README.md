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
| Pipeline Python | ✅ Funcional | Generación de perfiles |
| Datos | ✅ 164 compositores | ~970 MB con pósters |
| Base de datos | 🔜 Planificado | SQLite + FTS5 |
| Backend API | 🔜 Planificado | FastAPI |
| Frontend | 🔜 Planificado | Next.js + Tailwind |

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

# Instalar dependencias
pip install requests beautifulsoup4 google
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
export TOP_FORCE_AWARDS=1        # Forzar premiadas en Top 10
export START_INDEX=1             # Índice para reanudar batch
```

## Uso

### Generar Todos los Compositores

```bash
python scripts/create_composer_files.py
```

### Reanudar desde un Índice Específico

```bash
START_INDEX=41 python scripts/create_composer_files.py
```

### Actualizar Solo Top 10 (sin regenerar datos)

```bash
python scripts/update_top10_youtube.py
```

### Test de un Compositor Individual

```bash
python scripts/test_single_composer.py --composer "John Williams"
```

## Estructura del Proyecto

```
App/
├── scripts/                      # Scripts de generación
│   ├── create_composer_files.py  # Pipeline principal
│   └── update_top10_youtube.py   # Actualización de Top 10
├── outputs/                      # Datos generados
│   ├── NNN_nombre_compositor.md  # Perfiles en Markdown
│   ├── NNN_nombre_compositor/    # Carpetas con pósters
│   ├── tmdb_cache.json           # Caché de TMDB
│   └── streaming_cache.json      # Caché de YouTube
├── AGENTS.md                     # Protocolo para agentes IA
├── CONVENTIONS.md                # Estándares de código Python
├── CONVENTIONS_FRONTEND.md       # Estándares de frontend
├── DEVELOPMENT_PLAN.md           # Plan de desarrollo detallado
├── AUDIT_AND_PROPOSAL.md         # Auditoría técnica
└── README.md                     # Este archivo
```

## Fuentes de Datos

| Fuente | Uso |
|--------|-----|
| TMDB | Filmografía, pósters, títulos en español, popularidad |
| Wikipedia ES/EN | Biografía, secciones, foto |
| Wikidata | Filmografía, premios |
| Perplexity | Búsqueda de Top 10 |
| Google Search | Fallback de búsqueda |
| YouTube | Views para ranking |
| Spotify | Popularidad (pendiente) |

## Formato de Salida

Cada compositor genera:

1. **Archivo Markdown** (`outputs/NNN_nombre_compositor.md`)
   - Biografía
   - Estilo musical
   - Anécdotas
   - Top 10 con enlaces a pósters
   - Filmografía completa
   - Premios
   - Fuentes

2. **Carpeta de assets** (`outputs/NNN_nombre_compositor/`)
   - `photo_nombre_compositor.jpg` - Foto del compositor
   - `posters/` - Todos los pósters de películas

### Formato de Títulos

```
Título Original (Título en España: Título Español)
```

Ejemplo:
```
Star Wars (Título en España: La guerra de las galaxias)
```

## Configuración Avanzada

### Variables de Entorno Completas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TMDB_API_KEY` | - | API key de TMDB (obligatoria) |
| `PPLX_API_KEY` | - | API key de Perplexity |
| `YOUTUBE_API_KEY` | - | API key de YouTube |
| `SPOTIFY_CLIENT_ID` | - | Client ID de Spotify |
| `SPOTIFY_CLIENT_SECRET` | - | Client secret de Spotify |
| `DOWNLOAD_POSTERS` | `1` | Descargar pósters (1/0) |
| `POSTER_WORKERS` | `8` | Workers concurrentes |
| `POSTER_LIMIT` | `0` | Límite de pósters (0=ilimitado) |
| `FILM_LIMIT` | `200` | Máximo películas por compositor |
| `TOP_MIN_VOTE_COUNT` | `50` | Mínimo votos para Top 10 |
| `TOP_FORCE_AWARDS` | `1` | Incluir premiadas en Top 10 |
| `EXTERNAL_SNIPPET_SOURCES` | `12` | Fuentes externas a buscar |
| `EXTERNAL_SNIPPET_MAX_CHARS` | `700` | Máximo chars por snippet |
| `MAX_BIO_PARAGRAPHS` | `6` | Párrafos de biografía |
| `SEARCH_WEB_ENABLED` | `1` | Habilitar búsqueda web |
| `START_INDEX` | `1` | Índice para reanudar |

## Plan de Desarrollo

El proyecto está en proceso de expansión hacia una aplicación web completa:

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 0 | Pendiente | Preparación y Git LFS |
| Fase 1 | Pendiente | Refactorización del código Python |
| Fase 2 | Pendiente | Base de datos SQLite + FTS5 |
| Fase 3 | Pendiente | Backend API con FastAPI |
| Fase 4 | Pendiente | Frontend base con Next.js |
| Fase 5 | Pendiente | Frontend avanzado |
| Fase 6 | Pendiente | Deploy y CI/CD |

Ver `DEVELOPMENT_PLAN.md` para el roadmap detallado.

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `README.md` | Guía de inicio rápido |
| `TASKS.md` | **Lista de tareas con checklist** (229 tareas) |
| `AGENTS.md` | Protocolo para agentes IA |
| `CONVENTIONS.md` | Estándares de código Python |
| `CONVENTIONS_FRONTEND.md` | Estándares de frontend |
| `DEVELOPMENT_PLAN.md` | Roadmap técnico |
| `AUDIT_AND_PROPOSAL.md` | Auditoría y propuestas |

> **IMPORTANTE**: `TASKS.md` debe mantenerse actualizado después de cada tarea completada.

## Stack Tecnológico

### Actual (Pipeline)
- Python 3.11+
- requests, BeautifulSoup4
- APIs: TMDB, Wikipedia, Wikidata, YouTube, Perplexity

### Planificado
- **Backend**: FastAPI + SQLite (FTS5)
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
