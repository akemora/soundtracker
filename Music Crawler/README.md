# Music Crawler (Módulo)

Este módulo forma parte del proyecto SOUNDTRACKER y debe seguir las reglas del repo.

Documentación y reglas principales:
- `../AGENTS.md`
- `../CONVENTIONS.md`
- `../CONVENTIONS_FRONTEND.md`
- `../TASKS.md`
- `../DEVELOPMENT_PLAN.md`
- `../AUDIT_AND_PROPOSAL.md`

Para uso del crawler, consulta `README_LOCAL.md` dentro de este módulo.

## Estado actual (2026-02-05)

- CLI funcional para búsqueda y descarga desde fuentes legales.
- Descarga real solo vía YouTube (`yt-dlp`); el resto registra enlaces.
- Cache local por carpeta de salida (`.crawl_cache.json`).
- Tests mínimos (parser de listas).
- Integración con SOUNDTRACKER pendiente.
