# CONVENTIONS.md - SOUNDTRACKER

**Estándares de Código y Convenciones** | v1.0 | 2026-02-03

> Este documento es **de solo lectura para agentes IA** (usar como contexto, no modificar).
> Para gobernanza operativa, ver `AGENTS.md`. Este archivo complementa las secciones de AGENTS.md.

---

## 0. Propósito y Alcance

Este documento define **estándares detallados de código** para el proyecto SOUNDTRACKER:
- Convenciones de naming (variables, funciones, clases, módulos)
- Estructura de módulos y paquetes
- Patrones de código permitidos y prohibidos
- Ejemplos concretos de código correcto/incorrecto
- Integración con linters y formatters

**Audiencia**: Desarrolladores humanos y agentes IA que contribuyen al proyecto.

---

## 1. Python: Estilo y Formateo

### 1.1 PEP 8 Estricto

**Herramientas de enforcement**:
- `ruff` (linter rápido, reemplazo de flake8/pylint)
- `black` (formatter automático)
- `isort` (ordenamiento de imports)
- `mypy` (type checking)

**Configuración** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### 1.2 Line Length y Wrapping

**Línea máxima**: 100 caracteres

**Excepciones permitidas**:
- URLs largas en docstrings o comentarios
- Imports que no se pueden partir lógicamente

**Ejemplo correcto**:
```python
def get_composer_filmography(
    composer_name: str,
    tmdb_client: TMDBClient,
    include_streaming: bool = True,
    max_films: int = 200,
) -> list[Film]:
    """Obtiene filmografía completa de un compositor."""
    pass
```

**Ejemplo incorrecto**:
```python
# ❌ Línea demasiado larga
def get_composer_filmography(composer_name: str, tmdb_client: TMDBClient, include_streaming: bool = True, max_films: int = 200) -> list[Film]:
    pass
```

---

## 2. Naming Conventions

### 2.1 Variables y Funciones

**Estilo**: `snake_case`

**Ejemplos correctos**:
```python
# Variables
composer_name = "John Williams"
film_count = 42
tmdb_api_key = os.getenv("TMDB_API_KEY")

# Funciones
def fetch_wikipedia_extract(query: str, lang: str = "es") -> str:
    pass

def calculate_top_10_score(film: Film, boost_scores: dict[str, int]) -> float:
    pass
```

**Ejemplos incorrectos**:
```python
# ❌ camelCase
composerName = "John Williams"
filmCount = 42

# ❌ Nombres no descriptivos
def calc(f):  # Demasiado corto
    pass

def function_to_fetch_the_wikipedia_extract_for_composer(q):  # Demasiado largo
    pass
```

### 2.2 Clases

**Estilo**: `PascalCase`

**Ejemplos correctos**:
```python
class TMDBClient:
    pass

class ComposerInfo:
    pass

class WikipediaExtractor:
    pass

class MarkdownGenerator:
    pass
```

### 2.3 Constantes

**Estilo**: `SCREAMING_SNAKE_CASE`

**Ubicación**: Definir al inicio del módulo o en `config.py`

**Ejemplos correctos**:
```python
# config.py
TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
MAX_FILM_LIMIT = 200
DEFAULT_POSTER_WORKERS = 8
SUPPORTED_LANGUAGES = ["es", "en"]
```

### 2.4 Módulos y Archivos

**Estilo**: `snake_case`

**Ejemplos correctos**:
```
src/soundtracker/
├── tmdb_client.py         # ✅
├── wikipedia_extractor.py # ✅
├── markdown_generator.py  # ✅
└── top10_calculator.py    # ✅
```

**Ejemplos incorrectos**:
```
src/soundtracker/
├── TMDBClient.py          # ❌ PascalCase
├── wikipedia-extractor.py # ❌ Guiones
├── markdownGenerator.py   # ❌ camelCase
```

---

## 3. Type Hints (Obligatorios)

### 3.1 Regla General

**TODAS las funciones públicas deben tener type hints completos**:
- Parámetros
- Valor de retorno
- Atributos de clase

### 3.2 Ejemplos Correctos

