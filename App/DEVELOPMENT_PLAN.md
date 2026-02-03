# Plan de Desarrollo - SOUNDTRACKER

**Versión**: 2.0 | **Actualizado**: 2026-02-03

> Este documento define el roadmap completo para transformar SOUNDTRACKER de un pipeline de generación de datos a una aplicación web completa.

---

## 1. Visión del Proyecto

### 1.1 Estado Actual
- Pipeline Python funcional (1,968 líneas en archivo monolítico)
- 164 compositores documentados con biografía, filmografía, Top 10 y premios
- ~970 MB de datos (Markdown + pósters)
- Integración con TMDB, Wikipedia, Wikidata, YouTube, Perplexity

### 1.2 Estado Objetivo
- **Backend**: FastAPI + SQLite (FTS5) con API REST documentada
- **Frontend**: Next.js 14 + Tailwind + shadcn/ui
- **Pipeline**: Código modular, testeable y mantenible
- **Datos**: Base de datos estructurada con búsqueda full-text

---

## 2. Arquitectura

### 2.1 Stack Tecnológico

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| **Pipeline** | Python 3.11+ | Continuidad con código existente |
| **Backend** | FastAPI | Async, tipado, OpenAPI automático |
| **Base de datos** | SQLite + FTS5 | Portable, versionable, sin servidor |
| **Frontend** | Next.js 14 | App Router, RSC, optimización de imágenes |
| **Estilos** | Tailwind CSS | Utilidades, design tokens, responsive |
| **Componentes** | shadcn/ui | Accesibles, personalizables |
| **i18n** | next-intl | ES (principal), EN (secundario) |

### 2.2 Estructura de Directorios (Objetivo)

```
App/
├── src/                          # Código fuente Python refactorizado
│   └── soundtracker/
│       ├── __init__.py
│       ├── config.py             # Configuración centralizada
│       ├── models.py             # Dataclasses/Pydantic
│       ├── clients/              # Clientes de APIs
│       │   ├── tmdb.py
│       │   ├── wikipedia.py
│       │   ├── wikidata.py
│       │   ├── youtube.py
│       │   └── search.py
│       ├── services/             # Lógica de negocio
│       │   ├── biography.py
│       │   ├── filmography.py
│       │   ├── top10.py
│       │   └── awards.py
│       ├── generators/           # Generación de salidas
│       │   └── markdown.py
│       └── cache/                # Sistema de caché
│           └── file_cache.py
├── backend/                      # API FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── services/
│   └── tests/
├── frontend/                     # Next.js
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── public/
├── scripts/                      # Scripts de orquestación
│   ├── create_composer_files.py  # Refactorizado (~50 líneas)
│   ├── build_database.py         # ETL Markdown → SQLite
│   └── update_top10.py
├── tests/                        # Tests del pipeline
├── outputs/                      # Datos generados (existente)
├── data/                         # Base de datos SQLite
│   └── soundtrackers.db
├── pyproject.toml
├── AGENTS.md
├── CONVENTIONS.md
├── CONVENTIONS_FRONTEND.md
└── README.md
```

---

## 3. Esquema de Base de Datos

### 3.1 Tablas Principales

```sql
-- Compositores
CREATE TABLE composers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    photo_path TEXT,
    biography_es TEXT,
    style_es TEXT,
    anecdotes_es TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Películas
CREATE TABLE films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id),
    title_original TEXT NOT NULL,
    title_es TEXT,
    year INTEGER,
    poster_path TEXT,
    is_top10 INTEGER DEFAULT 0,
    top10_rank INTEGER,
    tmdb_popularity REAL,
    tmdb_vote_count INTEGER,
    tmdb_vote_average REAL,
    youtube_views INTEGER,
    score REAL
);

-- Premios
CREATE TABLE awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id),
    award_name TEXT NOT NULL,
    year INTEGER,
    film_title TEXT,
    status TEXT CHECK(status IN ('Win', 'Nomination'))
);

-- Fuentes externas
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id),
    source_name TEXT NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT
);

-- FTS5 para búsqueda full-text
CREATE VIRTUAL TABLE fts_composers USING fts5(
    name,
    biography_es,
    style_es,
    film_titles,
    award_names,
    tokenize='porter unicode61'
);
```

### 3.2 Vista de Estadísticas

```sql
CREATE VIEW v_composer_stats AS
SELECT
    c.id, c.name, c.slug, c.photo_path,
    COUNT(DISTINCT f.id) as film_count,
    COUNT(DISTINCT CASE WHEN a.status = 'Win' THEN a.id END) as wins,
    COUNT(DISTINCT CASE WHEN a.status = 'Nomination' THEN a.id END) as nominations,
    MIN(f.year) as career_start,
    MAX(f.year) as career_end
FROM composers c
LEFT JOIN films f ON f.composer_id = c.id
LEFT JOIN awards a ON a.composer_id = c.id
GROUP BY c.id;
```

