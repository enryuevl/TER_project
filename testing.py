# seed_faculty_simple.py
import sqlite3
import db  # uses your existing connect() with PRAGMAs

# ---------- set your department here ----------
DEPT_CODE = "CCMS"
DEPT_NAME = "College of Computing and Multimedia Studies"
# ---------------------------------------------

# (first_name, middle_name, last_name, suffix)
FACULTY = [
    # BSIT list
    ("Marc Lester",  None,    "Acuñin",   None),
    ("Bryan",        "R.",    "Arellano", None),
    ("Rosemarie",    "T.",    "Bigueras", None),
    ("Mary Grace",   "B.",    "Bolos",    None),
    ("Adrian",       "G.",    "Daniel",   None),
    ("Sharine",      "A.",    "Gutierrez",None),
    ("Norianne",     "C.",    "Lamadrid", None),
    ("Daniel",       "E.",    "Maligat",  "Jr."),
    ("Kenneth",      None,    "Marquez",  None),
    ("Roderick",     "C.",    "Tuazon",   None),

    # BSIS list
    ("Evelyn",       "M.",    "Baesa",    None),
    ("Alexy Gene",   "B.",    "Castillo", None),
    ("Edgar Bryan",  "B.",    "Nicart",   None),
    ("Mary Angeneth","A.",    "Peña",     None),
    ("Edralin",      "R.",    "Raro",     None),
    ("Spencer",      "S.",    "Saludes",  None),
    ("Jocelyn",      "O.",    "Torio",    None),
    ("Renz Alvie",   "M.",    "Tubig",    None),
]

def ensure_department(conn: sqlite3.Connection, code: str, name: str) -> int:
    row = conn.execute(
        "SELECT id FROM departments WHERE code = ? OR name = ?",
        (code, name)
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO departments (code, name) VALUES (?, ?)",
        (code, name)
    )
    return cur.lastrowid

def faculty_exists(conn: sqlite3.Connection, first, middle, last, suffix, dept_id) -> bool:
    return conn.execute(
        """
        SELECT 1 FROM faculty
        WHERE first_name = ? AND COALESCE(middle_name,'') = COALESCE(?, '')
          AND last_name  = ? AND COALESCE(suffix,'')      = COALESCE(?, '')
          AND department_id = ?
        """,
        (first, middle, last, suffix, dept_id)
    ).fetchone() is not None

def insert_faculty(conn: sqlite3.Connection, first, middle, last, suffix, dept_id):
    conn.execute(
        """
        INSERT INTO faculty (first_name, middle_name, last_name, suffix, department_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (first, middle, last, suffix, dept_id)
    )

def seed():
    with db.connect() as conn:
        conn.execute("BEGIN")
        try:
            dept_id = ensure_department(conn, DEPT_CODE, DEPT_NAME)
            added, skipped = 0, 0
            for first, middle, last, suffix in FACULTY:
                if faculty_exists(conn, first, middle, last, suffix, dept_id):
                    skipped += 1
                    continue
                insert_faculty(conn, first, middle, last, suffix, dept_id)
                added += 1
            conn.commit()
            print(f"✅ Faculty seeding complete. Added: {added}, Skipped(existing): {skipped}. Department ID={dept_id}")
        except Exception as e:
            conn.rollback()
            raise

if __name__ == "__main__":
    seed()