```python
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Film:
    title: str
    original_title: str
    title_es: Optional[str] = None
    year: Optional[int] = None
    poster_path: Optional[Path] = None

def get_filmography(
    composer_name: str,
    max_films: int = 200,
    include_posters: bool = True,
) -> list[Film]:
    """Obtiene filmografía de un compositor."""
    pass

def calculate_score(
    film: Film,
    boost_scores: dict[str, int],
    award_keys: set[str],
) -> float:
    """Calcula score para ranking."""
    pass
```

### 3.3 Ejemplos Incorrectos

```python
# ❌ Sin type hints
def get_filmography(composer_name, max_films=200):
    pass

# ❌ Uso de Any sin justificación
from typing import Any

def process_data(data: Any) -> Any:
    pass
```

### 3.4 Tipos Específicos del Proyecto

```python
# types.py
from typing import TypeAlias
from pathlib import Path

ComposerSlug: TypeAlias = str
FilmTitle: TypeAlias = str
PosterPath: TypeAlias = Path | str
BoostScores: TypeAlias = dict[str, int]
AwardKeys: TypeAlias = set[str]
```

---

## 4. Docstrings (Estilo Google)

### 4.1 Funciones Públicas (Obligatorio)

```python
def get_top_10_films(
    composer: str,
    filmography: list[Film],
    awards: list[Award],
    boost_scores: dict[str, int],
) -> list[Film]:
    """Selecciona las 10 mejores bandas sonoras de un compositor.

    Utiliza un algoritmo de scoring combinando:
    - Popularidad de TMDB
    - Views de YouTube
    - Premios ganados
    - Menciones en listas web

    Args:
        composer: Nombre del compositor
        filmography: Lista completa de películas
        awards: Premios y nominaciones del compositor
        boost_scores: Puntuaciones de boost por título normalizado

    Returns:
        Lista de 10 películas ordenadas por score descendente

    Raises:
        ValueError: Si filmography está vacía
    """
    pass
```

### 4.2 Clases

```python
class TMDBClient:
    """Cliente para la API de TMDB (The Movie Database).

    Maneja autenticación, caché de respuestas y rate limiting.
    Soporta búsqueda de personas, películas y descarga de pósters.

    Attributes:
        api_key: Clave de API de TMDB
        cache: Diccionario de respuestas cacheadas
        base_url: URL base de la API

    Example:
        >>> client = TMDBClient(api_key="...")
        >>> person_id = client.search_person("John Williams")
        >>> films = client.get_movie_credits(person_id)
    """

    def __init__(self, api_key: str, cache_path: Optional[Path] = None) -> None:
        """Inicializa el cliente TMDB.

        Args:
            api_key: Clave de API (requerida)
            cache_path: Ruta para persistir caché (opcional)
        """
        pass
```

---

## 5. Imports (Ordenamiento con isort)

### 5.1 Orden Estándar

1. **Standard library** (alfabético)
2. **Third-party packages** (alfabético)
3. **Local imports** (alfabético)

**Separación**: Una línea en blanco entre cada grupo

### 5.2 Ejemplo Correcto

```python
# Standard library
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse

# Third-party
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Local
from soundtracker.clients.tmdb import TMDBClient
from soundtracker.config import settings
from soundtracker.models import ComposerInfo, Film
```

---

## 6. Estructura de Módulos

### 6.1 Orden de Elementos en un Módulo

```python
"""Module docstring - Descripción del módulo."""

# 1. Imports
import standard_library
import third_party
from local import module

# 2. Logger
logger = logging.getLogger(__name__)

# 3. Constantes globales
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10

# 4. Type aliases (si aplica)
ConfigDict = dict[str, str | int | float]

# 5. Excepciones custom (si aplica)
class TMDBError(Exception):
    """Error de la API de TMDB."""
    pass

# 6. Clases
class MainClass:
    pass

# 7. Funciones públicas
def public_function() -> None:
    pass

# 8. Funciones privadas (helpers)
def _internal_helper(data: str) -> str:
    pass

# 9. Main guard (si es script ejecutable)
if __name__ == "__main__":
    main()
```

