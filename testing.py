import db

def seed_subjects():
    insert_sql = """
    INSERT INTO faculty (department_id, first_name, middle_name, last_name, suffix) VALUES
-- BSIT Program
(1, 'Marc Lester', NULL, 'Acunin', NULL),
(1, 'Bryan', 'R.', 'Arellano', NULL),
(1, 'Rosemarie', 'T.', 'Bigueras', NULL),
(1, 'Mary Grace', 'B.', 'Bolos', NULL),
(1, 'Adrian', 'G.', 'Daniel', NULL),
(1, 'Sharine', 'A.', 'Gutierrez', NULL),
(1, 'Norianne', 'C.', 'Lamadrid', NULL),
(1, 'Daniel Jr.', 'E.', 'Maligat', NULL),
(1, 'Kenneth', NULL, 'Marquez', NULL),
(1, 'Roderick', 'C.', 'Tuazon', NULL),

-- BSIS Program
(1, 'Evelyn', 'M.', 'Baesa', NULL),
(1, 'Alexy Gene', 'B.', 'Castillo', NULL),
(1, 'Edgar Bryan', 'B.', 'Nicart', NULL),
(1, 'Mary Angeneth', 'A.', 'Peña', NULL),
(1, 'Edralin', 'R.', 'Raro', NULL),
(1, 'Spencer', 'S.', 'Saludes', NULL),
(1, 'Jocelyn', 'O.', 'Torio', NULL),
(1, 'Renz Alvie', 'M.', 'Tubig', NULL);


    """
    with db.connect() as conn:
        conn.executescript(insert_sql)
        conn.commit()
        print("✅ Subjects inserted successfully!")

if __name__ == "__main__":
    seed_subjects()
