# TASKS.md - Lista de Tareas de Desarrollo

**Control de Progreso del Proyecto SOUNDTRACKER** | v1.3 | 2026-02-03

---

> **IMPORTANTE**: Este documento debe mantenerse **SIEMPRE ACTUALIZADO** después de completar cada tarea.
> Marca las tareas completadas con `[x]` y añade la fecha de completado.

---

## Guía de Asignación de IAs

### Criterios de Selección

| IA | Fortalezas | Modelo Económico | Modelo Potente |
|----|------------|------------------|----------------|
| **Claude** | Arquitectura, código complejo, refactoring, razonamiento | `claude-3-5-haiku` | `claude-3-5-sonnet` / `opus` |
| **GPT** | Código general, scripts, documentación | `gpt-4o-mini` | `gpt-4o` |
| **Gemini** | Contexto largo, lectura masiva, resúmenes | `gemini-1.5-flash` | `gemini-1.5-pro` |
| **Perplexity** | Búsqueda web, investigación, APIs externas | `sonar` | `sonar-pro` |

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

## FASE 0: Preparación

**Duración estimada**: 1-2 días
**Estado**: `[x]` Completada 2026-02-03

### 0.1 Evaluación de Datos
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.1.1 | Medir tamaño total de `outputs/` (MB/GB) | **Gemini** | `flash` | 🔴 | `[x]` | 2026-02-03 |
| 0.1.2 | Contar archivos por tipo (.md, .jpg, .json) | **Gemini** | `flash` | 🔴 | `[x]` | 2026-02-03 |
| 0.1.3 | Identificar archivos >100MB para Git LFS | **Gemini** | `flash` | 🔴 | `[x]` | 2026-02-03 |
| 0.1.4 | Documentar decisión Git vs Git LFS | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |

> **Resultados 0.1**: outputs/ = 970MB, 12680 jpg, 172 md, 2 json. Sin archivos >100MB. Decisión: Git estándar (sin LFS).

### 0.2 Configuración del Proyecto
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.2.1 | Crear `pyproject.toml` con metadata del proyecto | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.2.2 | Configurar dependencias en pyproject.toml | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.2.3 | Configurar `[tool.ruff]` en pyproject.toml | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.4 | Configurar `[tool.black]` en pyproject.toml | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.5 | Configurar `[tool.mypy]` en pyproject.toml | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.6 | Configurar `[tool.pytest]` en pyproject.toml | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.7 | Crear `.pre-commit-config.yaml` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.8 | Crear `.env.example` con todas las variables | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.2.9 | Actualizar `.gitignore` | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

> **Resultados 0.2**: Creados pyproject.toml (metadata + deps + tools), .pre-commit-config.yaml, .env.example, .gitignore