### 6.2 Límites de Tamaño (CRÍTICO)

| Elemento | Límite | Acción al Exceder |
|----------|--------|-------------------|
| Función | 50 líneas | Refactorizar en subfunciones |
| Clase | 300 líneas | Dividir en clases cohesivas |
| Módulo | 1,000 líneas | Dividir en submódulos |

---

## 7. Patrones de Código

### 7.1 Error Handling

**Regla**: Siempre usar excepciones específicas, nunca `except Exception` sin re-raise

**Correcto**:
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.HTTPError as e:
    logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
    return None
except requests.Timeout:
    logger.warning(f"Timeout fetching {url}")
    return None
except requests.RequestException as e:
    logger.error(f"Request failed for {url}: {e}")
    raise
```

**Incorrecto**:
```python
# ❌ Catch-all silencioso
try:
    response = requests.get(url)
except:
    pass

# ❌ Sin re-raise
try:
    risky_operation()
except Exception as e:
    print(f"Error: {e}")  # Solo loguea, no propaga
```

### 7.2 Dataclasses para Datos Estructurados

**Preferir dataclasses/Pydantic sobre dicts**:

```python
# ✅ Correcto - Dataclass tipada
from dataclasses import dataclass
from typing import Optional

@dataclass
class Film:
    title: str
    original_title: str
    year: Optional[int] = None
    poster_path: Optional[str] = None

# ❌ Incorrecto - Dict no tipado
film = {
    "title": "Star Wars",
    "original_title": "Star Wars",
    "year": 1977,
}
```

### 7.3 Context Managers

**Preferir context managers para recursos**:

```python
# ✅ Correcto
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

# ❌ Incorrecto
f = open("data.json")
data = json.load(f)
f.close()
```

### 7.4 List Comprehensions vs Loops

**Preferir comprehensions para transformaciones simples**:

```python
# ✅ Comprehension simple
film_titles = [film.title for film in films if film.year and film.year > 2000]

# ✅ Generator para grandes datasets
total_views = sum(film.youtube_views or 0 for film in films)

# ⚠️ Loop cuando la lógica es compleja
results = []
for film in films:
    if film.year and film.year > 2000:
        score = calculate_complex_score(film, awards, boost_scores)
        if score > threshold:
            results.append((film, score))
