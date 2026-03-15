import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "vocab_learner.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the application database schema."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                title TEXT NOT NULL,
                authors TEXT,
                lang TEXT,
                UNIQUE(asin, title)
            );

            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                stem TEXT,
                lang TEXT,
                book_id INTEGER REFERENCES books(id),
                usage TEXT,
                lookup_time INTEGER,
                lookup_count INTEGER DEFAULT 1,
                -- Spaced repetition fields
                ease_factor REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                next_review TEXT,
                last_reviewed TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(word, book_id, usage)
            );

            CREATE INDEX IF NOT EXISTS idx_words_next_review ON words(next_review);
            CREATE INDEX IF NOT EXISTS idx_words_stem ON words(stem);
            """
        )
        conn.commit()
    finally:
        conn.close()