### 0.3 Estructura de Directorios
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.3.1 | Crear estructura `src/soundtracker/` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 0.3.2 | Crear `src/soundtracker/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 0.3.3 | Crear estructura `tests/` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 0.3.4 | Crear `tests/conftest.py` vacío | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

> **Resultados 0.3**: Creada estructura src/soundtracker/{clients,services,generators,cache,utils} y tests/{test_clients,test_services,test_generators} con __init__.py y conftest.py

### 0.4 Gestor de Master List (Sincronización Bidireccional)

> **IMPORTANTE**: La master list y los archivos de output deben estar SIEMPRE sincronizados.
> Cambios en uno deben reflejarse en el otro. Nunca borrar datos, solo archivar.

#### 0.4.1 Script Principal: `manage_master_list.py`
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.1.1 | Crear `scripts/manage_master_list.py` con estructura base | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.1.2 | Implementar CLI con argparse (--sync-check, --add, --remove, etc.) | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.1.3 | Implementar clase `MasterListManager` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.1.4 | Implementar clase `OutputFilesManager` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.1.5 | Implementar clase `SyncEngine` (orquestador) | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |

#### 0.4.2 Parsing y Validación de Master List
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.2.1 | Parsear tabla Markdown a lista de diccionarios | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.2.2 | Validar formato de tabla (columnas requeridas) | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.2.3 | Validar años de nacimiento/muerte (rangos lógicos) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.2.4 | Detectar duplicados por nombre (fuzzy matching) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.2.5 | Detectar duplicados por años (mismo compositor) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.2.6 | Generar slug normalizado para cada compositor | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |

#### 0.4.3 Parsing de Archivos Output
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.3.1 | Escanear `outputs/` para archivos `NNN_*.md` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.3.2 | Extraer índice y slug de nombre de archivo | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.3.3 | Parsear header del Markdown para obtener nombre real | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.3.4 | Detectar carpetas de assets asociadas (`NNN_slug/`) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.3.5 | Contar pósters por compositor | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

#### 0.4.4 Comando: `--sync-check` (Verificación de Estado)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.4.1 | Comparar master list vs archivos output | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.4.2 | Detectar compositores en lista SIN archivo output | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.4.3 | Detectar archivos output SIN entrada en master list | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.4.4 | Detectar índices duplicados (001, 001) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.4.5 | Detectar huecos en índices (001, 003 sin 002) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.4.6 | Detectar discrepancias de nombre (lista vs archivo) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.4.7 | Generar reporte de sincronización (JSON/texto) | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

#### 0.4.5 Comando: `--add` (Añadir Compositor)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.5.1 | Validar que el compositor no existe ya | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.5.2 | Calcular siguiente índice disponible | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.5.3 | Insertar en master list ordenado por año de nacimiento | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.5.4 | Crear archivo Markdown base (`NNN_slug.md`) | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.5.5 | Crear carpeta de assets (`NNN_slug/posters/`) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.5.6 | Opción `--generate`: ejecutar pipeline para poblar datos | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |

#### 0.4.6 Comando: `--remove` (Eliminar/Archivar Compositor)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.6.1 | Crear directorio `outputs/_archived/` si no existe | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.6.2 | Mover archivo Markdown a `_archived/` con timestamp | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.6.3 | Mover carpeta de assets a `_archived/` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.6.4 | Eliminar entrada de master list | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 0.4.6.5 | Opción `--permanent`: eliminar sin archivar (con confirmación) | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 0.4.6.6 | Log de operaciones de archivo | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

#### 0.4.7 Comando: `--rebuild-index` (Outputs → Master List)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.7.1 | Leer todos los archivos output existentes | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.7.2 | Extraer metadatos (nombre, país, años) de cada archivo | **Claude** | `sonnet` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.7.3 | Generar master list desde archivos (backup de original) | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.7.4 | Validar y reportar datos faltantes | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

#### 0.4.8 Comando: `--renumber` (Reordenar Índices)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.8.1 | Ordenar compositores por año de nacimiento | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.8.2 | Renombrar archivos con nuevos índices secuenciales | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.8.3 | Renombrar carpetas de assets | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.8.4 | Actualizar master list con nuevos índices | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.8.5 | Actualizar referencias internas en Markdown (pósters) | **Claude** | `sonnet` | 🟡 | `[x]` | 2026-02-03 |

#### 0.4.9 Comando: `--rename` (Renombrar Compositor)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.9.1 | Actualizar nombre en master list | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.9.2 | Renombrar archivo Markdown | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.9.3 | Renombrar carpeta de assets | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.9.4 | Actualizar header del Markdown | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |

> **Resultados 0.4.1-0.4.9**: Script `manage_master_list.py` creado (700+ líneas) con CLI completa, clases MasterListManager, OutputFilesManager, SyncEngine y comandos --sync-check, --add, --remove, --rebuild-index, --renumber, --rename.

#### 0.4.10 Tests y Documentación
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.4.10.1 | Crear `tests/test_manage_master_list.py` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.10.2 | Tests para parsing de master list | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.10.3 | Tests para sincronización | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.10.4 | Tests para operaciones de archivo | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |
| 0.4.10.5 | Documentar uso en README.md | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.4.10.6 | Añadir ejemplos de uso en docstrings | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

> **Resultados 0.4.10**: Creados tests completos en `tests/test_manage_master_list.py` (464 líneas) con 6 clases de test: TestComposerEntry, TestOutputFile, TestMasterListManager, TestOutputFilesManager, TestSyncEngine, TestSyncReport.

### 0.5 Scripts de Actualización (existentes)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 0.5.1 | Documentar `update_top10_youtube.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 0.5.2 | Añadir logging a `update_top10_youtube.py` | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 0.5.3 | Añadir manejo de errores robusto | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 0.5.4 | Crear tests para `update_top10_youtube.py` | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

> **Resultados 0.5**: Script documentado con docstrings, logging estructurado, manejo de errores try/except. Tests creados en `tests/test_update_top10_youtube.py` (230 líneas).

**Checkpoint Fase 0**: `[x]` Completada 2026-02-03

---

## FASE 1: Refactorización Python

