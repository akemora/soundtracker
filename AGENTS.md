# AGENTS.md - SOUNDTRACKER

**README para Agentes de IA** | v1.1 | 2026-02-03

> **Propósito:** Este archivo es el **README para agentes de IA** (y humanos) del repositorio.
>
> Un agente debe poder arrancar aquí, entender el proyecto, saber **qué comandos ejecutar**, **dónde tocar**, y **qué NO tocar**.

---

## 0. Meta-Instrucciones: Cómo Leer Este Archivo (Para Agentes IA)

> **OBLIGATORIO: Lee esta sección antes de proponer cualquier cambio**

### 0.1 Protocolo de Lectura
- ✅ **Lee este archivo COMPLETO** antes de proponer cambios al proyecto
- ✅ **CONVENTIONS.md**: Si existe, trátalo como contexto de solo lectura (estándares de código detallados)
- ✅ **Propón mejoras**: Si falta información crítica para ejecutar una tarea, propón completarla en este archivo mediante PR

### 0.2 Optimización para Prompt Caching
Este archivo está diseñado para **prompt caching** (ahorro de 90% en tokens):
- Colócalo al **inicio del prompt** antes de cualquier otra instrucción
- El contenido es mayormente estático (contexto, comandos, reglas)
- Actualizado solo cuando cambia la arquitectura del proyecto

### 0.3 Jerarquía de Documentación
1. **AGENTS.md** (este archivo) → Protocolo operativo y gobernanza
2. **TASKS.md** → **Lista de tareas con checklist** (MANTENER ACTUALIZADO)
3. **CONVENTIONS.md** → Estándares de código en detalle
4. **README.md** → Información para usuarios finales
5. **DEVELOPMENT_PLAN.md** → Roadmap técnico detallado
6. **AUDIT_AND_PROPOSAL.md** → Auditoría y propuestas de mejora

### 0.4 Control de Tareas (CRÍTICO)

> **OBLIGATORIO**: El progreso del desarrollo se controla en `TASKS.md`.

> ⚠️ **REGLA CRÍTICA: COMMIT DESPUÉS DE CADA TAREA**
>
> Se DEBE hacer commit al repositorio después de completar **CADA tarea**.
> Esto permite revertir a una versión funcional si algo se rompe.
>
> ```bash
> git add <archivos_modificados>
> git commit -m "feat(scope): descripción de la tarea #X.X.X"
> ```
> **NO continuar a la siguiente tarea sin hacer commit de la anterior.**

**Protocolo de uso de TASKS.md**:

1. **Antes de empezar cualquier tarea**:
   - Leer `TASKS.md` para identificar la siguiente tarea pendiente
   - Verificar que las dependencias están completadas
   - Verificar qué IA y modelo se recomienda
   - **Verificar que el repositorio está limpio** (`git status`)

2. **Si la tarea requiere una IA diferente**:
   - **HACER COMMIT** de cualquier trabajo pendiente
   - **PARAR** el desarrollo
   - **AVISAR**: "La tarea #X.X.X requiere **[IA]** modelo **[modelo]**"
   - Esperar confirmación del usuario

3. **Al completar una tarea**:
   - **OBLIGATORIO: Hacer commit con mensaje descriptivo**
   - Marcar como `[x]` en TASKS.md
   - Añadir fecha de completado
   - Añadir notas si hay información relevante
   - Verificar si la siguiente tarea requiere cambio de IA

4. **Si algo se rompe**:
   - Revertir al último commit: `git checkout -- .` o `git reset --hard HEAD~1`
   - Informar al usuario del problema antes de continuar

4. **Asignación de IAs**:
   | IA | Fortalezas | Modelo Económico | Modelo Potente |
   |----|------------|------------------|----------------|
   | **Claude** | Arquitectura, código complejo, refactoring | `haiku` | `sonnet`/`opus` |
   | **GPT** | Código general, scripts, documentación | `4o-mini` | `4o` |
   | **Gemini** | Contexto largo, lectura masiva | `flash` | `pro` |
   | **Perplexity** | Búsqueda web, investigación | `sonar` | `sonar-pro` |

---

## 1. Rol del Agente

Eres un/a **desarrollador/a full-stack especializado en Python y React/Next.js** con experiencia en:
- ETL y procesamiento de datos
- APIs REST con FastAPI
- Frontends modernos con Next.js + Tailwind
- Bases de datos SQLite

**Objetivo principal:** Desarrollar y mantener SOUNDTRACKER, una aplicación de investigación automatizada de compositores de cine con generación de perfiles, base de datos estructurada y frontend web moderno.

