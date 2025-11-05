import os
import sqlite3
from typing import Optional
import shutil
from datetime import datetime
import json



DB_FILENAME = "ter_db2.sqlite"
PKL_FILENAME = "results.pkl"  


def get_default_db_path() -> str:
    """Return a writable path for the SQLite database file."""
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
    work_folder = os.path.join(documents_folder, "MyWork")
    os.makedirs(work_folder, exist_ok=True)
    return os.path.join(work_folder, DB_FILENAME)


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_default_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn



SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;

-- =========================
-- 1) Departments & Faculty
-- =========================
CREATE TABLE IF NOT EXISTS departments (
  id        INTEGER PRIMARY KEY,
  code      TEXT UNIQUE,                     -- e.g., CCMS, CBPA
  name      TEXT NOT NULL UNIQUE,
  dean_id   INTEGER UNIQUE                   -- dean must be a faculty in this dept (triggers below)
);

CREATE TABLE IF NOT EXISTS faculty (
  id            INTEGER PRIMARY KEY,
  employee_no   TEXT UNIQUE,
  first_name    TEXT NOT NULL,
  middle_name   TEXT,
  last_name     TEXT NOT NULL,
  suffix        TEXT,
  full_name     TEXT GENERATED ALWAYS AS (
    TRIM(
      first_name || ' ' ||
      COALESCE(middle_name || ' ', '') ||
      last_name ||
      CASE WHEN suffix IS NOT NULL AND suffix <> '' THEN ' ' || suffix ELSE '' END
    )
  ) STORED,
  department_id INTEGER NOT NULL,
  role          TEXT,                        -- e.g., 'Instructor','Dean','Chair'
  is_dean       INTEGER NOT NULL DEFAULT 0,
  is_active     INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- Dean integrity: dean must exist and belong to same department
CREATE TRIGGER IF NOT EXISTS trg_dept_dean_check_ins
AFTER INSERT ON departments
FOR EACH ROW
WHEN NEW.dean_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'Dean must reference an existing faculty')
  WHERE NOT EXISTS (SELECT 1 FROM faculty WHERE id = NEW.dean_id);

  SELECT RAISE(ABORT, 'Dean must belong to the same department')
  WHERE EXISTS (SELECT 1 FROM faculty WHERE id = NEW.dean_id AND department_id <> NEW.id);
END;

CREATE TRIGGER IF NOT EXISTS trg_dept_dean_check_upd
AFTER UPDATE OF dean_id ON departments
FOR EACH ROW
WHEN NEW.dean_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'Dean must reference an existing faculty')
  WHERE NOT EXISTS (SELECT 1 FROM faculty WHERE id = NEW.dean_id);

  SELECT RAISE(ABORT, 'Dean must belong to the same department')
  WHERE EXISTS (SELECT 1 FROM faculty WHERE id = NEW.dean_id AND department_id <> NEW.id);
END;

-- =========================
-- 2) Programs & Subjects
-- =========================
CREATE TABLE IF NOT EXISTS programs (
  id            INTEGER PRIMARY KEY,
  code          TEXT NOT NULL UNIQUE,           -- e.g., BSIT, BSA
  name          TEXT NOT NULL,
  department_id INTEGER NOT NULL,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subjects (
  id            INTEGER PRIMARY KEY,
  code          TEXT NOT NULL UNIQUE,           -- globally unique
  title         TEXT NOT NULL,
  units         INTEGER DEFAULT 3,
  year_level    INTEGER NOT NULL CHECK (year_level BETWEEN 1 AND 4),
  semester      TEXT NOT NULL CHECK (semester IN ('1st','2nd','Summer')),  -- catalog semester
  program_id    INTEGER NOT NULL,
  department_id INTEGER,                        -- optional shortcut
  FOREIGN KEY (program_id)    REFERENCES programs(id)    ON DELETE CASCADE,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- =========================
-- 3) Blocks (program/year specific per term)
-- =========================
CREATE TABLE IF NOT EXISTS blocks (
  id            INTEGER PRIMARY KEY,
  program_id    INTEGER NOT NULL,
  year_level    INTEGER NOT NULL CHECK (year_level BETWEEN 1 AND 4),
  section       TEXT NOT NULL,                  -- 'A','B','C',...
  academic_year TEXT NOT NULL,                  -- 'YYYY-YYYY'
  semester      TEXT NOT NULL CHECK (semester IN ('1st','2nd','Summer')),
  UNIQUE (program_id, year_level, section, academic_year, semester),
  FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
);

-- =========================
-- 4) Teaching Assignments (per term)
-- =========================
CREATE TABLE IF NOT EXISTS teaching_assignments (
  id                INTEGER PRIMARY KEY,
  teacher_id        INTEGER NOT NULL,
  subject_id        INTEGER NOT NULL,
  block_id          INTEGER,                    -- NULL = merged/multi-block class
  academic_year     TEXT NOT NULL,              -- 'YYYY-YYYY'
  semester          TEXT NOT NULL CHECK (semester IN ('1st','2nd','Summer')),
  expected_students INTEGER NOT NULL DEFAULT 0 CHECK(expected_students >= 0), -- target # of student raters
  FOREIGN KEY (teacher_id) REFERENCES faculty(id)  ON DELETE CASCADE,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  FOREIGN KEY (block_id)   REFERENCES blocks(id)   ON DELETE CASCADE
);