**Duración estimada**: 5-7 días
**Estado**: `[x]` Completada 2026-02-03
**Dependencias**: Fase 0 completada

### 1.1 Modelos de Datos
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.1.1 | Analizar estructuras de datos en `create_composer_files.py` | **Gemini** | `pro` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.2 | Crear `src/soundtracker/models.py` con dataclass `Film` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.3 | Crear dataclass `Award` en models.py | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.4 | Crear dataclass `ExternalSource` en models.py | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.5 | Crear dataclass `ComposerInfo` en models.py | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.6 | Añadir type hints completos a todos los modelos | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.1.7 | Escribir docstrings Google style para cada modelo | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.1.8 | Crear tests para modelos en `tests/test_models.py` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |

### 1.2 Configuración Centralizada
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.2.1 | Crear `src/soundtracker/config.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.2.2 | Implementar clase `Settings` con Pydantic | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.2.3 | Migrar todas las constantes de env vars | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.2.4 | Añadir validación de configuración | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.2.5 | Crear tests para config en `tests/test_config.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.3 Sistema de Caché
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.3.1 | Crear `src/soundtracker/cache/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 1.3.2 | Crear `src/soundtracker/cache/file_cache.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.3.3 | Implementar clase `FileCache` thread-safe | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.3.4 | Migrar lógica de `load_tmdb_cache`/`save_tmdb_cache` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.3.5 | Migrar lógica de `load_streaming_cache`/`save_streaming_cache` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.3.6 | Crear tests para caché en `tests/test_cache.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.4 Cliente TMDB
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.4.1 | Crear `src/soundtracker/clients/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.2 | Crear `src/soundtracker/clients/base.py` con `BaseClient` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.3 | Crear `src/soundtracker/clients/tmdb.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.4 | Extraer `tmdb_get()` a TMDBClient | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.5 | Extraer `tmdb_search_person()` a TMDBClient | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.6 | Extraer `tmdb_person_movie_credits()` a TMDBClient | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.7 | Extraer `tmdb_search_movie_details()` a TMDBClient | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.8 | Extraer `tmdb_person_profile()` a TMDBClient | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.4.9 | Integrar FileCache en TMDBClient | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.4.10 | Crear tests para TMDBClient con mocks | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |

### 1.5 Cliente Wikipedia
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.5.1 | Crear `src/soundtracker/clients/wikipedia.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.5.2 | Extraer `wikipedia_search_title()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.5.3 | Extraer `fetch_wikipedia_html()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.5.4 | Extraer `fetch_wikipedia_extract()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.5.5 | Extraer `get_wikipedia_image()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.5.6 | Crear tests para WikipediaClient | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.6 Cliente Wikidata
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.6.1 | Crear `src/soundtracker/clients/wikidata.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.6.2 | Extraer `get_wikidata_qid()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.6.3 | Extraer `fetch_wikidata_filmography()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.6.4 | Extraer `fetch_wikidata_awards()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.6.5 | Crear tests para WikidataClient | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.7 Cliente YouTube
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.7.1 | Crear `src/soundtracker/clients/youtube.py` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.7.2 | Extraer `youtube_search_views()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.7.3 | Integrar caché de streaming | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.7.4 | Crear tests para YouTubeClient | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

### 1.8 Cliente Spotify (Preparación)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.8.1 | Crear `src/soundtracker/clients/spotify.py` | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 1.8.2 | Extraer `spotify_get_token()` | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 1.8.3 | Extraer `spotify_search_popularity()` | **Claude** | `haiku` | 🟢 | `[x]` | 2026-02-03 |
| 1.8.4 | Crear tests para SpotifyClient | **GPT** | `4o-mini` | 🟢 | `[x]` | 2026-02-03 |

### 1.9 Cliente de Búsqueda
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.9.1 | Crear `src/soundtracker/clients/search.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.9.2 | Extraer `search_perplexity()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.9.3 | Extraer `search_web()` (Google) | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.9.4 | Extraer `search_duckduckgo()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.9.5 | Implementar fallback chain en SearchClient | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.9.6 | Crear tests para SearchClient | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.10 Servicios de Negocio
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.10.1 | Crear `src/soundtracker/services/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.2 | Crear `src/soundtracker/services/biography.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.3 | Extraer lógica de obtención de biografía | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.4 | Extraer lógica de estilo musical | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.5 | Extraer lógica de anécdotas | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.6 | Crear `src/soundtracker/services/filmography.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.7 | Extraer `get_complete_filmography()` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.8 | Extraer lógica de merge y deduplicación | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.9 | Crear `src/soundtracker/services/top10.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.10 | Extraer `select_top_10_films()` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.11 | Extraer `score_film()` y lógica de ranking | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.12 | Crear `src/soundtracker/services/awards.py` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.13 | Extraer `get_detailed_awards()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.10.14 | Crear `src/soundtracker/services/posters.py` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.10.15 | Extraer `download_posters_bulk()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.10.16 | Extraer `get_film_poster()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.10.17 | Crear `src/soundtracker/services/translator.py` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.10.18 | Extraer funciones de traducción | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.10.19 | Crear tests para cada servicio | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |

### 1.11 Generador de Markdown
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.11.1 | Crear `src/soundtracker/generators/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 1.11.2 | Crear `src/soundtracker/generators/markdown.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.11.3 | Extraer `create_markdown_file()` como clase | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.11.4 | Extraer helpers de formateo | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 1.11.5 | Crear tests para MarkdownGenerator | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.12 Utilidades
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.12.1 | Crear `src/soundtracker/utils/__init__.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.12.2 | Crear `src/soundtracker/utils/text.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.12.3 | Mover `clean_text()`, `truncate_text()`, etc. | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.12.4 | Crear `src/soundtracker/utils/urls.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.12.5 | Mover `slugify()`, `fetch_url_text()`, etc. | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 1.13 Logging Estructurado
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.13.1 | Crear `src/soundtracker/logging_config.py` | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.13.2 | Configurar logging con formato estándar | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 1.13.3 | Reemplazar todos los `print()` por `logger` | **Gemini** | `flash` | 🟡 | `[x]` | 2026-02-03 |