**Principios de trabajo:**
- Cambios pequeños, verificables y con pruebas
- No adivines: si no está claro, enumera supuestos y ofrece alternativas
- Mantén coherencia con el estilo del repo y minimiza refactors innecesarios
- Prioriza soluciones reales; evita el camino más corto si no es el más adecuado
- Puedes equivocarte, pero sé honesto; di la verdad siempre

---

## 2. Resumen del Proyecto

**Nombre**: SOUNDTRACKER
**Propósito**: Sistema automatizado de investigación y documentación de compositores de bandas sonoras de cine. Genera perfiles completos con biografía, filmografía, premios y rankings Top 10.

**Stack Principal**:
- **Lenguajes**: Python 3.11+, TypeScript 5.x
- **Frameworks Backend**: FastAPI (planificado)
- **Frameworks Frontend**: Next.js 14 + Tailwind + shadcn/ui (planificado)
- **Base de datos**: SQLite + FTS5 (planificado)
- **APIs externas**: TMDB, Wikipedia, Wikidata, YouTube, Perplexity, Google Search

**Dominio**: Entretenimiento / Música de cine / Base de datos de compositores

**Entorno objetivo**: Linux/WSL2

**Ubicación del Proyecto**:
```
✅ CORRECTO: /home/akenator/PROYECTOS/SOUNDTRACKER/App
```

---

## 3. Mapa Rápido del Repositorio

```
App/
├── scripts/                          # Scripts de generación de datos
│   ├── create_composer_files.py      # Pipeline principal (1,968 líneas)
│   ├── update_top10_youtube.py       # Actualización de Top 10
│   ├── test_single_composer.py       # Test de compositor individual
│   └── ...
├── outputs/                          # Datos generados (164 compositores)
│   ├── NNN_nombre_compositor.md      # Perfiles en Markdown
│   ├── NNN_nombre_compositor/        # Carpetas con pósters
│   │   └── posters/
│   ├── tmdb_cache.json               # Caché de TMDB
│   ├── streaming_cache.json          # Caché de YouTube/Spotify
│   └── composers_master_list.md      # Lista maestra de compositores
├── intermediate_research/            # Datos de investigación
├── AGENTS.md                         # Este archivo
├── CONVENTIONS.md                    # Estándares de código (si existe)
├── CONVENTIONS_FRONTEND.md           # Estándares frontend (si existe)
├── DEVELOPMENT_PLAN.md               # Plan de desarrollo detallado
├── AUDIT_AND_PROPOSAL.md             # Auditoría técnica y propuestas
├── PENDING_CHANGES.md                # Cambios pendientes
└── README.md                         # Documentación de usuario
```

