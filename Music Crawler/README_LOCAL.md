# Music Crawler

CLI para buscar y descargar música de fuentes legales, priorizando fuentes gratuitas y registrando alternativas de pago.

## Propósito

Music Crawler automatiza la búsqueda de pistas musicales específicas (ej: bandas sonoras clásicas de cine) en múltiples plataformas simultáneamente:

- **Descarga** de fuentes gratuitas (YouTube, Internet Archive, SoundCloud, etc.)
- **Registra** dónde comprar en servicios de pago (Spotify, iTunes, Deezer, etc.)
- **Genera reportes** en Markdown con todos los resultados

Ideal para coleccionistas de música clásica de cine, investigadores y archivistas.

## Estado actual (2026-02-05)

- CLI funcional con búsqueda multi-fuente y generación de reportes.
- Descarga real solo desde YouTube mediante `yt-dlp`.
- Resto de fuentes: solo se registran enlaces en el reporte.
- Cache local por carpeta de salida (`.crawl_cache.json`).
- Tests actuales limitados al parser de listas de pistas.

## Limitaciones conocidas

- Varias fuentes usan búsqueda web HTML (más frágil ante cambios externos).
- Sin integración directa con el pipeline de SOUNDTRACKER (pendiente).
- Rate limiting básico (sleep fijo); sin backoff ni control por proveedor.

## Instalación

```bash
cd "Music Crawler"
pip install -r requirements.txt
```

Dependencias principales:
- `yt-dlp` - Extracción de audio de YouTube
- `requests` - Peticiones HTTP
- `beautifulsoup4` - Parsing HTML
- `rich` - Interfaz CLI bonita

## Uso Básico

### Buscar y descargar desde una lista

```bash
python -m src.cli.crawl tracks.txt
```

### Buscar una pista individual

```bash
python -m src.cli.crawl --track "The Wizard of Oz - Over the Rainbow"
```

### Solo buscar (sin descargar)

```bash
python -m src.cli.crawl tracks.txt --search-only
```

### Modo rápido (solo APIs, sin rate limiting)

```bash
python -m src.cli.crawl tracks.txt --fast
```

### Ver fuentes disponibles

```bash
python -m src.cli.crawl --list-sources
```

## Opciones CLI

| Opción | Descripción |
|--------|-------------|
| `--output, -o` | Directorio de salida (default: `downloads/{compositor}/`) |
| `--format, -f` | Formato de audio: mp3, flac, wav, best |
| `--quality, -q` | Calidad MP3: 128, 192, 256, 320, best |
| `--composer` | Nombre del compositor para búsquedas |
| `--search-only, -s` | Solo buscar, no descargar |
| `--fast` | Modo rápido: solo fuentes con API |
| `--sources` | Fuentes específicas: `--sources=youtube,deezer` |
| `--no-cache` | Ignorar caché y re-buscar todo |
| `--report, -r` | Ruta del reporte (default: `REPORT.md`) |

## Formato de Lista de Pistas

```
10
Treasure Island
"Main Title" (de la colección FSM)
Fanfarria pirata clásica.

9
The Wizard of Oz
"Over the Rainbow"
Tema icónico de Dorothy.
```

Cada bloque contiene:
1. Número de ranking
2. Nombre de la película
3. Título del cue (con notas opcionales en paréntesis)
4. Descripción (opcional)

## Fuentes Soportadas

### Fuentes Gratuitas (descargan)

| Fuente | Método | Descripción |
|--------|--------|-------------|
| YouTube | API (yt-dlp) | Extracción de audio de videos |
| Internet Archive | API | Grabaciones de dominio público |
| SoundCloud | Web Search | Algunos tracks gratuitos |
| Jamendo | API/Web | Música Creative Commons |
| Free Music Archive | Web Search | Archivo Creative Commons |
| Musopen | Web Search | Clásica de dominio público |
| IMSLP | Web Search | Partituras y grabaciones PD |

### Fuentes de Pago (solo registro)

| Fuente | Método | Descripción |
|--------|--------|-------------|
| Spotify | Web Search | Streaming por suscripción |
| iTunes/Apple Music | API | Compra por pista |
| Deezer | API | Streaming Hi-Fi |
| Amazon Music | Web Search | HD/Ultra HD streaming |
| Tidal | Web Search | MQA Hi-Res streaming |
| Qobuz | Web Search | Especialista Hi-Res |
| Bandcamp | Web Search | Compra directa al artista |

