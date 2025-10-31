# ------------------------------------
# db/database.py — работа с SQLite
# ------------------------------------
import os
import sqlite3
from config import DB_PATH, TRACKS_DIR, COVERS_DIR

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(TRACKS_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_cur = _conn.cursor()

_cur.execute("""
CREATE TABLE IF NOT EXISTS releases(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    track_name TEXT,
    artist TEXT,
    authors TEXT,
    description TEXT,
    release_date TEXT,
    track_file TEXT,
    cover_file TEXT,
    email TEXT,
    status TEXT
)
""")
_conn.commit()

def add_release(
    user_id: int,
    username: str,
    track_name: str,
    artist: str,
    authors: str,
    description: str,
    release_date: str,
    track_file: str,
    cover_file: str,
    email: str,
    status: str = "pending"
) -> int:
    _cur.execute("""
        INSERT INTO releases(user_id, username, track_name, artist, authors, description, release_date, track_file, cover_file, email, status)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, username, track_name, artist, authors, description, release_date, track_file, cover_file, email, status))
    _conn.commit()
    return _cur.lastrowid