---

## 4. API Backend

### 4.1 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/composers` | Lista paginada con filtros |
| GET | `/api/composers/{slug}` | Detalle completo |
| GET | `/api/composers/{slug}/filmography` | Filmografía paginada |
| GET | `/api/composers/{slug}/awards` | Premios |
| GET | `/api/search` | Búsqueda FTS5 |
| GET | `/api/films` | Lista de películas |
| GET | `/api/assets/{path}` | Servir pósters |

### 4.2 Filtros Soportados

```
GET /api/composers?
  page=1&
  per_page=20&
  sort_by=name|film_count|wins&
  order=asc|desc&
  has_awards=true&
  decade=1980&
  q=williams
```

---

## 5. Frontend

### 5.1 Páginas

| Ruta | Descripción |
|------|-------------|
| `/` | Home con buscador y compositores destacados |
| `/composers` | Listado con filtros y paginación |
| `/composers/[slug]` | Detalle: bio, Top 10, filmografía, premios |
| `/search` | Búsqueda avanzada con facetas |

### 5.2 Componentes Principales

- **ComposerCard**: Tarjeta con foto, nombre, stats
- **ComposerGrid**: Grid responsivo de tarjetas
- **ComposerDetail**: Página de detalle completa
- **Top10Gallery**: Galería de pósters con modal
- **FilmographyList**: Lista paginada con pósters
- **AwardsList**: Premios con badges
- **SearchBar**: Buscador con autocompletado
- **FilterPanel**: Filtros de búsqueda

### 5.3 Design System

**Paleta de colores** (cinematográfica cálida):
- Primary: `#C96A40` (terracota)
- Secondary: `#5A7499` (azul grisáceo)
- Accent Gold: `#D4AF37` (premios)

**Tipografía**:
- Display: Playfair Display (títulos)
- Body: Inter (texto)

---

## 6. Roadmap de Implementación

### Fase 0: Preparación (1-2 días)

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| Medir tamaño real de outputs | Alta | Pendiente |
| Evaluar necesidad de Git LFS | Alta | Pendiente |
| Crear pyproject.toml | Media | Pendiente |
| Configurar pre-commit hooks | Media | Pendiente |

**Entregables**:
- Decisión sobre Git LFS
- pyproject.toml configurado
- .pre-commit-config.yaml

### Fase 1: Refactorización Python (5-7 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Crear modelos de datos | Alta | 1 día |
| Extraer TMDBClient | Alta | 1 día |
| Extraer WikipediaClient | Alta | 0.5 días |
| Extraer WikidataClient | Alta | 0.5 días |
| Extraer YouTubeClient | Media | 0.5 días |
| Extraer SearchClient | Alta | 0.5 días |
| Extraer servicios de negocio | Alta | 1.5 días |
| Implementar logging estructurado | Media | 0.5 días |
| Tests unitarios (50%+ cobertura) | Alta | 2 días |

**Entregables**:
- `src/soundtracker/` con módulos separados
- `tests/` con cobertura >50%
- `scripts/create_composer_files.py` refactorizado (<100 líneas)

### Fase 2: Base de Datos + ETL (3-4 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Implementar esquema SQLite | Alta | 0.5 días |
| Implementar FTS5 | Alta | 0.5 días |
| Desarrollar parser de Markdown | Alta | 1.5 días |
| Script ETL completo | Alta | 1 día |
| Validación de integridad | Media | 0.5 días |

**Entregables**:
- `data/soundtrackers.db` con 164 compositores
- `scripts/build_database.py`
- Tests de integridad

### Fase 3: Backend API (4-5 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Setup FastAPI | Alta | 0.5 días |
| Endpoints de compositores | Alta | 1.5 días |
| Endpoint de búsqueda FTS5 | Alta | 1 día |
| Servir assets (pósters) | Alta | 0.5 días |
| Autenticación JWT (opcional) | Baja | 1 día |
| Tests de API | Media | 1 día |

**Entregables**:
- `backend/` con API funcional
- Documentación OpenAPI automática
- Tests de integración

### Fase 4: Frontend Base (5-7 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Setup Next.js + Tailwind | Alta | 0.5 días |
| Configurar shadcn/ui | Alta | 0.5 días |
| Design tokens en Tailwind | Alta | 0.5 días |
| Layout principal | Alta | 1 día |
| Página Home | Alta | 1 día |
| Listado de compositores | Alta | 1.5 días |
| Configurar i18n (ES/EN) | Media | 1 día |

**Entregables**:
- `frontend/` con Home y Listado
- Responsive mobile-first
- i18n configurado

