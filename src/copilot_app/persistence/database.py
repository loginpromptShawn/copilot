import sqlite3
from pathlib import Path

# Use config-based path with fallback to home directory
def _default_db_path() -> Path:
    try:
        from ..utils.config import get_config
        config = get_config()
        if config.has_section("paths") and config.has_option("paths", "data_dir"):
            return Path(config.get("paths", "data_dir")) / "copilot.db"
    except Exception:
        pass
    return Path.home() / "copilot.db"

DB_PATH = _default_db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_users_schema(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE,
            password_hash TEXT,
            is_active INTEGER DEFAULT 1
        )
        """
    )
    cur.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cur.fetchall()}
    if "username" not in existing_columns:
        cur.execute("ALTER TABLE users ADD COLUMN username TEXT")
    if "password_hash" not in existing_columns:
        cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "is_active" not in existing_columns:
        cur.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    _ensure_users_schema(cur)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS system_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            os TEXT,
            version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()
