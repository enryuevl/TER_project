import os
import sqlite3
from typing import Optional

DB_FILENAME = "ter_db2.sqlite"


def get_default_db_path() -> str:
    """Return a writable path for the SQLite database file."""
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
    work_folder = os.path.join(documents_folder, "MyWork")
    os.makedirs(work_folder, exist_ok=True)
    return os.path.join(work_folder, DB_FILENAME)


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys enforced."""
    if db_path is None:
        db_path = get_default_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rank TEXT NOT NULL CHECK (
        rank IN ('Instructor','Assistant Professor','Associate Professor','Professor')
    ),
    subrank TEXT NOT NULL CHECK (
        subrank IN ('I','II','III','IV')
    ),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);
"""



def initialize_database(db_path: Optional[str] = None) -> str:
    """Ensure the database file exists and schema is created. Returns the db path."""
    if db_path is None:
        db_path = get_default_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(SQLITE_SCHEMA)
        conn.commit()
    return db_path