### Fase 5: Frontend Avanzado (7-10 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Página de detalle | Alta | 2 días |
| Galería Top 10 | Alta | 1.5 días |
| Filmografía con paginación | Alta | 1.5 días |
| Lista de premios | Media | 1 día |
| Búsqueda con filtros | Alta | 2 días |
| Dark mode | Media | 1 día |
| Optimización de imágenes | Media | 1 día |

**Entregables**:
- Frontend completo
- Dark mode funcional
- Imágenes optimizadas

### Fase 6: Deploy y CI/CD (2-3 días)

| Tarea | Prioridad | Estimación |
|-------|-----------|------------|
| Dockerizar backend | Alta | 0.5 días |
| Dockerizar frontend | Alta | 0.5 días |
| docker-compose | Alta | 0.5 días |
| Script de deploy | Alta | 0.5 días |
| GitHub Actions CI | Media | 1 día |

**Entregables**:
- Dockerfiles
- docker-compose.yml
- .github/workflows/ci.yml

---

## 7. Estimación Total

| Fase | Duración | Acumulado |
|------|----------|-----------|
| Fase 0: Preparación | 1-2 días | 2 días |
| Fase 1: Refactorización | 5-7 días | 9 días |
| Fase 2: Base de datos | 3-4 días | 13 días |
| Fase 3: Backend | 4-5 días | 18 días |
| Fase 4: Frontend base | 5-7 días | 25 días |
| Fase 5: Frontend avanzado | 7-10 días | 35 días |
| Fase 6: Deploy | 2-3 días | 38 días |

**Total estimado**: 27-38 días laborables

---

## 8. Decisión: Git vs Git LFS

> **Análisis realizado**: 2026-02-03 | **Decisión**: ✅ Git estándar (sin LFS)

### Resultados del Análisis

| Métrica | Valor |
|---------|-------|
| Tamaño total `outputs/` | **970 MB** |
| Archivos JPG (pósters) | 12,680 |
| Archivos MD | 172 |
| Archivos JSON (cachés) | 2 |
| Archivos >100MB | **0** |
| Tamaño promedio JPG | ~76 KB |

### Decisión

**Git estándar** (sin Git LFS) es suficiente porque:

1. **Ningún archivo supera 100MB** (límite de GitHub)
2. **Pósters son pequeños** (~76KB promedio)
3. **Regenerables**: Los pósters pueden regenerarse ejecutando el pipeline
4. **Simplicidad**: Git LFS añade complejidad innecesaria

### Recomendaciones

- ✅ Mantener `outputs/` en Git estándar
- ✅ Añadir `outputs/` a `.gitignore` si el repo se hace público (datos regenerables)
- ⚠️ Revisar si el repo crece significativamente (>2GB)

---

## 9. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Pósters exceden límites de Git | ~~Alta~~ **Baja** | Alto | ✅ Análisis confirma: sin archivos >100MB |
| APIs externas cambian | Media | Medio | Caché agresivo + fallbacks |
| FTS5 lento con datos grandes | Baja | Medio | Índices optimizados + límites |
| Refactorización introduce bugs | Media | Alto | Tests antes de migrar |
| Credenciales Spotify no disponibles | Alta | Bajo | YouTube como único streaming |

---

## 9. Criterios de Éxito

### Código
- [ ] 100% archivos < 1,000 líneas
- [ ] Cobertura tests > 70%
- [ ] `ruff` sin warnings
- [ ] `mypy --strict` sin errores

### Datos
- [ ] 164 compositores en SQLite
- [ ] Búsqueda FTS5 < 100ms
- [ ] Pósters servidos correctamente

### Frontend
- [ ] Lighthouse Performance > 90
- [ ] Lighthouse Accessibility > 95
- [ ] Responsive en móvil/tablet/desktop
- [ ] Dark mode funcional

### Deploy
- [ ] Docker build exitoso
- [ ] CI/CD configurado
- [ ] Documentación API generada

---

## 10. Control de Progreso

> **IMPORTANTE**: El progreso del desarrollo se controla en `TASKS.md`.
> Este archivo debe mantenerse **SIEMPRE ACTUALIZADO** después de cada tarea completada.

Ver `TASKS.md` para:
- Lista detallada de 229 tareas numeradas
- Asignación de IA óptima para cada tarea (Claude, GPT, Gemini, Perplexity)
- Modelo recomendado para minimizar costes
- Checklist de progreso por fase

---

## 11. Documentación Relacionada

| Documento | Propósito |
|-----------|-----------|
| `TASKS.md` | **Lista de tareas con checklist** (control de progreso) |
| `AGENTS.md` | Protocolo operativo para agentes IA |
| `CONVENTIONS.md` | Estándares de código Python |
| `CONVENTIONS_FRONTEND.md` | Estándares de código frontend |
| `AUDIT_AND_PROPOSAL.md` | Auditoría técnica detallada |
| `README.md` | Documentación de usuario |

---

**Última actualización**: 2026-02-03
**Versión**: 2.0
