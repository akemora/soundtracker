-- SOUNDTRACKER Database Schema
-- SQLite with FTS5 full-text search support
-- Version: 1.0

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Composers table (main entity)
CREATE TABLE IF NOT EXISTS composers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_num INTEGER UNIQUE NOT NULL,          -- Position in master list (001, 002, etc.)
    name TEXT NOT NULL,                          -- Full name
    slug TEXT UNIQUE NOT NULL,                   -- URL-friendly identifier
    birth_year INTEGER,                          -- Year of birth
    death_year INTEGER,                          -- Year of death (NULL if alive)
    country TEXT,                                -- Country of origin
    photo_url TEXT,                              -- URL to composer photo
    photo_local TEXT,                            -- Local path to photo
    biography TEXT,                              -- Biography text
    style TEXT,                                  -- Musical style description
    anecdotes TEXT,                              -- Interesting anecdotes
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Films table (filmography)
CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL,
    title TEXT NOT NULL,                         -- Display title
    original_title TEXT,                         -- Original title
    title_es TEXT,                               -- Spanish title
    year INTEGER,                                -- Release year
    poster_url TEXT,                             -- TMDB poster URL
    poster_local TEXT,                           -- Local path to poster
    is_top10 INTEGER DEFAULT 0,                  -- 1 if in top 10
    top10_rank INTEGER,                          -- Position in top 10 (1-10)
    tmdb_id INTEGER,                             -- TMDB movie ID
    imdb_id TEXT,                                -- IMDB ID
    vote_average REAL,                           -- TMDB vote average
    vote_count INTEGER,                          -- TMDB vote count
    popularity REAL,                             -- TMDB popularity score
    spotify_popularity REAL,                     -- Spotify popularity
    youtube_views INTEGER,                       -- YouTube view count
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (composer_id) REFERENCES composers(id) ON DELETE CASCADE
);

-- Awards table
CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL,
    award_name TEXT NOT NULL,                    -- Award name (Oscar, Grammy, etc.)
    category TEXT,                               -- Award category
    year INTEGER,                                -- Year awarded/nominated
    film_title TEXT,                             -- Associated film (if any)
    status TEXT NOT NULL CHECK (status IN ('win', 'nomination')),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (composer_id) REFERENCES composers(id) ON DELETE CASCADE
);

-- External sources table
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL,
    name TEXT NOT NULL,                          -- Source name (Wikipedia, IMDb, etc.)
    url TEXT NOT NULL,                           -- Source URL
    snippet TEXT,                                -- Brief description or snippet
    source_type TEXT DEFAULT 'reference',        -- 'reference' or 'snippet'
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (composer_id) REFERENCES composers(id) ON DELETE CASCADE
);

-- Notes table (additional text content)
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL,
    title TEXT,                                  -- Note title
    content TEXT NOT NULL,                       -- Note content
    note_type TEXT DEFAULT 'general',            -- Type of note
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (composer_id) REFERENCES composers(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Composer indexes
CREATE INDEX IF NOT EXISTS idx_composers_name ON composers(name);
CREATE INDEX IF NOT EXISTS idx_composers_birth_year ON composers(birth_year);
CREATE INDEX IF NOT EXISTS idx_composers_country ON composers(country);
CREATE INDEX IF NOT EXISTS idx_composers_index_num ON composers(index_num);

-- Film indexes
CREATE INDEX IF NOT EXISTS idx_films_composer_id ON films(composer_id);
CREATE INDEX IF NOT EXISTS idx_films_year ON films(year);
CREATE INDEX IF NOT EXISTS idx_films_title ON films(title);
CREATE INDEX IF NOT EXISTS idx_films_is_top10 ON films(is_top10);
CREATE INDEX IF NOT EXISTS idx_films_top10_rank ON films(top10_rank);
CREATE INDEX IF NOT EXISTS idx_films_tmdb_id ON films(tmdb_id);

-- Award indexes
CREATE INDEX IF NOT EXISTS idx_awards_composer_id ON awards(composer_id);
CREATE INDEX IF NOT EXISTS idx_awards_year ON awards(year);
CREATE INDEX IF NOT EXISTS idx_awards_status ON awards(status);
CREATE INDEX IF NOT EXISTS idx_awards_award_name ON awards(award_name);

-- Source indexes
CREATE INDEX IF NOT EXISTS idx_sources_composer_id ON sources(composer_id);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);

-- Note indexes
CREATE INDEX IF NOT EXISTS idx_notes_composer_id ON notes(composer_id);