-- Prevent duplicate assignments
CREATE UNIQUE INDEX IF NOT EXISTS ux_ta_nullblock
  ON teaching_assignments(teacher_id, subject_id, academic_year, semester)
  WHERE block_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_ta_blocked
  ON teaching_assignments(teacher_id, subject_id, academic_year, semester, block_id)
  WHERE block_id IS NOT NULL;

-- =========================
-- 5) Integrity: Block ↔ Subject/Term Consistency
-- =========================
-- INSERT case
CREATE TRIGGER IF NOT EXISTS trg_ta_block_consistency_ins
BEFORE INSERT ON teaching_assignments
FOR EACH ROW
WHEN NEW.block_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'Block does not exist')
  WHERE NOT EXISTS (SELECT 1 FROM blocks WHERE id = NEW.block_id);

  SELECT RAISE(ABORT, 'Subject does not exist')
  WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE id = NEW.subject_id);

  SELECT RAISE(ABORT, 'Block/Subject/Term mismatch')
  WHERE NOT EXISTS (
    SELECT 1
    FROM blocks b
    JOIN subjects s ON s.id = NEW.subject_id
    WHERE b.id = NEW.block_id
      AND b.program_id    = s.program_id
      AND b.year_level    = s.year_level
      AND b.academic_year = NEW.academic_year
      AND b.semester      = NEW.semester
  );
END;

-- UPDATE case
CREATE TRIGGER IF NOT EXISTS trg_ta_block_consistency_upd
BEFORE UPDATE OF block_id, subject_id, academic_year, semester ON teaching_assignments
FOR EACH ROW
WHEN NEW.block_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'Block does not exist')
  WHERE NOT EXISTS (SELECT 1 FROM blocks WHERE id = NEW.block_id);

  SELECT RAISE(ABORT, 'Subject does not exist')
  WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE id = NEW.subject_id);

  SELECT RAISE(ABORT, 'Block/Subject/Term mismatch')
  WHERE NOT EXISTS (
    SELECT 1
    FROM blocks b
    JOIN subjects s ON s.id = NEW.subject_id
    WHERE b.id = NEW.block_id
      AND b.program_id    = s.program_id
      AND b.year_level    = s.year_level
      AND b.academic_year = NEW.academic_year
      AND b.semester      = NEW.semester
  );
END;


-- =========================
-- 6) Helpful Indexes
-- =========================
CREATE INDEX IF NOT EXISTS ix_faculty_dept          ON faculty(department_id);
CREATE INDEX IF NOT EXISTS ix_programs_dept         ON programs(department_id);
CREATE INDEX IF NOT EXISTS ix_subjects_prog_sem     ON subjects(program_id, year_level, semester);
CREATE INDEX IF NOT EXISTS ix_blocks_prog_term      ON blocks(program_id, academic_year, semester);
CREATE INDEX IF NOT EXISTS ix_ta_teacher_term       ON teaching_assignments(teacher_id, academic_year, semester);
CREATE INDEX IF NOT EXISTS ix_ta_subject_term       ON teaching_assignments(subject_id, academic_year, semester);