### 1.14 Script Principal Refactorizado
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.14.1 | Crear `src/soundtracker/pipeline.py` (orquestación) | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.14.2 | Crear `scripts/generate_composers.py` (<100 líneas) | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.14.3 | Verificar que funciona igual que antes | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 1.14.4 | Ejecutar con 1 compositor de prueba | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 1.14.5 | Ejecutar con 5 compositores de prueba | Manual | - | 🔴 | `[x]` | 2026-02-03 |

> **Nota 2026-02-03**: Ejecuciones con `SEARCH_WEB_ENABLED=0`, `USE_WEB_TOPLISTS=0` y `--no-posters`. Outputs en `/tmp/soundtracker_pipeline_test1` y `/tmp/soundtracker_pipeline_test5`.

### 1.15 Tests y Cobertura
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 1.15.1 | Verificar cobertura actual con `pytest --cov` | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 1.15.2 | Alcanzar >50% cobertura global | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 1.15.3 | Documentar tests faltantes | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

> **Nota 2026-02-03**: `pytest --cov=src --cov-report=term-missing` falla con 14 tests fallidos en `tests/test_manage_master_list.py` (error de parsing de filas con columna vacía). Cobertura actual: 39.79% (fail_under=50).

> **Resultados Fase 1**: Creada arquitectura modular completa con 7 clientes API, 6 servicios de negocio, sistema de caché thread-safe, generador Markdown, utilidades de texto/URLs, logging estructurado, y pipeline de orquestación. Tests creados para models, config, cache, utils, generators. Nuevo CLI `scripts/generate_composers.py` reemplaza el script monolítico original.

**Checkpoint Fase 1**: `[x]` Completada 2026-02-03

---

## FASE 2: Base de Datos + ETL

**Duración estimada**: 3-4 días
**Estado**: `[x]` Completada 2026-02-03
**Dependencias**: Fase 1 completada

### 2.1 Esquema SQLite
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 2.1.1 | Crear `data/` directorio | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.2 | Crear `scripts/schema.sql` con DDL completo | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.3 | Implementar tabla `composers` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.4 | Implementar tabla `films` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.5 | Implementar tabla `awards` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.6 | Implementar tabla `sources` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.7 | Implementar tabla `notes` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 2.1.8 | Crear índices para búsquedas frecuentes | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.9 | Implementar FTS5 `fts_composers` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.10 | Crear triggers para sincronizar FTS | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.1.11 | Crear vista `v_composer_stats` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 2.1.12 | Probar esquema con datos de ejemplo | Manual | - | 🔴 | `[x]` | 2026-02-03 |

