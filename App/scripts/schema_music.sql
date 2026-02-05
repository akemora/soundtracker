-- Schema for music crawler outputs

CREATE TABLE IF NOT EXISTS music_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL REFERENCES composers(id) ON DELETE CASCADE,
    film_id INTEGER REFERENCES films(id),
    title TEXT NOT NULL,
    work TEXT NOT NULL,
    rank INTEGER,
    status TEXT CHECK(status IN ('downloaded', 'free_available', 'paid_only', 'not_found', 'error')),
    source TEXT,
    url TEXT,
    local_path TEXT,
    alternatives_json TEXT,
    searched_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(composer_id, film_id, title, work)
);

CREATE TABLE IF NOT EXISTS composer_playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composer_id INTEGER NOT NULL UNIQUE REFERENCES composers(id) ON DELETE CASCADE,
    total_tracks INTEGER DEFAULT 0,
    free_count INTEGER DEFAULT 0,
    paid_count INTEGER DEFAULT 0,
    playlist_json TEXT NOT NULL,
    generated_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL REFERENCES composer_playlists(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    film_title TEXT NOT NULL,
    film_year INTEGER,
    track_title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    embed_url TEXT,
    status TEXT CHECK(status IN ('free', 'paid')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_music_composer ON music_tracks(composer_id);
CREATE INDEX IF NOT EXISTS idx_music_status ON music_tracks(status);
CREATE INDEX IF NOT EXISTS idx_playlist_composer ON composer_playlists(composer_id);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id);