```

---

## 8. Código Prohibido

### 8.1 Variables Globales Mutables

**Prohibido** (actual en `create_composer_files.py`):
```python
# ❌ Actual - Variables globales mutables
TMDB_MOVIE_CACHE = load_tmdb_cache()
STREAMING_CACHE = load_streaming_cache()
SPOTIFY_TOKEN = {'value': None, 'expires_at': 0}
```

**Correcto** (migrar a clases):
```python
# ✅ Clase con estado encapsulado
class CacheManager:
    def __init__(self, cache_path: Path):
        self._cache_path = cache_path
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if self._cache_path.exists():
            return json.loads(self._cache_path.read_text())
        return {}

    def get(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def set(self, key: str, value: dict) -> None:
        self._data[key] = value
        self._save()

    def _save(self) -> None:
        self._cache_path.write_text(json.dumps(self._data, indent=2))
```

### 8.2 print() para Logging

**Prohibido**:
```python
# ❌ Print para logging
print(f"Processing {composer} -> {filename}")
print(f"    - failed to fetch {url}: {exc}")
```

**Correcto**:
```python
# ✅ Logging estructurado
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing composer: {composer}")
logger.warning(f"Failed to fetch {url}", exc_info=True)
logger.error(f"Critical error processing {composer}", exc_info=True)
```

### 8.3 Star Imports

**Prohibido**:
```python
# ❌ Prohibido
from soundtracker.models import *
```

**Correcto**:
```python
# ✅ Explícito
from soundtracker.models import ComposerInfo, Film, Award
```

### 8.4 Mutable Default Arguments

**Prohibido**:
```python
# ❌ Bug clásico de Python
def append_film(film: Film, films: list[Film] = []) -> list[Film]:
    films.append(film)
    return films
```

**Correcto**:
```python
# ✅ Correcto
def append_film(film: Film, films: Optional[list[Film]] = None) -> list[Film]:
    if films is None:
        films = []
    films.append(film)
    return films
```

---

## 9. Testing Conventions

### 9.1 Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidos
├── test_clients/
│   ├── test_tmdb.py
│   ├── test_wikipedia.py
│   └── test_wikidata.py
├── test_services/
│   ├── test_filmography.py
│   ├── test_top10.py
│   └── test_awards.py
└── test_generators/
    └── test_markdown.py
```

### 9.2 Naming de Tests

**Formato**: `test_<cosa>_<condición>_<resultado>`

```python
def test_calculate_score_with_awards_returns_higher_value():
    """Test que premios aumentan el score."""
    pass

def test_get_filmography_with_empty_response_returns_empty_list():
    """Test que respuesta vacía devuelve lista vacía."""
    pass

def test_parse_markdown_with_missing_section_handles_gracefully():
    """Test que secciones faltantes no causan error."""
    pass
```

### 9.3 Fixtures

```python
# conftest.py
import pytest
from soundtracker.models import Film, Award

@pytest.fixture
def sample_film() -> Film:
    return Film(
        title="Star Wars",
        original_title="Star Wars",
        year=1977,
        poster_path="/path/to/poster.jpg",
    )

@pytest.fixture
def sample_awards() -> list[Award]:
    return [
        Award(award="Oscar", year=1978, film="Star Wars", status="Win"),
        Award(award="Grammy", year=1978, film="Star Wars", status="Win"),
    ]

@pytest.fixture
def mock_tmdb_client(mocker):
    return mocker.patch("soundtracker.clients.tmdb.TMDBClient")
```

---

## 10. Logging

### 10.1 Niveles de Log

| Nivel | Uso |
|-------|-----|
| DEBUG | Información detallada para debugging |
| INFO | Eventos normales (procesando compositor, guardado archivo) |
| WARNING | Eventos inusuales pero manejables (retry, timeout, fallback) |
| ERROR | Errores que impiden completar operación |
| CRITICAL | Errores que comprometen el sistema |

### 10.2 Formato de Mensajes

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Correcto
logger.info(f"Processing composer: {composer_name}")
logger.warning(f"TMDB rate limit hit, waiting {wait_time}s")
logger.error(f"Failed to download poster for {film_title}", exc_info=True)

# ❌ Incorrecto
print("Processing...")
logger.info("Error")  # Sin contexto
```

---

## 11. Configuración y Secrets

### 11.1 Pydantic Settings

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # APIs
    tmdb_api_key: str
    pplx_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None

    # Comportamiento
    download_posters: bool = True
    poster_workers: int = 8
    film_limit: int = 200

    # Paths
    output_dir: str = "outputs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 11.2 .env.example

```bash
# .env.example (SÍ commitear)
TMDB_API_KEY=tu_clave_aqui
PPLX_API_KEY=tu_clave_perplexity
YOUTUBE_API_KEY=tu_clave_youtube
DOWNLOAD_POSTERS=1
POSTER_WORKERS=8
```

---

## 12. Enforcement y Validación

### 12.1 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies: [pydantic, requests]
```

### 12.2 CI/CD Checks

```yaml
# .github/workflows/ci.yml
- name: Lint with ruff
  run: ruff check src/

- name: Format with black
  run: black --check src/

- name: Type check with mypy
  run: mypy --strict src/

- name: Run tests
  run: pytest --cov=src --cov-report=term-missing --cov-fail-under=70
```

---

## 13. Referencias Rápidas

### Comandos
```bash
ruff check src/ --fix    # Lint
black src/               # Format
mypy src/ --strict       # Types
pytest --cov=src         # Tests
```

### Enlaces
- [PEP 8](https://peps.python.org/pep-0008/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Black](https://black.readthedocs.io/)
- [MyPy](https://mypy.readthedocs.io/)
- [Google Style Guide](https://google.github.io/styleguide/pyguide.html)

---

**v1.0** | 2026-02-03 | SOUNDTRACKER | Para cambios: issue con tag `[CONVENTIONS]`