-- =============================================================================
-- FTS5 FULL-TEXT SEARCH
-- =============================================================================

-- FTS5 virtual table for composer search
CREATE VIRTUAL TABLE IF NOT EXISTS fts_composers USING fts5(
    name,
    biography,
    style,
    anecdotes,
    country,
    content='composers',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- =============================================================================
-- FTS5 TRIGGERS (keep FTS in sync with composers table)
-- =============================================================================

-- Trigger: After INSERT on composers
CREATE TRIGGER IF NOT EXISTS composers_ai AFTER INSERT ON composers BEGIN
    INSERT INTO fts_composers(rowid, name, biography, style, anecdotes, country)
    VALUES (new.id, new.name, new.biography, new.style, new.anecdotes, new.country);
END;

-- Trigger: After DELETE on composers
CREATE TRIGGER IF NOT EXISTS composers_ad AFTER DELETE ON composers BEGIN
    INSERT INTO fts_composers(fts_composers, rowid, name, biography, style, anecdotes, country)
    VALUES ('delete', old.id, old.name, old.biography, old.style, old.anecdotes, old.country);
END;

-- Trigger: After UPDATE on composers
CREATE TRIGGER IF NOT EXISTS composers_au AFTER UPDATE ON composers BEGIN
    INSERT INTO fts_composers(fts_composers, rowid, name, biography, style, anecdotes, country)
    VALUES ('delete', old.id, old.name, old.biography, old.style, old.anecdotes, old.country);
    INSERT INTO fts_composers(rowid, name, biography, style, anecdotes, country)
    VALUES (new.id, new.name, new.biography, new.style, new.anecdotes, new.country);
END;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Composer statistics view
CREATE VIEW IF NOT EXISTS v_composer_stats AS
SELECT
    c.id,
    c.index_num,
    c.name,
    c.slug,
    c.birth_year,
    c.death_year,
    c.country,
    c.photo_local,
    (SELECT COUNT(*) FROM films f WHERE f.composer_id = c.id) AS film_count,
    (SELECT COUNT(*) FROM films f WHERE f.composer_id = c.id AND f.is_top10 = 1) AS top10_count,
    (SELECT COUNT(*) FROM awards a WHERE a.composer_id = c.id AND a.status = 'win') AS wins,
    (SELECT COUNT(*) FROM awards a WHERE a.composer_id = c.id AND a.status = 'nomination') AS nominations,
    (SELECT COUNT(*) FROM awards a WHERE a.composer_id = c.id) AS total_awards,
    (SELECT COUNT(*) FROM sources s WHERE s.composer_id = c.id) AS source_count
FROM composers c
ORDER BY c.index_num;

-- Top 10 films view with composer info
CREATE VIEW IF NOT EXISTS v_top10_films AS
SELECT
    f.id AS film_id,
    f.title,
    f.original_title,
    f.title_es,
    f.year,
    f.top10_rank,
    f.poster_local,
    f.vote_average,
    f.spotify_popularity,
    f.youtube_views,
    c.id AS composer_id,
    c.name AS composer_name,
    c.slug AS composer_slug
FROM films f
JOIN composers c ON f.composer_id = c.id
WHERE f.is_top10 = 1
ORDER BY c.index_num, f.top10_rank;

-- Awards summary view
CREATE VIEW IF NOT EXISTS v_awards_summary AS
SELECT
    c.id AS composer_id,
    c.name AS composer_name,
    c.slug AS composer_slug,
    a.award_name,
    SUM(CASE WHEN a.status = 'win' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN a.status = 'nomination' THEN 1 ELSE 0 END) AS nominations
FROM composers c
LEFT JOIN awards a ON c.id = a.composer_id
GROUP BY c.id, a.award_name
HAVING a.award_name IS NOT NULL
ORDER BY c.index_num, wins DESC;

-- =============================================================================
-- HELPER FUNCTIONS (via application layer)
-- =============================================================================

-- Note: SQLite doesn't support stored procedures, but these queries can be
-- used in the application layer:

-- Search composers by name (FTS5):
-- SELECT c.* FROM composers c
-- JOIN fts_composers fts ON c.id = fts.rowid
-- WHERE fts_composers MATCH 'search_term*';

-- Get composer with all related data:
-- SELECT * FROM v_composer_stats WHERE slug = ?;

-- Rebuild FTS index (if needed):
-- INSERT INTO fts_composers(fts_composers) VALUES('rebuild');