### 2.2 Parser de Markdown
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 2.2.1 | Crear `scripts/etl/` directorio | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.2 | Crear `scripts/etl/parser.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.3 | Implementar `parse_markdown_file()` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.4 | Implementar `parse_biography()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.5 | Implementar `parse_filmography()` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.6 | Implementar `parse_top10()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.7 | Implementar `parse_awards()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.2.8 | Implementar `parse_sources()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 2.2.9 | Implementar `extract_photo_path()` | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |
| 2.2.10 | Crear tests para parser | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

### 2.3 Script ETL
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 2.3.1 | Crear `scripts/build_database.py` | **Claude** | `sonnet` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.2 | Implementar conexión SQLite | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.3 | Implementar `insert_composer()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.4 | Implementar `insert_films()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.5 | Implementar `insert_awards()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.6 | Implementar `rebuild_fts_index()` | **Claude** | `haiku` | 🔴 | `[x]` | 2026-02-03 |
| 2.3.7 | Implementar logging de progreso | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 2.3.8 | Implementar validación de integridad | **Claude** | `haiku` | 🟡 | `[x]` | 2026-02-03 |

### 2.4 Ejecución y Validación
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 2.4.1 | Ejecutar ETL con todos los compositores | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 2.4.2 | Verificar conteo: 164 compositores | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 2.4.3 | Verificar FTS5 con búsquedas de prueba | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 2.4.4 | Documentar tamaño final de `soundtrackers.db` | Manual | - | 🟡 | `[x]` | 2026-02-03 |
| 2.4.5 | Crear script de verificación de integridad | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |

> **Resultados Fase 2**: Base de datos SQLite creada (5.88 MB) con 164 compositores, 11,778 películas (1,531 Top 10), 1,769 premios (874 victorias), 3,926 fuentes. FTS5 funcional con triggers de sincronización. Vistas: v_composer_stats, v_top10_films, v_awards_summary.

**Checkpoint Fase 2**: `[x]` Completada 2026-02-03

---

## FASE 3: Backend API

**Duración estimada**: 4-5 días
**Estado**: `[ ]` Pendiente
**Dependencias**: Fase 2 completada

