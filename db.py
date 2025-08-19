import os
import sqlite3
from typing import Optional


DB_FILENAME = "ter_db.sqlite"


def get_default_db_path() -> str:
	"""Return a writable path for the SQLite database file.

	We keep data under Documents/MyWork to match existing folders used by the app.
	"""
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
CREATE TABLE IF NOT EXISTS blocks (
	id INTEGER PRIMARY KEY,
	year_level INTEGER NOT NULL,
	section TEXT NOT NULL CHECK (section IN ('A','B','C'))
);

CREATE TABLE IF NOT EXISTS departments (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	block_id INTEGER,
	FOREIGN KEY (block_id) REFERENCES blocks(id)
);

CREATE TABLE IF NOT EXISTS subjects (
	id INTEGER PRIMARY KEY,
	code TEXT NOT NULL,
	name TEXT NOT NULL,
	units REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS faculty (
	id INTEGER PRIMARY KEY,
	department_id INTEGER,
	name TEXT NOT NULL,
	rank TEXT NOT NULL CHECK (rank IN ('Instructor','Assistant Professor','Associate Professor','Professor')),
	FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS enrollments (
	id INTEGER PRIMARY KEY,
	student_id INTEGER,
	subject_id INTEGER,
	block_id INTEGER,
	FOREIGN KEY (student_id) REFERENCES students(id),
	FOREIGN KEY (subject_id) REFERENCES subjects(id),
	FOREIGN KEY (block_id) REFERENCES blocks(id)
);

CREATE TABLE IF NOT EXISTS teaching_assignments (
	id INTEGER PRIMARY KEY,
	faculty_id INTEGER,
	subject_id INTEGER,
	block_id INTEGER,
	semester TEXT,
	FOREIGN KEY (faculty_id) REFERENCES faculty(id),
	FOREIGN KEY (subject_id) REFERENCES subjects(id),
	FOREIGN KEY (block_id) REFERENCES blocks(id)
);
"""


def initialize_database(db_path: Optional[str] = None) -> str:
	"""Ensure the database file exists and schema is created. Returns the db path."""
	if db_path is None:
		db_path = get_default_db_path()
	# Ensure parent directory exists
	os.makedirs(os.path.dirname(db_path), exist_ok=True)
	with connect(db_path) as conn:
		conn.executescript(SQLITE_SCHEMA)
		conn.commit()
	return db_path


