# MUSIC_CRAWLER_TASKS.md - Lista Detallada de Tareas

**Control de Progreso del Módulo Music Crawler + Playlist Generator**
**Versión**: 1.0 | **Fecha**: 2026-02-05

---

> **IMPORTANTE**: Este documento debe mantenerse **SIEMPRE ACTUALIZADO** después de completar cada tarea.
> Marca las tareas completadas con `[x]` y añade la fecha de completado.

---

## Guía de Asignación de IAs

### Niveles de Esfuerzo (LOE)

| LOE | Descripción | Tiempo Est. | Modelo Recomendado |
|-----|-------------|-------------|-------------------|
| **L** (Low) | Tarea simple, mecánica | <30 min | `haiku` / `gpt-4o-mini` / `flash` |
| **M** (Medium) | Tarea estándar, algo de lógica | 30-90 min | `sonnet` / `gpt-4o` / `pro` |
| **H** (High) | Tarea compleja, arquitectura | >90 min | `opus` / `gpt-4o` / `pro` |

### Criterios de Selección de IA

| IA | Fortalezas | Cuándo Usar |
|----|------------|-------------|
| **Claude** | Arquitectura, refactoring, código complejo, razonamiento | Diseño de clases, lógica de negocio, algoritmos |
| **GPT** | Código general, scripts, documentación, tests | Scripts simples, tests unitarios, documentación |
| **Gemini** | Contexto largo, lectura masiva, resúmenes | Auditorías, análisis de código existente |
| **Codex/Copilot** | Autocompletado, snippets rápidos | Implementación directa de funciones |

### Regla de Cambio de IA

Cuando una tarea requiera una IA diferente a la actual:
1. **PARAR** el desarrollo
2. **AVISAR** al usuario qué IA debe usar
3. **INDICAR** el número de tarea y modelo recomendado

---

## Leyenda

- `[ ]` Pendiente
- `[x]` Completado
- `[~]` En progreso
- `[-]` Cancelado/No aplica

**Prioridad**: 🔴 Alta | 🟡 Media | 🟢 Baja

---

## Dependencias entre Fases

```
FASE 1 (Estabilización)
    ↓ bloquea
FASE 2 (SearchProvider)
    ↓ bloquea
FASE 3 (Integración SOUNDTRACKER)
    ↓ bloquea
FASE 4 (Playlist Generator)
    ↓ bloquea
FASE 5 (Tests + CI)
```

---

## FASE 1: Estabilización (2 días)

**Estado**: `[ ]` Pendiente
**Bloquea**: Fases 2, 3, 4, 5
**Directorio de trabajo**: `Music Crawler/`

### 1.1 Sistema de Logging

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 1.1.1 | Crear `src/core/logger.py` con configuración base de logging | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.1.2 | Definir formato de log: `[TIMESTAMP] [LEVEL] [MODULE] message` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.1.3 | Configurar niveles: DEBUG, INFO, WARNING, ERROR | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.1.4 | Añadir rotación de logs (max 5 archivos, 10MB cada uno) | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |
| 1.1.5 | Reemplazar todos los `print()` por `logger.info/debug` en `cli/crawl.py` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.1.6 | Reemplazar `print()` en `report/generator.py` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.1.7 | Reemplazar `print()` en `downloaders/ytdlp.py` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.1.8 | Buscar y eliminar TODOS los `except: pass` (grep recursivo) | M | Gemini | flash | 🔴 | `[x]` | 2026-02-05 |
| 1.1.9 | Reemplazar `except: pass` por `except Exception as e: logger.error(...)` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.1.10 | Añadir `exc_info=True` a todos los `logger.error` | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |

**Verificación 1.1**: `grep -r "print(" src/` debe devolver 0 resultados. `grep -r "except.*pass" src/` debe devolver 0 resultados.

---