-- =========================
-- 7) Users / Login Accounts
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id             INTEGER PRIMARY KEY,
  username       TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,                         -- store bcrypt/argon2 hash
  role           TEXT NOT NULL CHECK (role IN ('operator','dean','admin')),
  department_id  INTEGER,                               -- required for operator/dean, NULL for admin
  is_active      INTEGER NOT NULL DEFAULT 1,
  last_login_at  TEXT,                                  -- optional
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_department      ON users(department_id);

-- Enforce department scoping rules
DROP TRIGGER IF EXISTS trg_users_role_dept_ins;
DROP TRIGGER IF EXISTS trg_users_role_dept_upd;

-- INSERT: operator/dean must have a department; admin must NOT have a department
CREATE TRIGGER IF NOT EXISTS trg_users_role_dept_ins
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
  -- operator/dean must have dept
  SELECT RAISE(ABORT, 'Department required for operator/dean')
  WHERE NEW.role IN ('operator','dean') AND NEW.department_id IS NULL;

  -- admin must not have dept (keep admin global)
  SELECT RAISE(ABORT, 'Admin must not have a department')
  WHERE NEW.role = 'admin' AND NEW.department_id IS NOT NULL;
END;

-- UPDATE: same rules on change
CREATE TRIGGER IF NOT EXISTS trg_users_role_dept_upd
BEFORE UPDATE OF role, department_id ON users
FOR EACH ROW
BEGIN
  SELECT RAISE(ABORT, 'Department required for operator/dean')
  WHERE NEW.role IN ('operator','dean') AND NEW.department_id IS NULL;

  SELECT RAISE(ABORT, 'Admin must not have a department')
  WHERE NEW.role = 'admin' AND NEW.department_id IS NOT NULL;
END;


"""


def initialize_database(db_path: Optional[str] = None) -> str:
    """Ensure the database file exists and schema is created. Returns the db path."""
    if db_path is None:
        db_path = get_default_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(SQLITE_SCHEMA)
        migrate_to_current_schema(conn)
        conn.commit()
    return db_path

def _colnames(conn, table: str) -> set:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}  # column names

# --- Activity Logs -----------------------------------------------------------


def _ensure_activity_logs(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id             INTEGER PRIMARY KEY,
            occurred_at    TEXT NOT NULL DEFAULT (datetime('now')),
            action         TEXT NOT NULL,           -- e.g. 'scan_started','scan_completed','export_summary'
            actor_name     TEXT,
            actor_role     TEXT,
            department_id  INTEGER,
            teacher_name   TEXT,
            rater_type     TEXT,
            file_name      TEXT,
            details_json   TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_time ON activity_logs(occurred_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_action ON activity_logs(action)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_actor  ON activity_logs(actor_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_logs_teacher ON activity_logs(teacher_name)")
    conn.commit()

def log_activity(
    action: str,
    actor_name: str | None = None,
    actor_role: str | None = None,
    department_id: int | None = None,
    teacher_name: str | None = None,
    rater_type: str | None = None,
    file_name: str | None = None,
    details: dict | None = None,
) -> None:
    try:
        with connect() as conn:
            conn.execute("""
                INSERT INTO activity_logs
                (action, actor_name, actor_role, department_id, teacher_name, rater_type, file_name, details_json)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                action,
                actor_name,
                actor_role,
                department_id,
                teacher_name,
                rater_type,
                file_name,
                json.dumps(details or {})
            ))
            conn.commit()
    except Exception as e:
        print(f"⚠️ log_activity failed: {e}")

def fetch_activity_logs(limit: int = 200, where: str = "", params: tuple = ()):
    with connect() as conn:
        q = "SELECT occurred_at, action, actor_name, actor_role, teacher_name, rater_type, file_name, details_json FROM activity_logs"
        if where:
            q += " WHERE " + where
        q += " ORDER BY occurred_at DESC LIMIT ?"
        rows = conn.execute(q, params + (limit,)).fetchall()
    return rows


