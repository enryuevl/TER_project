import sqlite3
from db import get_default_db_path

db_path = get_default_db_path()
print("Using DB:", db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Turn off FKs while we reshape the table
cur.execute("PRAGMA foreign_keys = OFF;")
conn.commit()

conn.execute("BEGIN;")

# 1) Rename old join table
cur.execute("ALTER TABLE curriculum_subjects RENAME TO curriculum_subjects_old;")

# 2) Create new join table pointing to `curricula`
cur.execute("""
CREATE TABLE curriculum_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    UNIQUE (curriculum_id, subject_id),
    FOREIGN KEY (curriculum_id) REFERENCES curricula(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);
""")

# 3) Copy existing data across
cur.execute("""
INSERT INTO curriculum_subjects (id, curriculum_id, subject_id)
SELECT id, curriculum_id, subject_id
FROM curriculum_subjects_old;
""")

# 4) Drop old table
cur.execute("DROP TABLE curriculum_subjects_old;")

conn.commit()

# Re-enable foreign keys
cur.execute("PRAGMA foreign_keys = ON;")
conn.commit()
conn.close()

print("Migration complete.")