### 1.2 Cache v2 con Estados y TTL

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 1.2.1 | Crear `src/cache/manager.py` con clase `CacheManager` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.2.2 | Definir schema de cache: `{query: {status, timestamp, path, url}}` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.3 | Implementar 5 estados: `downloaded`, `free_available`, `paid_only`, `not_found`, `error` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.2.4 | Añadir campo `timestamp` a cada entrada de cache | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.5 | Implementar `CACHE_TTL_DAYS` configurable (default: 7) | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.6 | Implementar método `is_expired(entry)` que compara timestamp | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.7 | Implementar método `get(query)` que respeta TTL | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.2.8 | Implementar método `set(query, status, path, url)` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.9 | Añadir flag `--refresh` al CLI que ignora cache | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.2.10 | Migrar `load_cache`/`save_cache` de `cli/crawl.py` a usar `CacheManager` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.2.11 | Eliminar código legacy de cache en `cli/crawl.py` | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |

**Verificación 1.2**: Test manual: ejecutar crawler, verificar que cache tiene timestamp y status correcto.

---

### 1.3 Filenames Seguros

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 1.3.1 | Modificar `Track.filename_base()` en `models/track.py` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 1.3.2 | Implementar truncado a 200 caracteres máximo | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.3.3 | Añadir hash MD5 (6 chars) al final si se trunca | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.3.4 | Sanitizar caracteres no permitidos en Windows/Linux | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |
| 1.3.5 | Añadir test unitario para filenames largos (>200 chars) | L | GPT | 4o-mini | 🟡 | `[x]` | 2026-02-05 |
| 1.3.6 | Añadir test unitario para filenames con caracteres especiales | L | GPT | 4o-mini | 🟡 | `[x]` | 2026-02-05 |

**Código esperado**:
```python
import hashlib

def filename_base(self) -> str:
    safe_film = "".join(c if c.isalnum() or c in " -" else "_" for c in self.film)
    safe_title = "".join(c if c.isalnum() or c in " -" else "_" for c in self.cue_title)
    full_name = f"{self.rank:02d}_{safe_film}_{safe_title}".lower().replace(" ", "_")
    if len(full_name) > 200:
        hash_suffix = hashlib.md5(full_name.encode()).hexdigest()[:6]
        return f"{full_name[:193]}_{hash_suffix}"
    return full_name
```

---

### 1.4 Fix Reporte (Conteos No Duplicados)

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 1.4.1 | Analizar `_format_sources_summary()` en `report/generator.py` | L | Gemini | flash | 🟡 | `[x]` | 2026-02-05 |
| 1.4.2 | Identificar bug: downloaded_from se cuenta doble | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |
| 1.4.3 | Fix: excluir downloaded_from de free_alternatives antes de contar | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 1.4.4 | Añadir test unitario para verificar conteos correctos | L | GPT | 4o-mini | 🟢 | `[x]` | 2026-02-05 |

---

### 1.5 Configuración del Proyecto

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 1.5.1 | Cambiar `requires-python` de `>=3.12` a `>=3.11` en `pyproject.toml` | L | GPT | 4o-mini | 🔴 | `[x]` | 2026-02-05 |
| 1.5.2 | Añadir `python-dotenv` a dependencias si no está | L | GPT | 4o-mini | 🔴 | `[x]` | 2026-02-05 |
| 1.5.3 | Añadir `load_dotenv()` al inicio de `cli/crawl.py` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 1.5.4 | Crear `src/core/config.py` con pydantic-settings | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 1.5.5 | Definir `Settings` class con todas las variables de entorno | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 1.5.6 | Migrar constantes hardcodeadas a Settings | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |

**Checkpoint Fase 1**: `[x]` Completada (2026-02-05)

---

## FASE 2: SearchProvider (3 días)

**Estado**: `[ ]` Pendiente
**Requiere**: Fase 1 completada
**Bloquea**: Fases 3, 4, 5
**Directorio de trabajo**: `Music Crawler/`

### 2.1 Abstracción SearchProvider

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 2.1.1 | Crear `src/providers/__init__.py` | L | GPT | 4o-mini | 🔴 | `[x]` | 2026-02-05 |
| 2.1.2 | Crear `src/providers/base.py` con ABC `SearchProvider` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.1.3 | Definir método abstracto `search_urls(query, num_results, site_filter) -> list[str]` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 2.1.4 | Añadir método `get_rate_limit() -> float` (segundos entre requests) | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 2.1.5 | Añadir método `get_name() -> str` | L | Claude | haiku | 🟢 | `[x]` | 2026-02-05 |