## Estructura del Proyecto

```
Music Crawler/
├── src/
│   ├── cli/
│   │   └── crawl.py           # Punto de entrada CLI
│   ├── parsers/
│   │   └── track_list.py      # Parser de listas de pistas
│   ├── searchers/
│   │   ├── base.py            # Clase base abstracta
│   │   ├── youtube.py         # Búsqueda YouTube
│   │   ├── archive_org.py     # Internet Archive
│   │   ├── soundcloud.py      # SoundCloud
│   │   ├── jamendo.py         # Jamendo (CC)
│   │   ├── fma.py             # Free Music Archive
│   │   ├── musopen.py         # Musopen + IMSLP
│   │   ├── spotify.py         # Spotify + iTunes
│   │   ├── deezer.py          # Deezer (API gratuita)
│   │   ├── amazon.py          # Amazon Music
│   │   ├── bandcamp.py        # Bandcamp
│   │   └── tidal.py           # Tidal + Qobuz
│   ├── downloaders/
│   │   └── ytdlp.py           # Wrapper de yt-dlp
│   ├── models/
│   │   └── track.py           # Dataclasses (Track, SearchResult)
│   └── report/
│       └── generator.py       # Generador de reportes MD
├── downloads/                  # Música descargada (por compositor)
├── data/
│   └── sample_lists/          # Listas de ejemplo
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Arquitectura

### Modelos de Datos

```python
@dataclass
class Track:
    rank: int
    film: str
    cue_title: str
    description: str
    composer: str = "Herbert Stothart"

@dataclass
class SearchResult:
    track: Track
    source: str       # "youtube", "spotify", etc.
    url: str
    is_free: bool
    quality: str
    downloaded: bool = False
    local_path: Path | None = None
```

### Flujo de Ejecución

1. **Parseo**: `track_list.py` lee el archivo de entrada
2. **Búsqueda**: Cada `Searcher` busca en su fuente
3. **Descarga**: `ytdlp.py` extrae audio de fuentes gratuitas
4. **Reporte**: `generator.py` crea el Markdown final

### Búsquedas

Dos tipos de searchers:

- **API-based**: Usan APIs oficiales (YouTube, Deezer, iTunes, Archive.org)
- **Web Search**: Buscan via Chrome headless (Google results) o Perplexity (SoundCloud, Spotify, Amazon, etc.)

El modo `--fast` solo usa searchers con API para evitar rate limiting.

## Salida

### Archivos Descargados

```
downloads/Herbert_Stothart/
├── 01_the_good_earth_main_title.mp3
├── 02_the_wizard_of_oz_main_title.mp3
├── ...
└── REPORT.md
```

### Formato del Reporte

```markdown
# Music Crawl Report - Herbert Stothart

## Summary
- Total tracks: 10
- Downloaded: 9
- Not found: 1

### Sources Found
| Source | Results | Type |
|--------|---------|------|
| YouTube | 27 | Free |
| Deezer | 5 | Paid |

## Downloaded Tracks
### 1. The Good Earth - "Main Title"
- **Source:** YouTube
- **Quality:** 320kbps MP3
- **File:** `01_the_good_earth_main_title.mp3`

## Not Found
- 5. A Tale of Two Cities - "The Guillotine"
```

## Caché

El crawler guarda un caché en `.crawl_cache.json` para evitar re-descargar pistas ya obtenidas. Usar `--no-cache` para forzar nueva búsqueda.

## Consideraciones Legales

- **YouTube**: Uso personal vía yt-dlp
- **Internet Archive**: Contenido de dominio público
- **Jamendo/FMA**: Licencias Creative Commons
- **Servicios de pago**: Solo se registra dónde comprar, no se descarga

## Ejemplos

### Buscar bandas sonoras de Herbert Stothart

```bash
python -m src.cli.crawl data/sample_lists/stothart_top10.txt --fast
```

### Buscar música de Mozart (solo APIs)

```bash
python -m src.cli.crawl --track "Mozart Symphony 40" --composer "Mozart" --fast
```

### Buscar en fuentes específicas

```bash
python -m src.cli.crawl tracks.txt --sources=youtube,deezer,itunes
```

### Exportar a FLAC de alta calidad

```bash
python -m src.cli.crawl tracks.txt --format flac --quality best
```
