# Auditoría y Propuesta de Mejora - SOUNDTRACKER

**Auditoría Técnica Completa** | v1.0 | 2026-02-03

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Estado Actual del Proyecto](#2-estado-actual-del-proyecto)
3. [Auditoría del Código Python](#3-auditoría-del-código-python)
4. [Propuesta de Base de Datos](#4-propuesta-de-base-de-datos)
5. [Propuesta de Backend API](#5-propuesta-de-backend-api)
6. [Propuesta de Frontend](#6-propuesta-de-frontend)
7. [Roadmap de Implementación](#7-roadmap-de-implementación)
8. [Riesgos y Mitigación](#8-riesgos-y-mitigación)

---

## 1. Resumen Ejecutivo

### 1.1 Qué es SOUNDTRACKER

SOUNDTRACKER es un **sistema de investigación automatizada de compositores de cine** que genera perfiles completos en Markdown con:
- Biografía, estilo musical y anécdotas
- Filmografía completa con pósters locales
- Top 10 bandas sonoras (ranking multi-criterio)
- Premios y nominaciones
- Fuentes externas verificadas

### 1.2 Estado Actual

| Componente | Estado | Observaciones |
|------------|--------|---------------|
| Pipeline Python | ✅ Funcional | 1,968 líneas en un solo archivo |
| Datos generados | ✅ 164 compositores | ~970 MB con pósters |
| Base de datos | ❌ No existe | Datos en Markdown (sin búsqueda estructurada) |
| Backend API | ❌ No existe | Plan en DEVELOPMENT_PLAN.md |
| Frontend | ❌ No existe | Plan en DEVELOPMENT_PLAN.md |

### 1.3 Hallazgos Críticos

**Fortalezas:**
- Integración robusta con múltiples APIs (TMDB, Wikipedia, Wikidata, YouTube)
- Sistema de caché efectivo (TMDB, streaming)
- Descarga concurrente de pósters (8 workers)
- Traducción automática con detección de idioma
- Sistema de fallback para búsquedas (Perplexity → Google → DuckDuckGo)

**Debilidades:**
- **Archivo monolítico**: `create_composer_files.py` (1,968 líneas) viola límites de mantenibilidad
- **Sin tests**: 0% cobertura
- **Sin type hints**: Solo en signaturas, no en retornos complejos
- **Acoplamiento alto**: Funciones de I/O, lógica y formateo mezcladas
- **Sin logging estructurado**: Solo `print()` statements
- **Sin validación de datos**: Entrada y salida sin schemas

---

## 2. Estado Actual del Proyecto

### 2.1 Estructura de Archivos

```
App/
├── scripts/
│   ├── create_composer_files.py     # 1,968 líneas (CRÍTICO)
│   ├── update_top10_youtube.py      # 170 líneas
│   ├── test_single_composer.py      # 48 líneas
│   ├── batch_process_composers.py   # 52 líneas (placeholder)
│   ├── get_composer_info.py         # 105 líneas
│   └── deep_search_composers.py     # 50 líneas (placeholder)
├── outputs/
│   ├── NNN_nombre_compositor.md     # 164 archivos
│   ├── NNN_nombre_compositor/       # 164 carpetas con pósters
│   ├── tmdb_cache.json              # Caché de TMDB
│   ├── streaming_cache.json         # Caché de YouTube/Spotify
│   └── composers_master_list.md     # Lista maestra
├── intermediate_research/           # Datos de verificación
├── DEVELOPMENT_PLAN.md
├── PENDING_CHANGES.md
├── README.md
├── AGENTS_TEMPLATE.md
├── CONVENTIONS_TEMPLATE.md
└── CONVENTIONS_FRONTEND_TEMPLATE.md
```

### 2.2 APIs y Servicios Integrados

| Servicio | Uso | Estado |
|----------|-----|--------|
| TMDB | Filmografía, pósters, títulos ES | ✅ Activo |
| Wikipedia ES/EN | Biografía, secciones | ✅ Activo |
| Wikidata | Filmografía, premios | ✅ Activo |
| Perplexity | Búsqueda principal | ✅ Activo |
| Google Search | Fallback | ✅ Activo |
| DuckDuckGo | Fallback | ✅ Activo |
| YouTube | Views para Top 10 | ✅ Activo |
| Spotify | Popularidad | ⏸️ Pendiente credenciales |
| Google Translate | Traducción | ✅ Activo |

### 2.3 Métricas del Código Actual

```
create_composer_files.py:
- Líneas totales: 1,968
- Funciones: 85+
- Clases: 0 (todo funcional)
- Imports: 14 módulos
- Constantes globales: 40+
- Diccionarios globales mutables: 4 (TMDB_MOVIE_CACHE, STREAMING_CACHE, SPOTIFY_TOKEN, BLOCKED_DOMAINS)
```

---

## 3. Auditoría del Código Python

### 3.1 Problemas Identificados

#### 🔴 CRÍTICO: Archivo Monolítico (1,968 líneas)

**Problema**: `create_composer_files.py` excede el límite recomendado de 1,000 líneas y mezcla:
- Configuración y constantes
- Clientes de APIs (TMDB, Wikipedia, Wikidata, YouTube, Spotify)
- Lógica de búsqueda y scraping
- Transformación de datos
- Generación de Markdown
- I/O de archivos

**Impacto**:
- Difícil de mantener y testear
- Contexto excesivo para LLMs (~40K tokens)
- Alto riesgo de regresiones

#### 🔴 CRÍTICO: Variables Globales Mutables

```python
# Líneas 610-612
TMDB_MOVIE_CACHE = load_tmdb_cache()
STREAMING_CACHE = load_streaming_cache()
SPOTIFY_TOKEN = {'value': None, 'expires_at': 0}
```

**Problema**: Mutación de estado global en múltiples funciones causa:
- Race conditions potenciales en concurrencia
- Dificultad para testear
- Efectos secundarios ocultos

#### 🟠 ALTO: Sin Type Hints Completos

```python
# Actual (incompleto)
def get_composer_info(composer: str, composer_folder: Path) -> Dict:

# Debería ser
def get_composer_info(composer: str, composer_folder: Path) -> ComposerInfo:
```

#### 🟠 ALTO: Sin Tests

- 0% cobertura de tests
- Sin validación de schemas de entrada/salida
- Sin mocks para APIs externas

#### 🟡 MEDIO: Logging con print()

```python
# Actual
print(f"Processing {composer} -> {filename}")
print(f"    - failed to fetch {url}: {exc}")

# Debería usar logging
logger.info(f"Processing {composer} -> {filename}")
logger.warning(f"Failed to fetch {url}", exc_info=True)
```

#### 🟡 MEDIO: Constantes Hardcodeadas

```python
# Línea 109
TOP_MIN_VOTE_COUNT = int(os.getenv('TOP_MIN_VOTE_COUNT', '50'))
# Pero también...
if year and (year < 1900 or year > 2026):  # Hardcoded 2026
```

### 3.2 Propuesta de Refactorización

**Nueva estructura modular:**

```
App/
├── src/
│   └── soundtracker/
│       ├── __init__.py
│       ├── config.py              # Configuración centralizada (Pydantic)
│       ├── models.py              # Dataclasses/Pydantic models
│       ├── clients/               # Clientes de APIs
│       │   ├── __init__.py
│       │   ├── base.py            # BaseClient abstracto
│       │   ├── tmdb.py            # TMDBClient
│       │   ├── wikipedia.py       # WikipediaClient
│       │   ├── wikidata.py        # WikidataClient
│       │   ├── youtube.py         # YouTubeClient
│       │   ├── spotify.py         # SpotifyClient
│       │   └── search.py          # SearchClient (Perplexity/Google/DDG)
│       ├── services/              # Lógica de negocio
│       │   ├── __init__.py
│       │   ├── biography.py       # Obtención de biografía
│       │   ├── filmography.py     # Construcción de filmografía
│       │   ├── awards.py          # Procesamiento de premios
│       │   ├── top10.py           # Algoritmo de ranking Top 10
│       │   ├── posters.py         # Descarga de pósters
│       │   └── translator.py      # Traducción
│       ├── generators/            # Generación de salidas
│       │   ├── __init__.py
│       │   └── markdown.py        # MarkdownGenerator
│       ├── cache/                 # Sistema de caché
│       │   ├── __init__.py
│       │   └── file_cache.py      # FileCache thread-safe
│       └── utils/                 # Utilidades
│           ├── __init__.py
│           ├── text.py            # clean_text, truncate_text
│           ├── urls.py            # slugify, fetch_url
│           └── async_helpers.py   # Utilidades async
├── tests/
│   ├── conftest.py
│   ├── test_clients/
│   ├── test_services/
│   └── test_generators/
├── scripts/
│   ├── create_composer_files.py   # Solo orquestación (~50 líneas)
│   └── update_top10.py
└── pyproject.toml
```

### 3.3 Modelos de Datos Propuestos

```python
# src/soundtracker/models.py
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class Film:
    title: str
    original_title: str
    title_es: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    poster_local: Optional[Path] = None
    popularity: Optional[float] = None
    vote_count: Optional[int] = None
    vote_average: Optional[float] = None
    youtube_views: Optional[int] = None
    spotify_popularity: Optional[float] = None

@dataclass
class Award:
    award: str
    year: Optional[int] = None
    film: Optional[str] = None
    status: str = "Nomination"  # "Win" | "Nomination"

@dataclass
class ExternalSource:
    name: str
    url: str
    snippet: Optional[str] = None

@dataclass
class ComposerInfo:
    name: str
    slug: str
    folder: Path
    photo: Optional[Path] = None
    biography: Optional[str] = None
    style: Optional[str] = None
    anecdotes: Optional[str] = None
    filmography: list[Film] = field(default_factory=list)
    top_10_films: list[Film] = field(default_factory=list)
    awards: list[Award] = field(default_factory=list)
    external_sources: list[ExternalSource] = field(default_factory=list)
    external_snippets: list[ExternalSource] = field(default_factory=list)
```

### 3.4 Configuración Centralizada

```python
# src/soundtracker/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # APIs
    tmdb_api_key: Optional[str] = None
    pplx_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None

    # Comportamiento
    download_posters: bool = True
    search_web_enabled: bool = True
    poster_workers: int = 8
    film_limit: int = 200
    top_min_vote_count: int = 50
    top_force_awards: bool = True

    # Texto
    external_snippet_sources: int = 12
    external_snippet_max_chars: int = 700
    max_bio_paragraphs: int = 6
    min_paragraph_len: int = 50

    # Batch
    start_index: int = 1

    class Config:
        env_file = ".env"
        env_prefix = ""

settings = Settings()
```

---

## 4. Propuesta de Base de Datos

### 4.1 Tecnología: SQLite + FTS5

**Justificación:**
- **Portabilidad**: Un solo archivo `soundtrackers.db`
- **Versionable**: Se puede incluir en Git
- **FTS5**: Búsqueda full-text nativa sin servidor adicional
- **Rendimiento**: Suficiente para 1,000+ compositores
- **Sin dependencias**: No requiere servidor de BD

### 4.2 Esquema de Base de Datos

```sql
-- Tabla principal: Compositores
CREATE TABLE composers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    photo_path TEXT,
    biography_es TEXT,
    biography_en TEXT,
    style_es TEXT,
    style_en TEXT,
    anecdotes_es TEXT,
    anecdotes_en TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    nationality TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Índices para búsquedas comunes
CREATE INDEX idx_composers_name ON composers(name);
CREATE INDEX idx_composers_slug ON composers(slug);

-- Tabla: Películas/Filmografía
CREATE TABLE films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id) ON DELETE CASCADE,
    title_original TEXT NOT NULL,
    title_es TEXT,
    year INTEGER,
    poster_path TEXT,
    poster_url TEXT,
    is_top10 INTEGER DEFAULT 0,
    top10_rank INTEGER,
    tmdb_id INTEGER,
    tmdb_popularity REAL,
    tmdb_vote_count INTEGER,
    tmdb_vote_average REAL,
    youtube_views INTEGER,
    spotify_popularity REAL,
    score REAL,  -- Score calculado para ranking
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_films_composer ON films(composer_id);
CREATE INDEX idx_films_year ON films(year);
CREATE INDEX idx_films_top10 ON films(is_top10);
CREATE INDEX idx_films_score ON films(score DESC);

-- Tabla: Premios
CREATE TABLE awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id) ON DELETE CASCADE,
    award_name TEXT NOT NULL,
    award_name_es TEXT,
    year INTEGER,
    film_title TEXT,
    status TEXT CHECK(status IN ('Win', 'Nomination')) DEFAULT 'Nomination',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_awards_composer ON awards(composer_id);
CREATE INDEX idx_awards_year ON awards(year);
CREATE INDEX idx_awards_status ON awards(status);

-- Tabla: Fuentes externas
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT,
    is_snippet INTEGER DEFAULT 0,  -- 1 si es snippet con texto extraído
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sources_composer ON sources(composer_id);

-- Tabla: Notas/Snippets externos
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_notes_composer ON notes(composer_id);

-- FTS5: Búsqueda full-text
CREATE VIRTUAL TABLE fts_composers USING fts5(
    name,
    biography_es,
    style_es,
    anecdotes_es,
    film_titles,      -- Concatenación de títulos de películas
    award_names,      -- Concatenación de premios
    content='composers',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers para mantener FTS sincronizado
CREATE TRIGGER composers_ai AFTER INSERT ON composers BEGIN
    INSERT INTO fts_composers(rowid, name, biography_es, style_es, anecdotes_es)
    VALUES (new.id, new.name, new.biography_es, new.style_es, new.anecdotes_es);
END;

CREATE TRIGGER composers_ad AFTER DELETE ON composers BEGIN
    INSERT INTO fts_composers(fts_composers, rowid, name, biography_es, style_es, anecdotes_es)
    VALUES ('delete', old.id, old.name, old.biography_es, old.style_es, old.anecdotes_es);
END;

CREATE TRIGGER composers_au AFTER UPDATE ON composers BEGIN
    INSERT INTO fts_composers(fts_composers, rowid, name, biography_es, style_es, anecdotes_es)
    VALUES ('delete', old.id, old.name, old.biography_es, old.style_es, old.anecdotes_es);
    INSERT INTO fts_composers(rowid, name, biography_es, style_es, anecdotes_es)
    VALUES (new.id, new.name, new.biography_es, new.style_es, new.anecdotes_es);
END;

-- Vista: Compositores con estadísticas
CREATE VIEW v_composer_stats AS
SELECT
    c.id,
    c.name,
    c.slug,
    c.photo_path,
    COUNT(DISTINCT f.id) as film_count,
    COUNT(DISTINCT CASE WHEN f.is_top10 = 1 THEN f.id END) as top10_count,
    COUNT(DISTINCT CASE WHEN a.status = 'Win' THEN a.id END) as wins,
    COUNT(DISTINCT CASE WHEN a.status = 'Nomination' THEN a.id END) as nominations,
    MIN(f.year) as career_start,
    MAX(f.year) as career_end
FROM composers c
LEFT JOIN films f ON f.composer_id = c.id
LEFT JOIN awards a ON a.composer_id = c.id
GROUP BY c.id;
```

### 4.3 ETL: Markdown → SQLite

```python
# scripts/etl_markdown_to_sqlite.py
"""
Parser de archivos Markdown a SQLite.

Flujo:
1. Lee App/outputs/*.md
2. Parsea secciones (Biografía, Estilo, etc.)
3. Extrae filmografía y premios
4. Normaliza datos
5. Inserta en SQLite
"""

import re
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedComposer:
    name: str
    slug: str
    photo_path: Optional[str]
    biography: Optional[str]
    style: Optional[str]
    anecdotes: Optional[str]
    top_10: list[dict]
    filmography: list[dict]
    awards: list[dict]
    sources: list[dict]
    snippets: list[dict]

def parse_markdown_file(path: Path) -> ParsedComposer:
    """Parsea un archivo Markdown de compositor."""
    content = path.read_text(encoding='utf-8')

    # Extraer nombre del heading
    name_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    name = name_match.group(1) if name_match else path.stem

    # Extraer secciones
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    # Parsear filmografía
    filmography = parse_filmography(sections.get('Filmografía completa', ''))

    # Parsear premios
    awards = parse_awards(sections.get('Premios y nominaciones', ''))

    # Parsear Top 10
    top_10 = parse_top10(sections.get('Top 10 bandas sonoras', ''))

    return ParsedComposer(
        name=name,
        slug=path.stem.split('_', 1)[1] if '_' in path.stem else path.stem,
        photo_path=extract_photo_path(content),
        biography=sections.get('Biografía'),
        style=sections.get('Estilo musical'),
        anecdotes=sections.get('Anécdotas y curiosidades'),
        top_10=top_10,
        filmography=filmography,
        awards=awards,
        sources=parse_sources(sections.get('Fuentes adicionales', '')),
        snippets=parse_snippets(sections.get('Notas externas', '')),
    )

def parse_filmography(text: str) -> list[dict]:
    """Parsea la sección de filmografía."""
    films = []
    pattern = r'^- (.+?)(?:\s+\((\d{4})\))?(?: · \[Póster\]\((.+?)\))?$'

    for line in text.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            title_full = match.group(1)
            year = int(match.group(2)) if match.group(2) else None
            poster = match.group(3)

            # Extraer título original y español
            title_match = re.match(r'(.+?)\s*\(Título en España:\s*(.+?)\)', title_full)
            if title_match:
                original = title_match.group(1).strip()
                spanish = title_match.group(2).strip()
            else:
                original = title_full
                spanish = None

            films.append({
                'title_original': original,
                'title_es': spanish,
                'year': year,
                'poster_path': poster,
            })

    return films

def build_database(output_dir: Path, db_path: Path):
    """Construye la base de datos desde los archivos Markdown."""
    conn = sqlite3.connect(db_path)

    # Crear esquema
    with open('schema.sql') as f:
        conn.executescript(f.read())

    # Procesar cada archivo
    for md_file in sorted(output_dir.glob('*.md')):
        if md_file.name == 'composers_master_list.md':
            continue

        composer = parse_markdown_file(md_file)
        insert_composer(conn, composer)

    # Actualizar índice FTS
    rebuild_fts_index(conn)

    conn.commit()
    conn.close()
```

---

## 5. Propuesta de Backend API

### 5.1 Stack: FastAPI + SQLite

**Justificación:**
- **FastAPI**: Async, tipado, documentación automática (OpenAPI)
- **Pydantic**: Validación de datos integrada
- **SQLite**: Sin servidor adicional
- **Uvicorn**: Servidor ASGI de alto rendimiento

### 5.2 Estructura del Backend

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app
│   ├── config.py              # Settings
│   ├── database.py            # Conexión SQLite
│   ├── models/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── composer.py
│   │   ├── film.py
│   │   └── award.py
│   ├── routers/               # Endpoints
│   │   ├── __init__.py
│   │   ├── composers.py
│   │   ├── films.py
│   │   ├── search.py
│   │   └── assets.py
│   ├── services/              # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── composer_service.py
│   │   └── search_service.py
│   └── auth/                  # Autenticación
│       ├── __init__.py
│       └── jwt.py
├── tests/
├── requirements.txt
└── Dockerfile
```

### 5.3 Endpoints Principales

```python
# app/routers/composers.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/composers", tags=["composers"])

@router.get("/")
async def list_composers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name", enum=["name", "film_count", "wins"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    has_awards: Optional[bool] = None,
    decade: Optional[int] = None,
):
    """Lista compositores con paginación y filtros."""
    pass

@router.get("/{composer_id}")
async def get_composer(composer_id: int):
    """Obtiene detalle completo de un compositor."""
    pass

@router.get("/{composer_id}/filmography")
async def get_filmography(
    composer_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
):
    """Obtiene filmografía paginada de un compositor."""
    pass

@router.get("/{composer_id}/awards")
async def get_awards(composer_id: int):
    """Obtiene premios y nominaciones de un compositor."""
    pass

# app/routers/search.py
@router.get("/api/search")
async def search(
    q: str = Query(..., min_length=2),
    type: str = Query("all", enum=["all", "composers", "films"]),
    limit: int = Query(20, ge=1, le=100),
):
    """Búsqueda full-text usando FTS5."""
    pass

# app/routers/assets.py
@router.get("/api/assets/{path:path}")
async def serve_asset(path: str):
    """Sirve pósters y fotos locales."""
    pass
```

### 5.4 Modelos Pydantic

```python
# app/models/composer.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComposerBase(BaseModel):
    name: str
    slug: str

class ComposerSummary(ComposerBase):
    id: int
    photo_path: Optional[str]
    film_count: int
    wins: int
    nominations: int
    career_start: Optional[int]
    career_end: Optional[int]

class ComposerDetail(ComposerBase):
    id: int
    photo_path: Optional[str]
    biography_es: Optional[str]
    style_es: Optional[str]
    anecdotes_es: Optional[str]
    top_10_films: list["FilmSummary"]
    stats: "ComposerStats"

class ComposerStats(BaseModel):
    film_count: int
    wins: int
    nominations: int
    career_start: Optional[int]
    career_end: Optional[int]

# app/models/film.py
class FilmSummary(BaseModel):
    id: int
    title_original: str
    title_es: Optional[str]
    year: Optional[int]
    poster_path: Optional[str]
    is_top10: bool
    top10_rank: Optional[int]

class FilmDetail(FilmSummary):
    tmdb_popularity: Optional[float]
    tmdb_vote_average: Optional[float]
    youtube_views: Optional[int]
    score: Optional[float]
```

---

## 6. Propuesta de Frontend

### 6.1 Stack: Next.js 14 + Tailwind + shadcn/ui

**Justificación:**
- **Next.js 14**: App Router, RSC, optimización de imágenes
- **Tailwind CSS**: Utilidades, design tokens, responsive
- **shadcn/ui**: Componentes accesibles y personalizables
- **TypeScript**: Type safety
- **next-intl**: i18n (ES/EN)

### 6.2 Estructura del Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── [locale]/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Home
│   │   │   ├── composers/
│   │   │   │   ├── page.tsx           # Listado
│   │   │   │   └── [slug]/
│   │   │   │       └── page.tsx       # Detalle
│   │   │   └── search/
│   │   │       └── page.tsx           # Búsqueda
│   │   └── api/                       # API routes (proxy)
│   ├── components/
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── composers/
│   │   │   ├── ComposerCard.tsx
│   │   │   ├── ComposerGrid.tsx
│   │   │   ├── ComposerDetail.tsx
│   │   │   ├── FilmographyList.tsx
│   │   │   ├── Top10Gallery.tsx
│   │   │   └── AwardsList.tsx
│   │   └── search/
│   │       ├── SearchBar.tsx
│   │       ├── SearchResults.tsx
│   │       └── FilterPanel.tsx
│   ├── lib/
│   │   ├── api.ts                     # API client
│   │   ├── types.ts                   # TypeScript types
│   │   └── utils.ts                   # Helpers
│   ├── styles/
│   │   ├── globals.css                # Tailwind + tokens
│   │   └── tokens.css                 # Design tokens
│   └── i18n/
│       ├── messages/
│       │   ├── es.json
│       │   └── en.json
│       └── config.ts
├── public/
│   └── assets/                        # Symlink a outputs
├── tailwind.config.ts
├── next.config.js
└── package.json
```

### 6.3 Design Tokens (Tailwind)

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Paleta principal (cálida, cinematográfica)
        primary: {
          50: "#FDF8F6",
          100: "#F9EBE5",
          200: "#F3D5C8",
          300: "#E9B59D",
          400: "#D98B66",
          500: "#C96A40",  // Principal
          600: "#A85532",
          700: "#8A4428",
          800: "#6D3620",
          900: "#4A2515",
        },
        secondary: {
          50: "#F5F7FA",
          100: "#E4E9F0",
          200: "#C9D3E1",
          300: "#A3B3CA",
          400: "#7A91B0",
          500: "#5A7499",  // Secundario
          600: "#485D7A",
          700: "#3A4A61",
          800: "#2D3A4D",
          900: "#1F2937",
        },
        accent: {
          gold: "#D4AF37",
          silver: "#C0C0C0",
          bronze: "#CD7F32",
        },
        background: {
          light: "#FAFAF9",
          dark: "#1A1A1A",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-playfair)", "Georgia", "serif"],
      },
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        "poster": "0 4px 20px -2px rgba(0, 0, 0, 0.3)",
        "card": "0 2px 8px -1px rgba(0, 0, 0, 0.1)",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("@tailwindcss/forms"),
  ],
};

export default config;
```

### 6.4 Componentes Clave

```tsx
// src/components/composers/ComposerCard.tsx
import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Trophy, Film } from "lucide-react";

interface ComposerCardProps {
  id: number;
  name: string;
  slug: string;
  photoPath?: string;
  filmCount: number;
  wins: number;
  careerStart?: number;
  careerEnd?: number;
}

export function ComposerCard({
  name,
  slug,
  photoPath,
  filmCount,
  wins,
  careerStart,
  careerEnd,
}: ComposerCardProps) {
  const careerYears = careerStart && careerEnd
    ? `${careerStart} - ${careerEnd}`
    : careerStart
    ? `Desde ${careerStart}`
    : "";

  return (
    <Link href={`/composers/${slug}`} className="group">
      <article className="bg-white rounded-xl shadow-card hover:shadow-poster transition-shadow duration-300 overflow-hidden">
        {/* Foto */}
        <div className="aspect-[3/4] relative bg-secondary-100">
          {photoPath ? (
            <Image
              src={`/api/assets/${photoPath}`}
              alt={name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-6xl text-secondary-300">🎼</span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-4">
          <h3 className="font-display text-lg font-semibold text-secondary-900 group-hover:text-primary-600 transition-colors">
            {name}
          </h3>

          {careerYears && (
            <p className="text-sm text-secondary-500 mt-1">{careerYears}</p>
          )}

          {/* Stats */}
          <div className="flex items-center gap-4 mt-3">
            <div className="flex items-center gap-1 text-sm text-secondary-600">
              <Film className="w-4 h-4" />
              <span>{filmCount}</span>
            </div>

            {wins > 0 && (
              <Badge variant="secondary" className="bg-accent-gold/10 text-accent-gold">
                <Trophy className="w-3 h-3 mr-1" />
                {wins} {wins === 1 ? "Oscar" : "Oscars"}
              </Badge>
            )}
          </div>
        </div>
      </article>
    </Link>
  );
}
```

```tsx
// src/components/composers/Top10Gallery.tsx
"use client";

import Image from "next/image";
import { useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

interface Film {
  id: number;
  titleOriginal: string;
  titleEs?: string;
  year?: number;
  posterPath?: string;
  rank: number;
}

interface Top10GalleryProps {
  films: Film[];
  composerName: string;
}

export function Top10Gallery({ films, composerName }: Top10GalleryProps) {
  const [selectedFilm, setSelectedFilm] = useState<Film | null>(null);

  return (
    <section>
      <h2 className="font-display text-2xl font-bold text-secondary-900 mb-6">
        Top 10 Bandas Sonoras
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
        {films.map((film) => (
          <button
            key={film.id}
            onClick={() => setSelectedFilm(film)}
            className="group relative aspect-[2/3] rounded-lg overflow-hidden shadow-poster hover:shadow-xl transition-all duration-300"
          >
            {/* Rank Badge */}
            <Badge
              className="absolute top-2 left-2 z-10 bg-primary-500 text-white font-bold"
            >
              #{film.rank}
            </Badge>

            {/* Poster */}
            {film.posterPath ? (
              <Image
                src={`/api/assets/${film.posterPath}`}
                alt={film.titleOriginal}
                fill
                className="object-cover group-hover:scale-110 transition-transform duration-500"
              />
            ) : (
              <div className="w-full h-full bg-secondary-200 flex items-center justify-center">
                <span className="text-4xl">🎬</span>
              </div>
            )}

            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="absolute bottom-0 left-0 right-0 p-3">
                <p className="text-white text-sm font-medium line-clamp-2">
                  {film.titleEs || film.titleOriginal}
                </p>
                {film.year && (
                  <p className="text-white/70 text-xs mt-1">{film.year}</p>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Modal de detalle */}
      <Dialog open={!!selectedFilm} onOpenChange={() => setSelectedFilm(null)}>
        <DialogContent className="max-w-2xl">
          {selectedFilm && (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                {selectedFilm.posterPath && (
                  <Image
                    src={`/api/assets/${selectedFilm.posterPath}`}
                    alt={selectedFilm.titleOriginal}
                    fill
                    className="object-cover"
                  />
                )}
              </div>
              <div>
                <Badge className="mb-2">#{selectedFilm.rank} en Top 10</Badge>
                <h3 className="font-display text-xl font-bold">
                  {selectedFilm.titleOriginal}
                </h3>
                {selectedFilm.titleEs && selectedFilm.titleEs !== selectedFilm.titleOriginal && (
                  <p className="text-secondary-600 mt-1">
                    Título en España: {selectedFilm.titleEs}
                  </p>
                )}
                {selectedFilm.year && (
                  <p className="text-secondary-500 mt-2">{selectedFilm.year}</p>
                )}
                <p className="mt-4 text-secondary-600">
                  Música compuesta por <span className="font-medium">{composerName}</span>
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}
```

### 6.5 Páginas Principales

```tsx
// src/app/[locale]/page.tsx (Home)
import { SearchBar } from "@/components/search/SearchBar";
import { ComposerGrid } from "@/components/composers/ComposerGrid";
import { getTranslations } from "next-intl/server";

export default async function HomePage() {
  const t = await getTranslations("home");

  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-secondary-900 to-secondary-800 text-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="font-display text-4xl md:text-5xl font-bold mb-4">
            {t("title")}
          </h1>
          <p className="text-secondary-200 text-lg mb-8 max-w-2xl mx-auto">
            {t("subtitle")}
          </p>
          <SearchBar
            placeholder={t("searchPlaceholder")}
            className="max-w-xl mx-auto"
          />
        </div>
      </section>

      {/* Featured Composers */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="font-display text-2xl font-bold text-secondary-900 mb-8">
            {t("featuredComposers")}
          </h2>
          <ComposerGrid featured limit={8} />
        </div>
      </section>
    </main>
  );
}
```

### 6.6 i18n

```json
// src/i18n/messages/es.json
{
  "home": {
    "title": "Enciclopedia de Compositores de Cine",
    "subtitle": "Descubre las mentes detrás de las bandas sonoras más memorables del cine",
    "searchPlaceholder": "Buscar compositor, película o premio...",
    "featuredComposers": "Compositores Destacados"
  },
  "composer": {
    "biography": "Biografía",
    "style": "Estilo Musical",
    "anecdotes": "Anécdotas y Curiosidades",
    "top10": "Top 10 Bandas Sonoras",
    "filmography": "Filmografía Completa",
    "awards": "Premios y Nominaciones",
    "sources": "Fuentes",
    "films": "{count, plural, one {# película} other {# películas}}",
    "wins": "{count, plural, one {# premio} other {# premios}}",
    "nominations": "{count, plural, one {# nominación} other {# nominaciones}}"
  },
  "search": {
    "results": "Resultados de búsqueda",
    "noResults": "No se encontraron resultados para \"{query}\"",
    "filters": "Filtros"
  },
  "common": {
    "loading": "Cargando...",
    "error": "Error al cargar datos",
    "retry": "Reintentar"
  }
}
```

---

## 7. Roadmap de Implementación

### Fase 0: Preparación (1-2 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Medir tamaño real de outputs (posters) | Alta | 0.5 días |
| Evaluar necesidad de Git LFS | Alta | 0.5 días |
| Configurar pyproject.toml | Media | 0.5 días |
| Crear estructura de directorios | Media | 0.5 días |

### Fase 1: Refactorización Python (5-7 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Crear modelos de datos (Pydantic/dataclasses) | Alta | 1 día |
| Extraer clientes de APIs (TMDBClient, etc.) | Alta | 2 días |
| Extraer servicios de negocio | Alta | 2 días |
| Implementar sistema de logging | Media | 0.5 días |
| Escribir tests unitarios (50% cobertura) | Alta | 2 días |

### Fase 2: Base de Datos + ETL (3-4 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Implementar esquema SQLite + FTS5 | Alta | 1 día |
| Desarrollar parser de Markdown | Alta | 1.5 días |
| Script de ETL completo | Alta | 1 día |
| Validación e integridad de datos | Media | 0.5 días |

### Fase 3: Backend API (4-5 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Setup FastAPI + estructura | Alta | 0.5 días |
| Endpoints de compositores | Alta | 1.5 días |
| Endpoint de búsqueda FTS5 | Alta | 1 día |
| Autenticación JWT (admin/user) | Media | 1 día |
| Tests de API | Media | 1 día |

### Fase 4: Frontend Base (5-7 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Setup Next.js + Tailwind + shadcn | Alta | 1 día |
| Design tokens y tema | Alta | 0.5 días |
| Layout principal + navegación | Alta | 1 día |
| Página Home | Alta | 1 día |
| Listado de compositores | Alta | 1.5 días |
| Configurar i18n | Media | 1 día |

### Fase 5: Frontend Avanzado (7-10 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Página de detalle de compositor | Alta | 2 días |
| Galería Top 10 con modal | Alta | 1.5 días |
| Listado de filmografía con paginación | Alta | 1.5 días |
| Búsqueda con filtros | Alta | 2 días |
| Responsive y dark mode | Media | 1.5 días |
| Optimización de imágenes | Media | 1 día |

### Fase 6: Deploy y CI/CD (2-3 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Dockerizar backend | Alta | 0.5 días |
| Dockerizar frontend | Alta | 0.5 días |
| Script de deploy | Alta | 1 día |
| Pipeline Git → servidor | Media | 1 día |

### Total Estimado: 27-38 días laborables

---

## 8. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Tamaño de pósters excede límites de Git | Alta | Alto | Usar Git LFS o almacenamiento S3 |
| APIs externas cambian/fallan | Media | Medio | Fallbacks + caché agresivo |
| FTS5 lento con muchos datos | Baja | Medio | Índices optimizados + límites de resultados |
| Refactorización introduce bugs | Media | Alto | Tests exhaustivos antes de migrar |
| Credenciales de Spotify no disponibles | Alta | Bajo | YouTube como único indicador de streaming |

---

## Anexo: Checklist de Implementación

### Python/Backend

- [ ] Crear `pyproject.toml` con dependencias y configuración
- [ ] Implementar `src/soundtracker/config.py` con Pydantic Settings
- [ ] Implementar `src/soundtracker/models.py` con dataclasses
- [ ] Extraer `TMDBClient` con caché
- [ ] Extraer `WikipediaClient`
- [ ] Extraer `WikidataClient`
- [ ] Extraer `YouTubeClient`
- [ ] Extraer `SearchClient` (Perplexity/Google/DDG)
- [ ] Implementar `BiographyService`
- [ ] Implementar `FilmographyService`
- [ ] Implementar `Top10Service`
- [ ] Implementar `MarkdownGenerator`
- [ ] Escribir tests para cada cliente
- [ ] Escribir tests para cada servicio
- [ ] Configurar pre-commit hooks (ruff, black, mypy)
- [ ] Implementar esquema SQLite
- [ ] Implementar ETL Markdown → SQLite
- [ ] Implementar endpoints FastAPI
- [ ] Implementar autenticación JWT

### Frontend

- [ ] Inicializar Next.js 14 con App Router
- [ ] Configurar Tailwind con design tokens
- [ ] Instalar y configurar shadcn/ui
- [ ] Configurar next-intl
- [ ] Implementar Layout principal
- [ ] Implementar Header con navegación
- [ ] Implementar SearchBar
- [ ] Implementar ComposerCard
- [ ] Implementar ComposerGrid
- [ ] Implementar página Home
- [ ] Implementar página Listado
- [ ] Implementar página Detalle
- [ ] Implementar Top10Gallery
- [ ] Implementar FilmographyList
- [ ] Implementar AwardsList
- [ ] Implementar página Búsqueda
- [ ] Implementar dark mode
- [ ] Optimizar imágenes con next/image
- [ ] Tests con React Testing Library

---

**Documento generado**: 2026-02-03
**Versión**: 1.0
**Autor**: Claude (auditoría automática)