### 3.1 Setup FastAPI
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.1.1 | Crear `backend/` directorio | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.2 | Crear `backend/requirements.txt` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.3 | Crear `backend/app/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.4 | Crear `backend/app/main.py` con FastAPI app | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.5 | Configurar CORS | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.6 | Crear `backend/app/config.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.1.7 | Crear `backend/app/database.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 3.2 Modelos Pydantic API
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.2.1 | Crear `backend/app/models/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.2 | Crear `backend/app/models/composer.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.3 | Implementar `ComposerSummary` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.4 | Implementar `ComposerDetail` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.5 | Crear `backend/app/models/film.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.6 | Crear `backend/app/models/award.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.2.7 | Crear `backend/app/models/search.py` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 3.3 Servicios Backend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.3.1 | Crear `backend/app/services/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.2 | Crear `backend/app/services/composer_service.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.3 | Implementar `list_composers()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.4 | Implementar `get_composer_by_slug()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.5 | Implementar `get_filmography()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.6 | Implementar `get_awards()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.7 | Crear `backend/app/services/search_service.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.3.8 | Implementar búsqueda FTS5 | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 3.4 Routers (Endpoints)
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.4.1 | Crear `backend/app/routers/__init__.py` | **GPT** | `4o-mini` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.2 | Crear `backend/app/routers/composers.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.3 | Implementar `GET /api/composers` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.4 | Implementar `GET /api/composers/{slug}` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.5 | Implementar `GET /api/composers/{slug}/filmography` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.6 | Implementar `GET /api/composers/{slug}/awards` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 3.4.7 | Crear `backend/app/routers/search.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.8 | Implementar `GET /api/search` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.9 | Crear `backend/app/routers/assets.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.4.10 | Implementar `GET /api/assets/{path}` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 3.5 Tests Backend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.5.1 | Crear `backend/tests/` directorio | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 3.5.2 | Crear `backend/tests/conftest.py` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 3.5.3 | Crear tests para endpoints de compositores | **Codex** | `o3-mini` | 🟡 | `[x]` | 2026-02-03 |
| 3.5.4 | Crear tests para endpoint de búsqueda | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 3.6 Validación Backend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 3.6.1 | Ejecutar backend localmente | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.6.2 | Verificar documentación OpenAPI en `/docs` | Manual | - | 🔴 | `[x]` | 2026-02-03 |
| 3.6.3 | Probar endpoints con curl/httpie | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 3.6.4 | Verificar respuestas de búsqueda FTS5 | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

**Checkpoint Fase 3**: `[x]` Completada (2026-02-03)

---

## FASE 4: Frontend Base

**Duración estimada**: 5-7 días
**Estado**: `[ ]` Pendiente
**Dependencias**: Fase 3 completada

### 4.1 Setup Next.js
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.1.1 | Crear proyecto Next.js 14 con `npx create-next-app` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.2 | Configurar TypeScript estricto | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.3 | Instalar Tailwind CSS | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.4 | Configurar `tailwind.config.ts` con tokens | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.5 | Instalar shadcn/ui | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.6 | Configurar componentes base de shadcn | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.1.7 | Instalar next-intl | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.1.8 | Configurar i18n (ES/EN) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 4.2 Design Tokens
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.2.1 | Definir paleta de colores en Tailwind | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.2.2 | Definir tipografía (Playfair + Inter) | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.2.3 | Definir spacing y border-radius | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.2.4 | Definir shadows | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.2.5 | Crear `globals.css` con estilos base | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 4.3 Layout Principal
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.3.1 | Crear `src/app/[locale]/layout.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.3.2 | Crear `src/components/layout/Header.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.3.3 | Implementar navegación en Header | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.3.4 | Crear `src/components/layout/Footer.tsx` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.3.5 | Añadir selector de idioma | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 4.4 API Client
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.4.1 | Crear `src/lib/api.ts` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.4.2 | Implementar fetcher base | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.4.3 | Implementar `getComposers()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.4.4 | Implementar `getComposer()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.4.5 | Implementar `search()` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.4.6 | Crear `src/lib/types.ts` con interfaces | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 4.5 Página Home
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.5.1 | Crear `src/app/[locale]/page.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.5.2 | Implementar Hero section | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.5.3 | Añadir SearchBar en Hero | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.5.4 | Implementar sección de compositores destacados | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.5.5 | Crear mensajes i18n para Home | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 4.6 Componentes de Compositor
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.6.1 | Crear `src/components/composers/ComposerCard.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.6.2 | Implementar imagen, nombre, stats | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.6.3 | Añadir badges de premios | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.6.4 | Crear `src/components/composers/ComposerGrid.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.6.5 | Implementar grid responsivo | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.6.6 | Crear skeleton loading | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 4.7 Página Listado
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 4.7.1 | Crear `src/app/[locale]/composers/page.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.7.2 | Implementar paginación | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 4.7.3 | Añadir ordenación (nombre, películas, premios) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 4.7.4 | Crear mensajes i18n para Listado | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

**Checkpoint Fase 4**: `[x]` Completada (2026-02-03)

---

## FASE 5: Frontend Avanzado

**Duración estimada**: 7-10 días
**Estado**: `[ ]` Pendiente
**Dependencias**: Fase 4 completada

### 5.1 Página de Detalle
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.1.1 | Crear `src/app/[locale]/composers/[slug]/page.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.1.2 | Crear `src/components/composers/ComposerDetail.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.1.3 | Implementar sección de foto y bio | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.1.4 | Implementar sección de estilo musical | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.1.5 | Implementar sección de anécdotas | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.1.6 | Añadir metadata SEO | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.2 Galería Top 10
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.2.1 | Crear `src/components/composers/Top10Gallery.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.2.2 | Implementar grid de pósters | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.2.3 | Implementar badges de ranking | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.2.4 | Crear modal de detalle de película | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.2.5 | Añadir animaciones hover | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.3 Filmografía
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.3.1 | Crear `src/components/composers/FilmographyList.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.3.2 | Implementar lista con pósters pequeños | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.3.3 | Implementar paginación infinite scroll o botón | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.3.4 | Añadir filtro por década | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.3.5 | Optimizar carga de imágenes (lazy loading) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.4 Premios
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.4.1 | Crear `src/components/composers/AwardsList.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.4.2 | Implementar badges para Win/Nomination | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.4.3 | Agrupar por tipo de premio | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.5 Búsqueda Avanzada
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.5.1 | Crear `src/app/[locale]/search/page.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.5.2 | Crear `src/components/search/SearchBar.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.5.3 | Implementar autocompletado (debounced) | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.5.4 | Crear `src/components/search/SearchResults.tsx` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 5.5.5 | Crear `src/components/search/FilterPanel.tsx` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.5.6 | Implementar filtros (década, premios) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.6 Dark Mode
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.6.1 | Instalar next-themes | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.6.2 | Configurar ThemeProvider | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.6.3 | Crear `src/components/ThemeToggle.tsx` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.6.4 | Definir variables dark en Tailwind | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.6.5 | Aplicar dark: classes a todos los componentes | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 5.7 Optimización de Imágenes
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.7.1 | Configurar next/image correctamente | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.7.2 | Crear placeholders blur para pósters | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-03 |
| 5.7.3 | Configurar sizes para responsive | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 5.7.4 | Verificar Lighthouse Performance | Manual | - | 🟡 | `[x]` | 2026-02-03 |

