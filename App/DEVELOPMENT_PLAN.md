# Plan de desarrollo detallado: Frontend + Backend para la base de datos de compositores

## 1. Proposito del frontend
El frontend sera la interfaz principal para explorar y consultar la base de datos de compositores de bandas sonoras. Permitira:
- Buscar compositores por nombre, pais, periodo, premios, estilos y obras.
- Consultar fichas completas con biografia, estilo musical, anecdotas, filmografia, top 10 y premios.
- Navegar filmografias con posters locales.
- Visualizar fuentes y notas externas.
- Acceso controlado por roles (admin / user).
- Interfaz bonita, moderna y dinamica, preparada para publicar en web.

## 2. Requisitos funcionales
- Backend en servidor propio.
- Datos locales (sin depender de servicios externos en tiempo real).
- Busqueda avanzada y rapida.
- Autenticacion con roles.
- Multi-idioma UI: ES (principal), EN (secundario).
- Exportable a web (frontend web + API local).
- Sincronizacion de datos mediante Git (versionado y rollback).

## 3. Arquitectura recomendada (razones)

### 3.1 Backend: FastAPI + SQLite (FTS5)
- **Motivo**: ya tenemos pipeline Python; FastAPI es rapido, moderno y facil de mantener.
- **SQLite con FTS5**: busqueda full-text sin servidor adicional, portable y versionable.
- **Ventaja**: base de datos en un solo fichero (`soundtrackers.db`).

### 3.2 Frontend: Next.js + Tailwind + shadcn/ui
- **Motivo**: UI moderna y estetica, componentes listos, facil de personalizar.
- **Soporte i18n**: integrado en Next.
- **Experiencia**: rapido para construir un frontend elegante y dinamico.

### 3.3 Sincronizacion
- **Recomendado**: generar `soundtrackers.db` localmente y versionarlo con Git.
- **Poster assets**: pueden versionarse en Git (si no es demasiado grande) o Git LFS.
- **Ventaja**: historial de datos, rollback, y despliegue simple al servidor.

## 4. Tamaño de datos (estimacion y gestion)
- Markdown: 164 compositores + metadatos.
- Posters: potencialmente miles de imagenes (GBs).
- Estrategia:
  - si < 2-3 GB: Git normal.
  - si > 3-5 GB: Git LFS recomendado.

## 5. Diseño de datos (esquema)

### 5.1 Tabla `composers`
- id (PK)
- name
- slug
- photo_path
- biography_es
- biography_en
- style_es
- style_en
- anecdotes_es
- anecdotes_en
- created_at
- updated_at

### 5.2 Tabla `films`
- id (PK)
- composer_id (FK)
- title_original
- title_es
- year
- poster_path
- is_top10
- top10_rank
- tmdb_popularity
- tmdb_vote_count
- tmdb_vote_average
- youtube_views
- created_at

### 5.3 Tabla `awards`
- id (PK)
- composer_id (FK)
- award_name
- year
- film_title
- status (Win/Nomination)

### 5.4 Tabla `sources`
- id (PK)
- composer_id (FK)
- source_name
- url
- snippet

### 5.5 Tabla `notes`
- id (PK)
- composer_id (FK)
- text
- source_name

### 5.6 Tabla `fts_composers`
- FTS5 index sobre:
  - name
  - biography_es
  - style_es
  - anecdotes_es
  - film titles
  - awards

## 6. ETL (Markdown -> SQLite)

### 6.1 Parser
- Lee `App/outputs/*.md`.
- Identifica secciones:
  - Biografia
  - Estilo musical
  - Anecdotas
  - Top 10
  - Filmografia completa
  - Premios y nominaciones
  - Fuentes adicionales
  - Notas externas

### 6.2 Normalizacion
- Titulos: `Original (Titulo en Espana: ... )` se separa en dos campos.
- Posters: rutas locales se convierten a rutas relativas.
- Premios: se normalizan y se asocian con peliculas.

### 6.3 Resultado
- Genera `soundtrackers.db` listo para consultas y API.

## 7. Backend API

### 7.1 Endpoints principales
- `GET /api/search`
  - params: q, year, award, country, style, has_award, has_top10, etc.
- `GET /api/composers`
  - listado paginado con filtros.
- `GET /api/composers/{id}`
  - detalle completo + filmografia + premios.
- `GET /api/films`
  - filtros por year, top10, composer.
- `GET /api/awards`
  - filtros por award/year.
- `GET /api/assets/{path}`
  - entrega posters locales.

### 7.2 Auth
- Login con usuario/clave.
- Roles:
  - admin: acceso completo + panel de mantenimiento.
  - user: solo lectura.

## 8. Frontend UI (detallado)

### 8.1 Paginas
- **Home**: buscador global + acceso a filtros.
- **Listado compositores**: cards con foto, top 3 y premios.
- **Detalle compositor**:
  - foto, biografia, estilo, anecdotas
  - top 10 con posters
  - filmografia completa con posters
  - premios
- **Buscador avanzado**:
  - filtros por periodo, premio, pais, estilo, etc.

### 8.2 UX / UI
- Diseno moderno (cards, tipografia elegante, colores neutros, sombras suaves).
- UI dinamica con filtros en tiempo real.
- Soporte responsive (desktop/tablet/movil).

### 8.3 i18n
- Espanol como default.
- Ingles opcional.

## 9. Sincronizacion y despliegue

- Pipeline:
  1) generar outputs
  2) construir DB (`soundtrackers.db`)
  3) commit/push a Git (o Git LFS)
  4) pull en servidor propio
  5) reiniciar backend/servicio

## 10. Riesgos y mitigacion

- **Poster gigantes**: usar Git LFS o almacenamiento separado.
- **Busquedas lentas**: FTS5 + indices.
- **Errores en parsing**: validadores y logs.
- **Credenciales externas**: fallback sin APIs.

## 11. Resultado final esperado
- Aplicacion web moderna, local y estetica.
- Busqueda avanzada rapida.
- Acceso controlado por roles.
- Datos versionados y sincronizables.

## 12. Roadmap detallado

### Fase 0: Preparacion (1-2 dias)
- Medir tamano real de `App/outputs` y posters.
- Definir si se necesita Git LFS.
- Confirmar entorno objetivo del servidor.

### Fase 1: Modelado de datos y ETL (3-5 dias)
- Definir esquema SQLite + FTS5.
- Implementar parser Markdown.
- Generar `soundtrackers.db` inicial.
- Validacion de integridad (conteo de compositores/films).

### Fase 2: Backend API (4-6 dias)
- Montar FastAPI.
- Endpoints de busqueda, listado, detalle.
- Autenticacion y roles.
- Tests basicos de API.

### Fase 3: Frontend base (5-7 dias)
- Setup Next.js + Tailwind + shadcn/ui.
- Layout principal + i18n.
- Pagina home + listado compositores.

### Fase 4: Frontend avanzado (7-10 dias)
- Detalle de compositor completo.
- Buscador avanzado con facetas.
- Paginacion y filtros dinamicos.
- Integracion con API.

### Fase 5: Admin y mantenimiento (3-4 dias)
- Login admin/user.
- Panel admin basico (ver stats, recargar DB).

### Fase 6: Deploy y sincronizacion (2-3 dias)
- Script de build + deploy.
- Configurar pipeline Git -> servidor.

### Total estimado
- 25-37 dias laborables (dependiendo de feedback y revision UI).