**Código esperado**:
```python
from abc import ABC, abstractmethod

class SearchProvider(ABC):
    @abstractmethod
    def search_urls(self, query: str, num_results: int = 5, site_filter: str | None = None) -> list[str]:
        """Search and return list of URLs."""
        pass

    @abstractmethod
    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        pass

    def get_name(self) -> str:
        return self.__class__.__name__
```

---

### 2.2 PerplexityProvider (Preferente)

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 2.2.1 | Crear `src/providers/perplexity.py` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.2.2 | Implementar `PerplexityProvider(SearchProvider)` | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.2.3 | Leer `PPLX_API_KEY` desde environment | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 2.2.4 | Implementar llamada a Perplexity API para búsqueda web | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.2.5 | Parsear respuesta y extraer URLs | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.2.6 | Rate limit: 0.5 segundos (API es más tolerante) | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |
| 2.2.7 | Manejo de errores: API key inválida, rate limit, timeout | M | Claude | sonnet | 🔴 | `[x]` | 2026-02-05 |
| 2.2.8 | Crear test con mock de API response | M | GPT | 4o | 🟡 | `[x]` | 2026-02-05 |

---

### 2.3 DuckDuckGoProvider (Fallback)

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 2.3.1 | Crear `src/providers/duckduckgo.py` | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 2.3.2 | Extraer lógica de scraping DDG de searchers existentes | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 2.3.3 | Implementar `DuckDuckGoProvider(SearchProvider)` | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 2.3.4 | Rate limit: 2.0 segundos (scraping requiere más cuidado) | L | Claude | haiku | 🟡 | `[x]` | 2026-02-05 |
| 2.3.5 | Añadir `logger.warning("Using DuckDuckGo fallback...")` | L | Claude | haiku | 🔴 | `[x]` | 2026-02-05 |
| 2.3.6 | Manejo de errores: HTML cambiado, blocked, timeout | M | Claude | sonnet | 🟡 | `[x]` | 2026-02-05 |
| 2.3.7 | Crear test con mock de HTML response | M | GPT | 4o | 🟡 | `[x]` | 2026-02-05 |

---

### 2.4 Refactor Searchers Web

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 2.4.1 | Listar todos los searchers que usan DDG scraping | L | Gemini | flash | 🔴 | `[ ]` | |
| 2.4.2 | Modificar `SpotifySearcher` para usar `SearchProvider` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.4.3 | Modificar `AmazonSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.4.4 | Modificar `SoundCloudSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.4.5 | Modificar `BandcampSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.4.6 | Modificar `TidalSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.4.7 | Modificar `QobuzSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🟡 | `[ ]` | |
| 2.4.8 | Modificar `JamendoSearcher` para usar `SearchProvider` | M | Claude | sonnet | 🟡 | `[ ]` | |
| 2.4.9 | Modificar `FMASearcher` para usar `SearchProvider` | M | Claude | sonnet | 🟡 | `[ ]` | |
| 2.4.10 | Eliminar código duplicado de scraping en cada searcher | M | Claude | sonnet | 🔴 | `[ ]` | |

**Patrón de refactor**:
```python
class SpotifySearcher(BaseSearcher):
    def __init__(self, provider: SearchProvider, max_results: int = 2):
        self.provider = provider
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        query = self.build_query(track)
        urls = self.provider.search_urls(query, self.max_results, site_filter="spotify.com")
        return [self._parse_spotify_url(url, track) for url in urls]
```

---

### 2.5 Rate Limiting y Backoff

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 2.5.1 | Crear `src/core/rate_limiter.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.5.2 | Implementar clase `RateLimiter` con per-provider limits | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.5.3 | Implementar exponential backoff para errores 429/5xx | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.5.4 | Config: max_retries=3, initial_delay=1s, max_delay=30s | L | Claude | haiku | 🟡 | `[ ]` | |
| 2.5.5 | Integrar RateLimiter en SearchProvider base | M | Claude | sonnet | 🔴 | `[ ]` | |
| 2.5.6 | Crear test para backoff con mock de respuestas 429 | M | GPT | 4o | 🟡 | `[ ]` | |

**Checkpoint Fase 2**: `[ ]` Completada