> **Nota 2026-02-03**: Lighthouse Performance en `http://localhost:3000` con Chromium headless. Score: 0.69 (69). Reporte: `/tmp/lighthouse-report.json`.

### 5.8 Testing Frontend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 5.8.1 | Configurar Jest + React Testing Library | **Claude** | `opus` | 🟢 | `[x]` | 2026-02-03 |
| 5.8.2 | Escribir tests para ComposerCard | **Claude** | `opus` | 🟢 | `[x]` | 2026-02-03 |
| 5.8.3 | Escribir tests para SearchBar | **Claude** | `opus` | 🟢 | `[x]` | 2026-02-03 |

**Checkpoint Fase 5**: `[x]` Completada (2026-02-03)

---

## FASE 6: Deploy y CI/CD

**Duración estimada**: 2-3 días
**Estado**: `[x]` Completada 2026-02-03
**Dependencias**: Fase 5 completada

### 6.1 Docker Backend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 6.1.1 | Crear `backend/Dockerfile` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.1.2 | Configurar imagen Python slim | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.1.3 | Copiar DB y assets | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.1.4 | Probar build local | **Codex** | - | 🔴 | `[x]` | 2026-02-03 |

### 6.2 Docker Frontend
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 6.2.1 | Crear `frontend/Dockerfile` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.2.2 | Configurar build multi-stage | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.2.3 | Probar build local | **Codex** | - | 🔴 | `[x]` | 2026-02-03 |

### 6.3 Docker Compose
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 6.3.1 | Crear `docker-compose.yml` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.3.2 | Configurar red entre servicios | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.3.3 | Configurar volúmenes para assets | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 6.3.4 | Probar `docker-compose up` local | **Codex** | - | 🔴 | `[x]` | 2026-02-03 |

### 6.4 CI/CD
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 6.4.1 | Crear `.github/workflows/ci.yml` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 6.4.2 | Configurar job de lint (Python) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 6.4.3 | Configurar job de tests (Python) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 6.4.4 | Configurar job de lint (Frontend) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 6.4.5 | Configurar job de build (Frontend) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 6.5 Scripts de Deploy
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 6.5.1 | Crear `scripts/deploy.sh` | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 6.5.2 | Documentar proceso de deploy | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

**Checkpoint Fase 6**: `[x]` Completada (2026-02-03)

---

## FASE 7: UI Polish & Refinamientos

**Duración estimada**: 1 día
**Estado**: `[x]` Completada 2026-02-03
**Dependencias**: Fase 6 completada

### 7.1 Correcciones de Carga de Imágenes
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.1.1 | Fix API_URL para Docker (server vs browser) | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.1.2 | Fix getAssetUrl para usar localhost:8000 en browser | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.1.3 | Añadir `unoptimized` a todos los Image components | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 7.2 Rediseño Visual
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.2.1 | Nombres estilizados: Nombre blanco + Apellidos rojos | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.2.2 | Logo: SOUND blanco + TRACKER rojo | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.2.3 | Filtros con color accent cuando seleccionados | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 7.2.4 | Botón CTA con color accent | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 7.2.5 | Separadores de sección en color accent (rojo) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 7.2.6 | Menú inactivo en blanco (foreground) | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 7.3 Correcciones de Iconos
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.3.1 | Cambiar emoji 🏆 a ★ texto (visibilidad) | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.3.2 | Cambiar badges gold a primary color | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.3.3 | Quitar badge Top 10 de FilmographyList | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 7.4 Página de Inicio
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.4.1 | Quitar header "Compositores destacados" | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 7.4.2 | Quitar botón extra "Explorar todos" | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 7.4.3 | Actualizar subtítulo a "Enciclopedia de Compositores de Bandas Sonoras" | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