def migrate_to_current_schema(conn: sqlite3.Connection) -> None:
    # 1) subjects: ensure 'title' exists (copy from legacy 'name' if present)
    cols = _colnames(conn, "subjects")
    if "title" not in cols:
        conn.execute("ALTER TABLE subjects ADD COLUMN title TEXT")
        if "name" in cols:
            conn.execute("UPDATE subjects SET title = name WHERE title IS NULL")
        conn.commit()

    # 2) teaching_assignments: ensure new columns exist
    cols = _colnames(conn, "teaching_assignments")
    if "academic_year" not in cols:
        conn.execute("ALTER TABLE teaching_assignments ADD COLUMN academic_year TEXT")
    if "semester" not in cols:
        conn.execute("ALTER TABLE teaching_assignments ADD COLUMN semester TEXT")
    if "expected_students" not in cols:
        conn.execute("ALTER TABLE teaching_assignments ADD COLUMN expected_students INTEGER DEFAULT 0")
    conn.commit()
    _ensure_activity_logs(conn)
    _safe_ensure_curriculum_schema(conn)
     # optional – idempotent
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS curriculum (
          id INTEGER PRIMARY KEY,
          program_id INTEGER NOT NULL,
          academic_year TEXT NOT NULL,
          semester TEXT NOT NULL CHECK (semester IN ('1st','2nd','Summer')),
          UNIQUE (program_id, academic_year, semester),
          FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS curriculum_subjects (
          id INTEGER PRIMARY KEY,
          curriculum_id INTEGER NOT NULL,
          subject_id INTEGER NOT NULL,
          UNIQUE (curriculum_id, subject_id),
          FOREIGN KEY (curriculum_id) REFERENCES curriculum(id) ON DELETE CASCADE,
          FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS ix_curriculum_prog_term
          ON curriculum(program_id, academic_year, semester);
        CREATE INDEX IF NOT EXISTS ix_currsubj_curriculum
          ON curriculum_subjects(curriculum_id);
        CREATE INDEX IF NOT EXISTS ix_currsubj_subject
          ON curriculum_subjects(subject_id);
    """)
    conn.commit()


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
  
def _safe_ensure_curriculum_schema(conn: sqlite3.Connection) -> None:
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS curriculum (
            id INTEGER PRIMARY KEY,
            program_id INTEGER NOT NULL,
            academic_year TEXT NOT NULL,
            semester TEXT NOT NULL CHECK (semester IN ('1st','2nd','Summer')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(program_id, academic_year, semester),
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        )
    """)

    # curriculum_subjects — detect bad/old schema and repair
    cols = _colnames(conn, "curriculum_subjects")
    if not cols:
        # brand-new: create correctly
        conn.execute("""
            CREATE TABLE IF NOT EXISTS curriculum_subjects (
                id INTEGER PRIMARY KEY,
                curriculum_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                UNIQUE (curriculum_id, subject_id),
                FOREIGN KEY (curriculum_id) REFERENCES curriculum(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id)     REFERENCES subjects(id)     ON DELETE CASCADE
            )
        """)
    else:
        needed = {"id", "curriculum_id", "subject_id"}
        if not needed.issubset(cols):
            # rename old table → create correct one → migrate what we can → drop old
            conn.execute("ALTER TABLE curriculum_subjects RENAME TO curriculum_subjects_old")
            conn.execute("""
                CREATE TABLE curriculum_subjects (
                    id INTEGER PRIMARY KEY,
                    curriculum_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    UNIQUE (curriculum_id, subject_id),
                    FOREIGN KEY (curriculum_id) REFERENCES curriculum(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id)     REFERENCES subjects(id)     ON DELETE CASCADE
                )
            """)
            oldcols = _colnames(conn, "curriculum_subjects_old")
            # best-effort copy if old had 'curriculum' and 'subject' column names
            if {"curriculum", "subject"}.issubset(oldcols):
                conn.execute("""
                    INSERT OR IGNORE INTO curriculum_subjects (curriculum_id, subject_id)
                    SELECT curriculum, subject FROM curriculum_subjects_old
                """)
            # if the old names were different, we skip migration (table was probably empty)
            conn.execute("DROP TABLE curriculum_subjects_old")

    # indexes (safe to repeat)
    conn.execute("""CREATE INDEX IF NOT EXISTS ix_curriculum_prog_term
                    ON curriculum(program_id, academic_year, semester)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS ix_currsubj_curriculum
                    ON curriculum_subjects(curriculum_id)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS ix_currsubj_subject
                    ON curriculum_subjects(subject_id)""")
    conn.commit()