---

## FASE 3: Integración SOUNDTRACKER (3 días)

**Estado**: `[ ]` Pendiente
**Requiere**: Fase 2 completada
**Bloquea**: Fases 4, 5
**Directorio de trabajo**: `App/`

### 3.1 Wrapper Script

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.1.1 | Crear `App/scripts/music_crawler_batch.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.1.2 | Implementar CLI con argparse: `--composer`, `--all`, `--playlist-only` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.1.3 | Implementar conexión a `soundtrackers.db` | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.1.4 | Implementar query para obtener Top 10 films de un compositor | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.1.5 | Generar `track_list.txt` temporal desde resultados de query | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.1.6 | Ejecutar Music Crawler via `subprocess.run` desde su directorio | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.1.7 | Pasar env vars: `PPLX_API_KEY` al subprocess | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.1.8 | Definir output dir: `App/data/music_crawler/{slug}/` | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.1.9 | Capturar y loggear stdout/stderr del subprocess | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.1.10 | Manejar errores de subprocess (returncode != 0) | L | Claude | haiku | 🟡 | `[ ]` | |

---

### 3.2 Generar track_list.txt desde DB

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.2.1 | Definir query SQL para Top 10 films por compositor (ordenados por score) | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.2.2 | Extraer: rank, film_title, cue_title (Main Title por defecto) | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.2.3 | Formatear en formato de track_list.txt que Music Crawler espera | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.2.4 | Guardar en archivo temporal (tempfile.NamedTemporaryFile) | L | Claude | haiku | 🟡 | `[ ]` | |

---

### 3.3 Output JSON y Report

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.3.1 | Modificar Music Crawler para generar `results.json` además de `REPORT.md` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.3.2 | Definir schema de `results.json` compatible con ETL | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.3.3 | Incluir: track_info, status, source, url, local_path, alternatives | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.3.4 | Añadir flag `--json` al CLI de Music Crawler | L | Claude | haiku | 🟡 | `[ ]` | |

---

### 3.4 ETL: results.json → DB

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.4.1 | Crear `App/scripts/etl_music.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.4.2 | Leer `results.json` de directorio de compositor | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.4.3 | Mapear campos a tabla `music_tracks` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.4.4 | Buscar `composer_id` por slug | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.4.5 | Buscar `film_id` por título (si existe) | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.4.6 | Implementar UPSERT (INSERT OR REPLACE) | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.4.7 | Actualizar `updated_at` en cada insert | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.4.8 | Integrar ETL en `music_crawler_batch.py` (ejecutar después de crawler) | L | Claude | haiku | 🔴 | `[ ]` | |

---

### 3.5 Schema SQL

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.5.1 | Crear `App/scripts/schema_music.sql` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.5.2 | Definir tabla `music_tracks` según MUSIC_CRAWLER_DEFINITIVE.md | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.5.3 | Definir tabla `composer_playlists` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.5.4 | Definir tabla `playlist_tracks` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.5.5 | Crear índices para queries frecuentes | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.5.6 | Ejecutar schema en `soundtrackers.db` | L | GPT | 4o-mini | 🔴 | `[ ]` | |

---

### 3.6 API Endpoint /music

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.6.1 | Crear `App/backend/app/services/music_service.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.6.2 | Implementar `get_tracks_by_composer(slug, status)` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.6.3 | Crear `App/backend/app/routers/music.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.6.4 | Implementar `GET /api/composers/{slug}/music` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.6.5 | Añadir router a `main.py` | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.6.6 | Crear modelo Pydantic para response | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.6.7 | Añadir tests para endpoint | M | GPT | 4o | 🟡 | `[ ]` | |

---

### 3.7 Actualizar .gitignore

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.7.1 | Añadir `App/data/music_crawler/*/downloads/` a `.gitignore` | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 3.7.2 | Verificar que `results.json` y `playlist.json` NO están ignorados | L | GPT | 4o-mini | 🟡 | `[ ]` | |

---