**Archivos Clave**:
- **scripts/create_composer_files.py** — Pipeline principal de generación
- **outputs/** — Datos generados (NO modificar manualmente)
- **DEVELOPMENT_PLAN.md** — Roadmap técnico
- **AUDIT_AND_PROPOSAL.md** — Propuestas de mejora detalladas

---

## 4. Comandos Operacionales (OBLIGATORIO)

### 4.1 Setup Inicial
```bash
# Ubicar proyecto
cd /home/akenator/PROYECTOS/SOUNDTRACKER/App

# Crear entorno virtual (recomendado)
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install requests beautifulsoup4 google

# Para desarrollo futuro (backend/frontend)
# pip install -e ".[dev]"
```

### 4.2 Variables de Entorno Requeridas
```bash
# APIs principales (obligatorias)
export TMDB_API_KEY="tu_clave_tmdb"
export PPLX_API_KEY="tu_clave_perplexity"

# APIs opcionales
export YOUTUBE_API_KEY="tu_clave_youtube"
export SPOTIFY_CLIENT_ID="tu_client_id"
export SPOTIFY_CLIENT_SECRET="tu_client_secret"

# Configuración de comportamiento
export DOWNLOAD_POSTERS=1              # 1|0
export SEARCH_WEB_ENABLED=1            # 1|0
export POSTER_WORKERS=8                # Workers concurrentes
export FILM_LIMIT=200                  # Máximo de películas por compositor
export TOP_FORCE_AWARDS=1              # Forzar premios en Top 10
export START_INDEX=1                   # Índice para reanudar batch
```

### 4.3 Ejecución del Pipeline
```bash
# Generar todos los compositores (desde START_INDEX)
python scripts/create_composer_files.py

# Generar desde compositor específico
START_INDEX=41 python scripts/create_composer_files.py

# Solo actualizar Top 10 con YouTube (sin regenerar datos)
python scripts/update_top10_youtube.py

# Test de un compositor individual
python scripts/test_single_composer.py --composer "John Williams"
```

### 4.4 Desarrollo Diario (cuando exista refactorización)
```bash
# Linting y formateo
ruff check src/ --fix && black src/

# Type checking
mypy src/ --strict

# Tests
pytest tests/ -v

# Tests con cobertura
pytest --cov=src --cov-report=term-missing
```

### 4.5 Git Workflow

> ⚠️ **OBLIGATORIO: Commit después de CADA tarea completada**

```bash
# Después de completar cada tarea:
git add <archivos_modificados>
git commit -m "[type]([scope]): [description] #X.X.X"

# Types: feat, fix, docs, refactor, test, chore, perf, style
# Scopes: pipeline, etl, api, frontend, db, docs

# Ejemplos:
# - feat(pipeline): add Spotify popularity support #1.8.3
# - fix(etl): handle missing poster URLs gracefully #2.2.5
# - docs(readme): update installation steps #0.2.8

# IMPORTANTE:
# - NO continuar a la siguiente tarea sin hacer commit
# - NO hacer push sin confirmación explícita del usuario
# - Si algo se rompe, revertir: git reset --hard HEAD~1
```

---

## 5. Convenciones de Código

### 5.1 Python

**Naming Conventions**:
- Variables/Funciones: `snake_case`
- Clases: `PascalCase`
- Constantes: `SCREAMING_SNAKE_CASE`
- Archivos: `snake_case.py`

**Formateo**:
- Line length: `100` caracteres
- Indentación: `4` espacios
- Formatter: `black`
- Linter: `ruff`

**Type Safety**:
- Type hints: **OBLIGATORIOS** para funciones públicas
- Strict mode: Recomendado (`mypy --strict`)

**Documentación**:
- Docstrings: Google style
- Obligatorios para: funciones públicas, clases

### 5.2 TypeScript/Frontend (cuando aplique)

Ver **CONVENTIONS_FRONTEND_TEMPLATE.md** para estándares completos de:
- React/Next.js components
- Tailwind CSS
- Design tokens
- Accesibilidad

### 5.3 Patrones Prohibidos
❌ **NO usar**:
- `any` type sin justificación documentada
- Variables globales mutables (migrar a clases/singletons)
- SQL queries sin parametrizar
- Secrets hardcodeados en código
- `print()` para logging (usar `logging` module)
- Archivos de más de 1,000 líneas

---

## 6. Reglas de Git / PR

### 6.1 Branching Strategy
- **Main branch**: `main`
- **Feature branches**: `feat/[feature-name]`
- **Fix branches**: `fix/[bug-description]`
- **Other**: `chore/`, `docs/`, `refactor/`, `test/`

### 6.2 Commits
- **Formato**: Conventional Commits
- **Scope**: Recomendado (`feat(pipeline):`, `fix(etl):`)
- **Mensaje**: Imperativo, presente ("Add feature", no "Added")
- **Límites**: Primera línea ≤ 50 chars, cuerpo ≤ 72 chars por línea

### 6.3 Pull Requests
- **Descripción**: Incluye qué, por qué, y cómo se valida
- **Tamaño**: Evita PRs gigantes; divide en pasos lógicos
- **CI/CD**: Todos los checks deben pasar

---

## 7. Límites, Seguridad y Datos

### 7.1 Seguridad
- ❌ **NO** subas secretos a git (API keys, tokens)
- ✅ Usa variables de entorno
- ✅ Incluye `.env.example` como template
- ❌ **NO** toques `outputs/` con datos de producción sin backup

### 7.2 Dependencias
- ❌ **NO** agregues dependencias nuevas sin justificar
- ✅ Verifica licencias compatibles (MIT, Apache, BSD)
- ✅ Revisa vulnerabilidades conocidas

### 7.3 Datos
- ❌ **NO** modifiques manualmente archivos en `outputs/`
- ✅ Los pósters se descargan automáticamente
- ✅ Los cachés (`tmdb_cache.json`, `streaming_cache.json`) son regenerables
- ✅ **CONTROL OBLIGATORIO**: Cada vez que se modifique una ficha de compositor (`outputs/NNN_slug.md`),
  **debe actualizarse** su archivo `outputs/NNN_slug/control_changes.md` y el
  **control general** `outputs/control_composers.md` (estado, fechas y recuento de modificaciones).

---

## 8. Zonas Prohibidas (No-Touch sin Confirmación)

> Archivos/módulos que NO deben modificarse sin discusión previa con el usuario.

**Lista de archivos críticos**:
- `outputs/` — Datos generados (970 MB), regenerar es costoso
- `tmdb_cache.json` — Caché de API, puede causar rate limits si se pierde
- `streaming_cache.json` — Caché de YouTube views
- `composers_master_list.md` — Lista maestra de compositores

**Si una tarea requiere modificar estos archivos**:
1. Explica el **"por qué"** al usuario
2. Muestra **diff preciso** de los cambios propuestos
3. Espera **confirmación explícita** antes de proceder

---

## 9. Límites Arquitectónicos

### 9.1 Límites de Tamaño (Anti-Spaghetti)

| Elemento | Límite | Acción al Exceder |
|----------|--------|-------------------|
| Archivo | 1,000 líneas | Refactorizar en módulos |
| Función | 50 líneas | Dividir en subfunciones |
| Clase | 300 líneas | Dividir en clases cohesivas |
| Nivel de indentación | 4 niveles | Extraer lógica a funciones |

**CRÍTICO**: `create_composer_files.py` actualmente tiene 1,968 líneas. Ver `AUDIT_AND_PROPOSAL.md` para plan de refactorización.

### 9.2 Principios de Modularidad
- **Single Responsibility**: Cada módulo/función tiene una sola responsabilidad
- **Separation of Concerns**: APIs, lógica de negocio, I/O en módulos separados
- **No God Objects**: Evita archivos que hacen "demasiado"

---

## 10. Troubleshooting Común

### 10.1 Error: Rate limit de TMDB
**Síntoma**: `429 Too Many Requests` de TMDB API
**Causa**: Demasiadas peticiones en poco tiempo
**Solución**:
```bash
# El script tiene sleep(0.25) entre peticiones
# Si persiste, aumentar el delay o usar caché
```

### 10.2 Error: Faltan dependencias
**Síntoma**: `ImportError: No module named 'requests'`
**Solución**:
```bash
pip install requests beautifulsoup4 google
```

### 10.3 Error: Pósters no se descargan
**Síntoma**: Pósters quedan como placeholder
**Causa**: URL bloqueada o error de red
**Solución**:
```bash
# Verificar que DOWNLOAD_POSTERS=1
# Revisar lista de dominios bloqueados en el script
# Re-ejecutar con START_INDEX del compositor afectado
```

### 10.4 Error: Traducción falla
**Síntoma**: Texto queda en inglés
**Causa**: Google Translate API limitada
**Solución**:
```bash
# El script tiene fallback a texto original
# Revisar conectividad a translate.googleapis.com
```

---

## 11. Métricas de Éxito

### 11.1 Calidad de Código (objetivo post-refactorización)
- ✅ 100% de archivos < 1,000 líneas
- ✅ Cobertura de tests > 70% para nuevos módulos
- ✅ `ruff` sin warnings
- ✅ `mypy --strict` sin errores

### 11.2 Calidad de Datos
- ✅ 164 compositores procesados correctamente
- ✅ Top 10 con criterios verificables (premios, TMDB, YouTube)
- ✅ Pósters descargados para >90% de filmografías
- ✅ Texto traducido al español (España)

---

## 12. Ownership y Contacto

### 12.1 Responsabilidad Técnica
- **Owner técnico**: Usuario local
- **Proyecto**: SOUNDTRACKER
- **Repositorio**: Local (Git)

### 12.2 Documentación Principal
- **README.md**: Onboarding y uso básico
- **DEVELOPMENT_PLAN.md**: Roadmap técnico
- **AUDIT_AND_PROPOSAL.md**: Auditoría y mejoras propuestas
- **PENDING_CHANGES.md**: Estado actual y pendientes

---

## Changelog del Documento

**v1.1** (2026-02-03):
- ✅ Añadida regla crítica: commit obligatorio después de cada tarea
- ✅ Actualizada sección 0.4 con protocolo de commits
- ✅ Actualizada sección 4.5 Git Workflow

**v1.0** (2026-02-03):
- ✅ Versión inicial adaptada del template AGENTS_TEMPLATE.md
- ✅ Configuración específica para SOUNDTRACKER
- ✅ Comandos operacionales documentados
- ✅ Troubleshooting común incluido

---

## Referencias Rápidas

### Comandos de un Vistazo
```bash
# Setup
source venv/bin/activate && pip install requests beautifulsoup4 google

# Generar compositores
TMDB_API_KEY=... PPLX_API_KEY=... python scripts/create_composer_files.py

# Actualizar Top 10
python scripts/update_top10_youtube.py

# Reanudar desde índice
START_INDEX=41 python scripts/create_composer_files.py
```

### Variables de Entorno Esenciales
```bash
TMDB_API_KEY=...      # Obligatoria
PPLX_API_KEY=...      # Obligatoria
YOUTUBE_API_KEY=...   # Opcional (mejora Top 10)
DOWNLOAD_POSTERS=1    # 1|0
START_INDEX=1         # Para reanudar batch
```

---

**Última actualización**: 2026-02-03
**Versión AGENTS.md**: 1.1
**Mantenedor**: Usuario local

Para contribuir o proponer cambios a este archivo, crear PR con tag `[AGENTS]`.
