# Estado y pendientes de `create_composer_files.py`

## Estado actual (implementado)

- Generacion de Markdown por compositor con:
  - Biografia, estilo musical, anecdotas (siempre presentes).
  - Top 10 con ranking por listas web + TMDB + premios + YouTube.
  - Filmografia completa con posters locales.
  - Premios y nominaciones con normalizacion en espanol.
  - Fuentes externas (MundoBSO, Film Score Monthly, SoundtrackCollector, WhatSong).
- Traduccion automatica con deteccion de idioma a espanol.
- Titulos de peliculas en formato: `Original (Titulo en Espana: ...)`.
- Descarga concurrente de posters para toda la filmografia.
- Busqueda web con Perplexity + fallback a Google y DuckDuckGo.
- Filtros de dominios bloqueados para evitar 403/404 repetidos.
- Reanudar batch con `START_INDEX`.
- Nombre de foto local: `photo_nombre_apellido.jpg`.
- Script dedicado para recalcular solo Top 10 con YouTube sin rehacer datos:
  - `App/scripts/update_top10_youtube.py`.

## Pendientes / Necesitan credenciales

- **Spotify**: usar popularidad (0-100) para enriquecer el Top 10.
  - Requiere `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` (actualmente alta de apps en pausa).
- **Amazon Music**: API oficial en beta cerrada (si hay acceso).
- **YouTube Music**: no hay API oficial (solo librerias no oficiales).

## Mejoras recomendadas

- Auto-resume por log (sin `START_INDEX`).
- Lista negra de dominios configurable por env.
- Filtrado mas agresivo de posters ruidosos.
- Validacion de Top 10 con sanity checks.
- Integracion UI + backend (ver `App/DEVELOPMENT_PLAN.md`).
