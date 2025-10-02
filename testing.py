import db

def seed_subjects():
    insert_sql = """
    INSERT INTO subjects (code, name, year_level, semester, department_id) VALUES
-- 1st Year, 1st Semester
('IT 100-1', 'Introduction to Computing', 1, '1st', 1),
('IT 101-1', 'Computer Programming 1', 1, '1st', 1),
('GEC 1', 'Understanding the Self', 1, '1st', 1),
('GEC 2', 'Readings in Philippine History', 1, '1st', 1),
('GEC 3', 'Mathematics in the Modern World', 1, '1st', 1),
('PATHFIT 1', 'Movement Competency Training', 1, '1st', 1),
('NSTP 1', 'ROTC/LTS/CWTS', 1, '1st', 1),

-- 1st Year, 2nd Semester
('IT 102-K', 'Computer Programming 2', 1, '2nd', 1),
('IT 103-I', 'Data Structures and Algorithms', 1, '2nd', 1),
('IT 104-I', 'Discrete Mathematics', 1, '2nd', 1),
('GEC 4', 'Purposive Communication', 1, '2nd', 1),
('GE ELECTIVE 7', 'Art Appreciation', 1, '2nd', 1),
('GEC 8', 'Environmental Science', 1, '2nd', 1),
('PATHFIT 2', 'Exercise-based Fitness Activities', 1, '2nd', 1),
('NSTP 2', 'ROTC/LTS/CWTS', 1, '2nd', 1),

-- 2nd Year, 1st Semester
('IT 105-I', 'Application Development and Emerging Technologies', 2, '1st', 1),
('IT 106-I', 'Information Management', 2, '1st', 1),
('IT 107-I', 'Introduction to Human Computer Interaction', 2, '1st', 1),
('IT 108-I', 'Operating System', 2, '1st', 1),
('GEC 6', 'Science, Technology, and Society', 2, '1st', 1),
('GEC 7A', 'Ethics', 2, '1st', 1),
('GE ELECTIVE 5', 'The Entrepreneurial Mind', 2, '1st', 1),
('PATHFIT 3', 'Dance / Sports / Martial Arts / Group Exercise / Outdoor and Adventure Activities', 2, '1st', 1),

-- 2nd Year, 2nd Semester
('GEC 9', 'The Contemporary World', 2, '2nd', 1),
('IT 109-I', 'Fundamentals of Database Systems', 2, '2nd', 1),
('IT 110-I', 'Computer Architecture and Robotics', 2, '2nd', 1),
('IT 111-I', 'Integrative Programming and Technologies 1', 2, '2nd', 1),
('IT 112-I', 'Mobile Applications', 2, '2nd', 1),
('IT 113-I', 'Information Assurance and Security 1', 2, '2nd', 1),
('GE ELECTIVE 6', 'Reading Visual Art', 2, '2nd', 1),
('PATHFIT 4', 'Menu of Dance, Sports, Martial Arts, Group Exercise, Outdoor and Adventure Activities', 2, '2nd', 1),

-- 3rd Year, 1st Semester
('IT 114-1', 'Quantitative Methods (Modeling and Simulation)', 3, '1st', 1),
('IT 115-I', 'Networking 1', 3, '1st', 1),
('IT 116-I', 'System Analysis and Design', 3, '1st', 1),
('IT 117-I', 'System Administration and Maintenance', 3, '1st', 1),
('IT 118-I', 'Internet of Things', 3, '1st', 1),
('IT 119-I', 'Data Scalability and Analytics', 3, '1st', 1),
('GEC 10', 'Ang Buhay at mga Akda ni Rizal', 3, '1st', 1),

-- 3rd Year, 2nd Semester
('IT 120-1', 'Networking 2', 3, '2nd', 1),
('IT 121-1', 'Capstone Project and Research 1', 3, '2nd', 1),
('IT 122-1', 'System Integration and Architecture 1', 3, '2nd', 1),
('IT 123-1', 'Information Assurance and Security 2', 3, '2nd', 1),
('ITELECT 001-1', 'IT Elective 1', 3, '2nd', 1),
('ITELECT 002-1', 'IT Elective 2', 3, '2nd', 1),

-- 4th Year, 1st Semester
('ITELECT 003-1', 'IT Elective 3', 4, '1st', 1),
('ITELECT 004-1', 'IT Elective 4', 4, '1st', 1),
('IT 124-1', 'Social and Professional Issues in Computing', 4, '1st', 1),
('IT 125-1', 'Capstone Project and Research 2', 4, '1st', 1),
('IT 126-1', 'Cyber Security and Principle', 4, '1st', 1),
('IT 127-1', 'Global Professional Practice', 4, '1st', 1),

-- 4th Year, 2nd Semester
('IT 128-1', 'Practicum', 4, '2nd', 1);



    """
    with db.connect() as conn:
        conn.executescript(insert_sql)
        conn.commit()
        print("✅ Subjects inserted successfully!")

if __name__ == "__main__":
    seed_subjects()