### 3.8 Sync Engine (Nuevos Compositores)

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 3.8.1 | Implementar `get_pending_composers(db_path)` en batch script | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.8.2 | Implementar `get_outdated_composers(db_path, days)` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.8.3 | Añadir flag `--pending` para listar compositores sin playlist | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.8.4 | Añadir flag `--outdated --days N` para listar desactualizados | L | Claude | haiku | 🔴 | `[ ]` | |
| 3.8.5 | Añadir flag `--sync-new` para procesar solo pendientes | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.8.6 | Añadir flag `--sync-outdated` para procesar solo viejos | M | Claude | sonnet | 🟡 | `[ ]` | |
| 3.8.7 | Añadir flag `--sync-all` para procesar todos | M | Claude | sonnet | 🔴 | `[ ]` | |
| 3.8.8 | Añadir flag `--force` para ignorar cache y regenerar | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.8.9 | Implementar loop de procesamiento batch con progress bar | M | Claude | sonnet | 🟡 | `[ ]` | |
| 3.8.10 | Añadir flag `--commit` para auto-commit de cambios | L | Claude | haiku | 🟢 | `[ ]` | |
| 3.8.11 | Logging de operaciones sync (compositores procesados, errores) | L | Claude | haiku | 🟡 | `[ ]` | |
| 3.8.12 | Crear tabla `music_crawler_runs` para tracking (opcional) | M | Claude | sonnet | 🟢 | `[ ]` | |

**Checkpoint Fase 3**: `[ ]` Completada

---

## FASE 4: Playlist Generator (4 días)

**Estado**: `[ ]` Pendiente
**Requiere**: Fase 3 completada
**Bloquea**: Fase 5
**Directorio de trabajo**: `Music Crawler/` y `App/`

### 4.1 CLI Command playlist

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.1.1 | Añadir subcommand `playlist` al CLI de Music Crawler | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.1.2 | Argumentos: `--composer`, `--db-path`, `--output` | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.1.3 | Validar que composer existe en DB | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.1.4 | Cargar Top 10 films desde DB | M | Claude | sonnet | 🔴 | `[ ]` | |

---

### 4.2 PlaylistGenerator Class

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.2.1 | Crear `src/playlist/__init__.py` | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 4.2.2 | Crear `src/playlist/models.py` con `Playlist`, `PlaylistTrack` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.2.3 | Crear `src/playlist/generator.py` con clase `PlaylistGenerator` | H | Claude | opus | 🔴 | `[ ]` | |
| 4.2.4 | Implementar `__init__(composer_slug, db_path, searchers)` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.2.5 | Implementar `_get_top_films()` - obtiene Top 10 del compositor | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.2.6 | Implementar `_get_popular_track(film)` - identifica track principal | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.2.7 | Implementar `_search_free_source(track)` - busca en fuentes gratuitas | H | Claude | opus | 🔴 | `[ ]` | |
| 4.2.8 | Implementar `SourcePriority` enum (YouTube=100, SoundCloud=90, etc.) | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.2.9 | Implementar `_get_alternative_tracks(film)` - otros tracks de la BSO | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.2.10 | Implementar `_find_playable_track(film, position)` con fallback completo | H | Claude | opus | 🔴 | `[ ]` | |
| 4.2.11 | Implementar `generate()` - orquesta todo y retorna Playlist | H | Claude | opus | 🔴 | `[ ]` | |
| 4.2.12 | Implementar `_get_purchase_links(track)` - iTunes, Amazon, Bandcamp | M | Claude | sonnet | 🟡 | `[ ]` | |

**Algoritmo de Fallback** (implementar en 4.2.10):
```
1. Track popular → buscar link gratis (YouTube > SoundCloud > Archive)
2. Si no hay gratis → buscar track alternativo de misma BSO
3. Si ninguno gratis → marcar paid_only + purchase_links
4. Si todo falla → log warning y skip
```

---

