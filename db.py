import os
import sqlite3
from typing import Optional
import shutil
from tkinter import filedialog
from datetime import datetime

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
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    suffix TEXT,
    full_name TEXT GENERATED ALWAYS AS (
        TRIM(
            first_name || ' ' ||
            COALESCE(middle_name || ' ', '') ||
            last_name ||
            CASE
                WHEN suffix IS NOT NULL AND suffix != '' THEN ' ' || suffix
                ELSE '' 
            END
        )
    ) STORED,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,              
    name TEXT NOT NULL,                     
    year_level INTEGER NOT NULL CHECK(year_level >= 1 AND year_level <= 4),  
    semester TEXT NOT NULL CHECK(semester IN ('1st', '2nd', 'Summer')),  
    department_id INTEGER,                  
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY,
    year_level INTEGER NOT NULL CHECK(year_level >= 1 AND year_level <= 4),
    section TEXT NOT NULL,
    academic_year TEXT NOT NULL,  -- e.g. "2024-2025"
    semester TEXT NOT NULL CHECK(semester IN ('1st','2nd','Summer')),
    num_students INTEGER NOT NULL DEFAULT 0,
    UNIQUE(year_level, section, academic_year, semester)
);

CREATE TABLE IF NOT EXISTS teaching_assignments (
    id INTEGER PRIMARY KEY,
    faculty_id INTEGER,
    subject_id INTEGER NOT NULL,
    block_id INTEGER NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (block_id) REFERENCES blocks(id) ON DELETE CASCADE
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


# Default file names
DB_FILENAME = "ter_db2.sqlite"
PKL_FILENAME = "results.pkl"   # <- adjust if your pickle file is named differently

def get_default_db_path() -> str:
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
    work_folder = os.path.join(documents_folder, "MyWork")
    os.makedirs(work_folder, exist_ok=True)
    return os.path.join(work_folder, DB_FILENAME)

def get_default_pkl_path() -> str:
    """Return the default path for the pickle file."""
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
    work_folder = os.path.join(documents_folder, "MyWork")
    return os.path.join(work_folder, PKL_FILENAME)

def backup_all(backup_dir: Optional[str] = None) -> str:
    """
    Create a backup of both the SQLite database and the pickle file.
    Returns the backup directory path.
    """
    db_path = get_default_db_path()
    pkl_path = get_default_pkl_path()

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"Pickle file not found: {pkl_path}")

    if backup_dir is None:
        documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
        backup_dir = os.path.join(documents_folder, "MyWork", "Backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Timestamped filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    db_backup = os.path.join(backup_dir, f"db_backup_{timestamp}.sqlite")
    pkl_backup = os.path.join(backup_dir, f"data_backup_{timestamp}.pkl")

    shutil.copy2(db_path, db_backup)
    shutil.copy2(pkl_path, pkl_backup)

    return backup_dir