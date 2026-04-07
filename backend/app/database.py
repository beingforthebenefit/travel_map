import aiosqlite
from pathlib import Path

from app.config import settings

_db_path: Path | None = None


def get_db_path() -> Path:
    global _db_path
    if _db_path is None:
        _db_path = Path(settings.data_dir) / "db.sqlite3"
    return _db_path


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db():
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    db = await get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id            TEXT PRIMARY KEY,
                title         TEXT NOT NULL,
                subtitle      TEXT DEFAULT '',
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                style         TEXT DEFAULT 'watercolor',
                print_width   REAL DEFAULT 24.0,
                print_height  REAL DEFAULT 18.0,
                dpi           INTEGER DEFAULT 300,
                show_title    INTEGER DEFAULT 1,
                loop_route    INTEGER DEFAULT 0,
                api_key_ref   TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS stops (
                id            TEXT PRIMARY KEY,
                trip_id       TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
                sort_order    INTEGER NOT NULL,
                city          TEXT NOT NULL,
                label         TEXT DEFAULT NULL,
                lat           REAL NOT NULL,
                lon           REAL NOT NULL,
                dates         TEXT NOT NULL,
                nights        INTEGER DEFAULT 0,
                highlight     INTEGER DEFAULT 0,
                photo_path    TEXT DEFAULT NULL,
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        # Migrations for existing databases
        try:
            await db.execute("ALTER TABLE trips ADD COLUMN loop_route INTEGER DEFAULT 0")
            await db.commit()
        except Exception:
            pass  # Column already exists

        await db.commit()
    finally:
        await db.close()