### 4.3 Embed URL Resolver

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.3.1 | Crear `src/playlist/embed.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.3.2 | Implementar `EmbedResolver.resolve(source, url) -> embed_url` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.3.3 | Implementar `_youtube_embed(url)` - extraer video_id y generar embed | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.3.4 | Implementar `_soundcloud_embed(url)` - widget player URL | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.3.5 | Implementar `_spotify_embed(url)` - embed track URL | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.3.6 | Manejar URLs inválidas o no soportadas (return None) | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.3.7 | Crear tests unitarios para cada resolver | M | GPT | 4o | 🟡 | `[ ]` | |

---

### 4.4 Output playlist.json

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.4.1 | Definir schema JSON según MUSIC_CRAWLER_DEFINITIVE.md | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.4.2 | Implementar `Playlist.to_json()` method | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.4.3 | Incluir metadata: generated_at, updated_at, free_count, paid_count | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.4.4 | Guardar en `{output_dir}/playlist.json` | L | Claude | haiku | 🔴 | `[ ]` | |

---

### 4.5 ETL playlist.json → DB

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.5.1 | Crear `App/scripts/etl_playlist.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.5.2 | Leer `playlist.json` de directorio de compositor | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.5.3 | UPSERT en tabla `composer_playlists` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.5.4 | DELETE + INSERT en tabla `playlist_tracks` (reemplazar todos) | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.5.5 | Integrar en `music_crawler_batch.py` | L | Claude | haiku | 🔴 | `[ ]` | |

---