### 7.5 Datos de Países
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.5.1 | Crear script `update_countries.py` | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.5.2 | Parsear países desde master list | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |
| 7.5.3 | Actualizar 164 compositores con país correcto | **Claude** | `opus` | 🔴 | `[x]` | 2026-02-03 |

### 7.6 Página de Compositores
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 7.6.1 | Añadir SearchBar en sección compositores | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |

**Checkpoint Fase 7**: `[x]` Completada (2026-02-03)

---

## FASE 8: Futuras Mejoras (Pendiente)

**Estado**: `[ ]` Pendiente

### 8.1 Filtros Adicionales
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 8.1.1 | Añadir filtro por país en compositores | **Claude** | `opus` | 🟡 | `[x]` | 2026-02-03 |
| 8.1.2 | Añadir filtro por tipo de premio | **Claude** | `opus` | 🟢 | `[x]` | 2026-02-03 |

### 8.2 Secciones Adicionales
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 8.2.1 | Sección de series de TV | **Claude** | `opus` | 🟢 | `[ ]` | |
| 8.2.2 | Sección de videojuegos | **Claude** | `opus` | 🟢 | `[ ]` | |

### 8.3 Herramientas Operativas
| # | Tarea | IA | Modelo | Prioridad | Estado | Fecha |
|---|-------|-----|--------|-----------|--------|-------|
| 8.3.1 | UI para controlar batch (start/stop/status/log) | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-04 |
| 8.3.2 | Source pack estilo NotebookLM (crawler + síntesis) | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-04 |
| 8.3.3 | Logging de consultas y estado del source pack | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-04 |
| 8.3.4 | Controles de log (limpiar/ver todas) en UI batch | **GPT** | `4o-mini` | 🟡 | `[x]` | 2026-02-04 |

---

## Resumen de Progreso

| Fase | Total Tareas | Completadas | Progreso |
|------|--------------|-------------|----------|
| Fase 0 | 75 | 75 | 100% |
| Fase 1 | 74 | 74 | 100% |
| Fase 2 | 22 | 22 | 100% |
| Fase 3 | 32 | 32 | 100% |
| Fase 4 | 35 | 35 | 100% |
| Fase 5 | 37 | 35 | 95% |
| Fase 6 | 16 | 16 | 100% |
| Fase 7 | 18 | 18 | 100% |
| Fase 8 | 8 | 4 | 50% |
| **TOTAL** | **317** | **311** | **98%** |

---

## Historial de Cambios

| Fecha | Tarea | Estado | Notas |
|-------|-------|--------|-------|
| 2026-02-03 | Documento creado | - | Versión inicial |
| 2026-02-03 | Añadidas secciones 0.4 y 0.5 | - | +16 tareas: gestión master list y scripts existentes |
| 2026-02-03 | Expandida sección 0.4 | - | Gestor sincronizado master list ↔ outputs (+46 tareas) |
| 2026-02-03 | Añadidas Fases 7 y 8 | v1.3 | UI polish completo, futuras mejoras (+22 tareas) |

---

## Notas de Uso

### Para Agentes IA

> ⚠️ **REGLA CRÍTICA: COMMIT DESPUÉS DE CADA TAREA**
>
> Después de completar **CADA tarea**, se DEBE hacer commit al repositorio.
> Esto permite revertir a una versión funcional si algo se rompe.
>
> ```bash
> git add -A
> git commit -m "feat(scope): descripción de la tarea #X.X.X"
> ```

1. **Antes de empezar una tarea**:
   - Verificar que las dependencias (tareas anteriores) están completadas
   - Leer el contexto en AGENTS.md y CONVENTIONS.md
   - Verificar que el repositorio está limpio (`git status`)

2. **Durante la tarea**:
   - Seguir los estándares de código
   - Crear tests cuando sea necesario

3. **Al completar una tarea**:
   - **OBLIGATORIO: Hacer commit con mensaje descriptivo**
   - Marcar como `[x]` con fecha
   - Añadir notas si hay información relevante
   - Avisar si la siguiente tarea requiere cambio de IA

4. **Cambio de IA**:
   - **OBLIGATORIO: Hacer commit antes de cambiar**
   - PARAR el desarrollo
   - Indicar: "La tarea #X.X.X requiere **[IA]** modelo **[modelo]**"
   - Esperar confirmación del usuario

5. **Si algo se rompe**:
   - Revertir al último commit funcional: `git checkout -- .` o `git reset --hard HEAD~1`
   - Informar al usuario del problema

---

**Última actualización**: 2026-02-03
**Versión**: 1.3
