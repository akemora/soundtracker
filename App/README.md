# Soundtrackers: Film Composer Research Application

> Ver plan de desarrollo completo en `App/DEVELOPMENT_PLAN.md`.

## Resumen

Este proyecto automatiza la investigacion profunda de compositores de cine. Genera un Markdown por compositor con biografia, estilo musical, anecdotas, filmografia completa, top 10 de bandas sonoras, premios, fuentes externas y enlaces a posters locales. Todo el texto se normaliza a espanol (Espana) y los titulos de peliculas se muestran como:

```
Titulo original (Titulo en Espana: Titulo)
```

## Caracteristicas clave

- **Biografia, estilo musical y anecdotas** siempre presentes (si no hay datos, se rellena con texto de apoyo).
- **Filmografia completa** desde TMDB + Wikidata + Wikipedia + buscadores.
- **Top 10** por compositor con criterios combinados:
  - listas web (Perplexity/Google/DDG),
  - "known_for" de TMDB,
  - popularidad y votos de TMDB,
  - premios (Oscar, BAFTA, etc.) forzados en el Top 10,
  - **views de YouTube** como criterio adicional.
- **Posters locales** para toda la filmografia (descarga masiva y concurrente).
- **Foto del compositor** en local: `photo_nombre_apellido.jpg`.
- **Fuentes externas**: MundoBSO, Film Score Monthly, SoundtrackCollector, WhatSong + otras fuentes generales.
- **Traduccion automatica** con deteccion de idioma a espanol.

## Fuentes y APIs

- **Wikipedia ES/EN** (biografia, secciones, infobox).
- **Wikidata** (filmografia + premios).
- **TMDB** (creditos, posters, titulos en espanol, popularidad).
- **Perplexity** (busquedas principales) con fallback a Google y DuckDuckGo.
- **YouTube**: views para enriquecer Top 10 (requiere API key).
- **Spotify**: preparado para popularidad (pendiente de credenciales).

## Estructura del proyecto

```
App/
  scripts/
  outputs/
  intermediate_research/
  DEVELOPMENT_PLAN.md
```

## Uso rapido

1) Instalar dependencias:
```
pip install requests beautifulsoup4 google
```

2) Exportar claves necesarias:
```
export TMDB_API_KEY=...
export PPLX_API_KEY=...
export YOUTUBE_API_KEY=...
```

3) Ejecutar:
```
python3 App/scripts/create_composer_files.py
```

## Actualizar solo el Top 10 con YouTube (sin rehacer datos)

```
export YOUTUBE_API_KEY=...
export TMDB_API_KEY=...
export PPLX_API_KEY=...
python3 App/scripts/update_top10_youtube.py
```

Opcional:
- `START_INDEX=41` para reanudar desde un indice.

## Configuracion avanzada (env vars)

- **Busqueda web**
  - `SEARCH_WEB_ENABLED=1|0`
  - `PPLX_API_KEY` o `PERPLEXITY_API_KEY`
  - `PPLX_MODEL=sonar` (modelo mas barato)

- **Posters**
  - `DOWNLOAD_POSTERS=1|0`
  - `POSTER_WEB_FALLBACK=1|0`
  - `POSTER_WORKERS=8`
  - `POSTER_LIMIT=0` (0 = ilimitado)

- **Filmografia**
  - `FILM_LIMIT=200`

- **Texto y profundidad**
  - `EXTERNAL_SNIPPET_SOURCES=12`
  - `EXTERNAL_SNIPPET_MAX_CHARS=700`
  - `MAX_BIO_PARAGRAPHS=6`
  - `EXTERNAL_DOMAIN_RESULTS=3`

- **Top 10**
  - `TOP_MIN_VOTE_COUNT=50`
  - `TOP_FORCE_AWARDS=1`

- **Reanudar batch**
  - `START_INDEX=41` (arranca desde el compositor 041)

- **Streaming (opcional)**
  - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_ENABLED=1`
  - `YOUTUBE_API_KEY`, `YOUTUBE_ENABLED=1`
  - `STREAMING_CANDIDATE_LIMIT=30`

## Notas

- Las salidas viven en `App/outputs/` y se versionan en Git.
- Algunos dominios bloquean scraping (lista negra interna) para evitar ruido y acelerar.
- YouTube Music no tiene API oficial; Amazon Music Web API es beta cerrada.
- Ver `App/DEVELOPMENT_PLAN.md` para el plan del frontend/backend.