### 4.6 API Endpoint /playlist

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.6.1 | Crear `App/backend/app/services/playlist_service.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.6.2 | Implementar `get_playlist_by_composer(slug)` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.6.3 | Añadir endpoint `GET /api/composers/{slug}/playlist` a `music.py` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.6.4 | Añadir endpoint `POST /api/composers/{slug}/playlist/refresh` | M | Claude | sonnet | 🟡 | `[ ]` | |
| 4.6.5 | Crear modelos Pydantic para response | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.6.6 | Añadir tests para endpoints | M | GPT | 4o | 🟡 | `[ ]` | |

---

### 4.7 Frontend: PlaylistPlayer Component

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.7.1 | Crear `App/frontend/src/components/PlaylistPlayer.tsx` | H | Claude | opus | 🔴 | `[ ]` | |
| 4.7.2 | Definir interfaces TypeScript para `PlaylistTrack`, `Playlist` | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.7.3 | Implementar estado: `currentTrack`, `isPlaying` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.7.4 | Implementar embed iframe para YouTube | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.7.5 | Implementar embed iframe para SoundCloud | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.7.6 | Implementar fallback UI para paid tracks (purchase links) | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.7.7 | Implementar lista de tracks con onClick navigation | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.7.8 | Añadir indicador visual para track activo | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.7.9 | Añadir badge para tracks de pago ($) | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.7.10 | Añadir thumbnails desde YouTube API | M | Claude | sonnet | 🟢 | `[ ]` | |
| 4.7.11 | Estilos Tailwind responsive | M | Claude | sonnet | 🟡 | `[ ]` | |

---

### 4.8 Frontend: Página /playlist

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.8.1 | Crear `App/frontend/src/app/composers/[slug]/playlist/page.tsx` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.8.2 | Implementar fetch de playlist desde API | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.8.3 | Renderizar `<PlaylistPlayer />` con datos | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.8.4 | Manejar estado loading y error | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.8.5 | Añadir metadata SEO (title, description) | L | Claude | haiku | 🟢 | `[ ]` | |

---

### 4.9 Integración en Ficha Compositor

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 4.9.1 | Modificar `App/frontend/src/app/composers/[slug]/page.tsx` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.9.2 | Añadir fetch de playlist en getServerSideProps/fetch | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.9.3 | Añadir sección "🎵 Escucha sus mejores temas" | M | Claude | sonnet | 🔴 | `[ ]` | |
| 4.9.4 | Renderizar `<PlaylistPlayer />` inline | L | Claude | haiku | 🔴 | `[ ]` | |
| 4.9.5 | Añadir stats: "X tracks gratuitos, Y de pago" | L | Claude | haiku | 🟡 | `[ ]` | |
| 4.9.6 | Añadir link a página standalone `/playlist` | L | Claude | haiku | 🟢 | `[ ]` | |

**Checkpoint Fase 4**: `[ ]` Completada

---

## FASE 5: Tests + CI (2 días)

**Estado**: `[ ]` Pendiente
**Requiere**: Fase 4 completada
**Directorio de trabajo**: `Music Crawler/` y `App/`

### 5.1 Tests Searchers

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.1.1 | Crear `Music Crawler/tests/test_searchers.py` | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.1.2 | Mock de `SearchProvider.search_urls()` | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.1.3 | Mock de `requests.get()` para parsing | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.1.4 | Test `YouTubeSearcher` con mock | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.1.5 | Test `SpotifySearcher` con mock | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.1.6 | Test al menos 5 searchers más | M | GPT | 4o | 🟡 | `[ ]` | |

---

### 5.2 Tests Cache

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.2.1 | Crear `Music Crawler/tests/test_cache.py` | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.2.2 | Test: set/get básico | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.2.3 | Test: TTL expiration | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.2.4 | Test: 5 estados diferentes | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.2.5 | Test: --refresh flag ignora cache | L | GPT | 4o-mini | 🟡 | `[ ]` | |

---

### 5.3 Tests ETL

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.3.1 | Crear `App/tests/test_etl_music.py` | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.3.2 | Test: parse results.json válido | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.3.3 | Test: insert en DB (SQLite in-memory) | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.3.4 | Test: upsert no duplica | M | GPT | 4o | 🟡 | `[ ]` | |

---

### 5.4 Tests PlaylistGenerator

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.4.1 | Crear `Music Crawler/tests/test_playlist.py` | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.4.2 | Mock de DB con Top 10 films | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.4.3 | Mock de searchers | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.4.4 | Test: track popular encontrado gratis | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.4.5 | Test: fallback a track alternativo | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.4.6 | Test: paid_only con purchase_links | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.4.7 | Test: EmbedResolver para YouTube | L | GPT | 4o-mini | 🟡 | `[ ]` | |
| 5.4.8 | Test: EmbedResolver para SoundCloud | L | GPT | 4o-mini | 🟡 | `[ ]` | |

---

### 5.5 Tests API Playlist

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.5.1 | Crear `App/backend/tests/test_music_router.py` | M | GPT | 4o | 🔴 | `[ ]` | |
| 5.5.2 | Test: GET /music con compositor válido | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.5.3 | Test: GET /playlist con compositor válido | L | GPT | 4o-mini | 🔴 | `[ ]` | |
| 5.5.4 | Test: 404 para compositor inexistente | L | GPT | 4o-mini | 🟡 | `[ ]` | |

---

### 5.6 CI Job

| # | Tarea | LOE | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|-----|--------|-----------|--------|-------|
| 5.6.1 | Crear/modificar `.github/workflows/ci.yml` | M | Claude | sonnet | 🔴 | `[ ]` | |
| 5.6.2 | Añadir job separado para Music Crawler tests | L | Claude | haiku | 🔴 | `[ ]` | |
| 5.6.3 | Configurar Python 3.11, instalar deps, pytest | L | Claude | haiku | 🔴 | `[ ]` | |
| 5.6.4 | Añadir badge de CI al README | L | GPT | 4o-mini | 🟢 | `[ ]` | |

**Checkpoint Fase 5**: `[ ]` Completada

---

## Resumen de Tareas por Fase

| Fase | Tareas | LOE Total Est. | Días |
|------|--------|----------------|------|
| 1. Estabilización | 33 | ~16h | 2 |
| 2. SearchProvider | 28 | ~24h | 3 |
| 3. Integración | 30 | ~24h | 3 |
| 4. Playlist Generator | 46 | ~32h | 4 |
| 5. Tests + CI | 26 | ~16h | 2 |
| **TOTAL** | **163** | **~112h** | **14** |

---

## Verificación Final

### Checklist Pre-Deploy

- [ ] `grep -r "print(" "Music Crawler/src/"` devuelve 0 resultados
- [ ] `grep -r "except.*pass" "Music Crawler/src/"` devuelve 0 resultados
- [ ] `pytest "Music Crawler/tests/"` pasa al 100%
- [ ] `pytest "App/tests/"` pasa al 100%
- [ ] API `/api/composers/john_williams/playlist` devuelve datos válidos
- [ ] Frontend muestra PlaylistPlayer con embeds funcionales
- [ ] `downloads/` no está en git (`git status` limpio)
- [ ] CI verde en GitHub Actions

---

**Documento creado**: 2026-02-05
**Última actualización**: 2026-02-05
**Versión**: 1.0
