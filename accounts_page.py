from customtkinter import *
from CTkTable import CTkTable
from PIL import Image, ImageTk
from tkinter import messagebox, ttk, filedialog

def acc_page(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    container = CTkFrame(master=main_frame, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = CTkLabel(
        container, 
        text="Database Management", 
        font=("Arial", 24, "bold"), 
        text_color="#691612"
    )
    title_label.pack(pady=(0, 20))
    
    # Create tabs for different entity types
    tab_frame = CTkFrame(container, fg_color="transparent")
    tab_frame.pack(fill="x", pady=(0, 20))
    
    # Tab buttons
    tab_buttons = {}
    tab_content = {}
    
    entities = ["Students", "Faculty", "Departments", "Subjects", "Blocks", "Teaching Assignments", "Enrollments"]
    
    for i, entity in enumerate(entities):
        btn = CTkButton(
            tab_frame,
            text=entity,
            command=lambda e=entity: show_tab(e),
            fg_color="#AC5353" if i == 0 else "#F1F3F5",
            text_color="#FFFFFF" if i == 0 else "#333333",
            hover_color="#BF3131" if i == 0 else "#E9ECEF",
            width=120,
            height=35,
            corner_radius=8
        )
        btn.pack(side="left", padx=5)
        tab_buttons[entity] = btn
    
    # Content area
    content_frame = CTkFrame(container, fg_color="#FFFFFF", corner_radius=10)
    content_frame.pack(fill="both", expand=True)
    
    # Success message indicator (non-blocking)
    success_frame = CTkFrame(container, fg_color="#10B981", corner_radius=8, height=0)
    success_frame.pack(fill="x", pady=(0, 10))
    success_frame.pack_propagate(False)
    
    success_label = CTkLabel(
        success_frame, 
        text="", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    )
    success_label.pack(pady=10)
    
    def show_success_message(message):
        success_label.configure(text=message)
        success_frame.configure(height=50)
        # Auto-hide after 3 seconds
        container.after(3000, lambda: success_frame.configure(height=0))
    
    def show_tab(entity_name):
        # Update button colors
        for name, btn in tab_buttons.items():
            if name == entity_name:
                btn.configure(fg_color="#AC5353", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#F1F3F5", text_color="#333333")
        
        # Clear content and show new form
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        if entity_name == "Students":
            show_student_form()
        elif entity_name == "Faculty":
            show_faculty_form()
        elif entity_name == "Departments":
            show_department_form()
        elif entity_name == "Subjects":
            show_subject_form()
        elif entity_name == "Blocks":
            show_block_form()
        elif entity_name == "Teaching Assignments":
            show_teaching_assignment_form()
        elif entity_name == "Enrollments":
            show_enrollment_form()
    
    def show_student_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        CTkLabel(
            form_frame, 
            text="Add New Student", 
            font=("Arial", 20, "bold"), 
        text_color="#691612"
        ).pack(pady=(0, 20))
        
        # Form fields
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Student name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Student Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Block selection
        block_frame = CTkFrame(fields_frame, fg_color="transparent")
        block_frame.pack(fill="x", pady=10)
        CTkLabel(block_frame, text="Block:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        # Get blocks from database
        blocks = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, year_level, section FROM blocks")
                blocks = cursor.fetchall()
        except:
            pass
        
        if blocks:
            block_options = [f"Year {b[1]} - Section {b[2]}" for b in blocks]
            block_var = StringVar()
            block_dropdown = CTkOptionMenu(
                block_frame,
                variable=block_var,
                values=block_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            block_dropdown.pack(fill="x", pady=(5, 0))
            if block_options:
                block_dropdown.set(block_options[0])
        else:
            CTkLabel(block_frame, text="No blocks available. Create blocks first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Student",
            command=lambda: add_student(name_entry.get(), block_var.get() if 'block_var' in locals() else None),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_faculty_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Faculty Member", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Faculty name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Faculty Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Department selection
        dept_frame = CTkFrame(fields_frame, fg_color="transparent")
        dept_frame.pack(fill="x", pady=10)
        CTkLabel(dept_frame, text="Department:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        departments = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM departments")
                departments = cursor.fetchall()
        except:
            pass
        
        if departments:
            dept_options = [d[1] for d in departments]
            dept_var = StringVar()
            dept_dropdown = CTkOptionMenu(
                dept_frame,
                variable=dept_var,
                values=dept_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            dept_dropdown.pack(fill="x", pady=(5, 0))
            dept_dropdown.set(dept_options[0])
        else:
            CTkLabel(dept_frame, text="No departments available. Create departments first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Rank selection
        rank_frame = CTkFrame(fields_frame, fg_color="transparent")
        rank_frame.pack(fill="x", pady=10)
        CTkLabel(rank_frame, text="Rank:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        rank_var = StringVar()
        rank_dropdown = CTkOptionMenu(
            rank_frame,
            variable=rank_var,
            values=["Instructor", "Assistant Professor", "Associate Professor", "Professor"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        rank_dropdown.pack(fill="x", pady=(5, 0))
        rank_dropdown.set("Instructor")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Faculty Member",
            command=lambda: add_faculty(name_entry.get(), dept_var.get() if 'dept_var' in locals() else None, rank_var.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
        font=("Arial", 14, "bold"), 
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_department_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Department", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Department name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Department Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Department",
            command=lambda: add_department(name_entry.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_subject_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Subject", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Subject code
        code_frame = CTkFrame(fields_frame, fg_color="transparent")
        code_frame.pack(fill="x", pady=10)
        CTkLabel(code_frame, text="Subject Code:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        code_entry = CTkEntry(code_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        code_entry.pack(fill="x", pady=(5, 0))
        
        # Subject name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Subject Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Units
        units_frame = CTkFrame(fields_frame, fg_color="transparent")
        units_frame.pack(fill="x", pady=10)
        CTkLabel(units_frame, text="Units:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        units_entry = CTkEntry(units_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        units_entry.pack(fill="x", pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Subject",
            command=lambda: add_subject(code_entry.get(), name_entry.get(), units_entry.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_block_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Block", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Year level
        year_frame = CTkFrame(fields_frame, fg_color="transparent")
        year_frame.pack(fill="x", pady=10)
        CTkLabel(year_frame, text="Year Level:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        year_entry = CTkEntry(year_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        year_entry.pack(fill="x", pady=(5, 0))
        
        # Section
        section_frame = CTkFrame(fields_frame, fg_color="transparent")
        section_frame.pack(fill="x", pady=10)
        CTkLabel(section_frame, text="Section:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        section_var = StringVar()
        section_dropdown = CTkOptionMenu(
            section_frame,
            variable=section_var,
            values=["A", "B", "C"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        section_dropdown.pack(fill="x", pady=(5, 0))
        section_dropdown.set("A")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Block",
            command=lambda: add_block(year_entry.get(), section_var.get()),
            fg_color="#691612",
            hover_color="#AC5353",
                text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    # Database functions
    def add_student(name, block_info):
        if not name:
            messagebox.showerror("Error", "Please enter student name")
            return

        try:
            import db
            with db.connect() as conn:
                if block_info:
                    # Extract block ID from the display text
                    block_parts = block_info.split(" - Section ")
                    year = int(block_parts[0].replace("Year ", ""))
                    section = block_parts[1]

                    cursor = conn.execute(
                        "SELECT id FROM blocks WHERE year_level = ? AND section = ?",
                        (year, section)
                    )
                    block_id = cursor.fetchone()

                    if block_id:
                        conn.execute(
                            "INSERT INTO students (name, block_id) VALUES (?, ?)",
                            (name, block_id[0])
                        )
                        conn.commit()
                        show_success_message(f"Student '{name}' added successfully!")
                    else:
                        messagebox.showerror("Error", "Selected block not found")
                else:
                    # No block info provided, insert student without block_id
                    conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
                    conn.commit()
                    show_success_message(f"Student '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add student: {str(e)}")

    
    def add_faculty(name, dept_name, rank):
        if not name:
            messagebox.showerror("Error", "Please enter faculty name")
            return
        
        try:
            import db
            with db.connect() as conn:
                if dept_name:
                    cursor = conn.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
                    dept_id = cursor.fetchone()
                    
                    if dept_id:
                        conn.execute("INSERT INTO faculty (name, department_id, rank) VALUES (?, ?, ?)", (name, dept_id[0], rank))
                        conn.commit()
                        show_success_message(f"Faculty member '{name}' added successfully!")
                    else:
                        messagebox.showerror("Error", "Selected department not found")
                else:
                    conn.execute("INSERT INTO faculty (name, rank) VALUES (?, ?)", (name, rank))
                    conn.commit()
                    show_success_message(f"Faculty member '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add faculty member: {str(e)}")
    
    def add_department(name):
        if not name:
            messagebox.showerror("Error", "Please enter department name")
            return
        
        try:
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
                conn.commit()
                show_success_message(f"Department '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add department: {str(e)}")
    
    def add_subject(code, name, units):
        if not all([code, name, units]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            units_float = float(units)
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO subjects (code, name, units) VALUES (?, ?, ?)", (code, name, units_float))
                conn.commit()
                show_success_message(f"Subject '{name}' added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Units must be a valid number")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add subject: {str(e)}")
    
    def add_block(year, section):
        if not year:
            messagebox.showerror("Error", "Please enter year level")
            return
        
        try:
            year_int = int(year)
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO blocks (year_level, section) VALUES (?, ?)", (year_int, section))
                conn.commit()
                show_success_message(f"Block Year {year_int} Section {section} added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Year level must be a valid number")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add block: {str(e)}")
    
    def show_teaching_assignment_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Teaching Assignment", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Faculty selection
        faculty_frame = CTkFrame(fields_frame, fg_color="transparent")
        faculty_frame.pack(fill="x", pady=10)
        CTkLabel(faculty_frame, text="Faculty Member:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        faculty_members = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM faculty")
                faculty_members = cursor.fetchall()
        except:
            pass
        
        if faculty_members:
            faculty_options = [f[1] for f in faculty_members]
            faculty_var = StringVar()
            faculty_dropdown = CTkOptionMenu(
                faculty_frame,
                variable=faculty_var,
                values=faculty_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            faculty_dropdown.pack(fill="x", pady=(5, 0))
            faculty_dropdown.set(faculty_options[0])
        else:
            CTkLabel(faculty_frame, text="No faculty members available. Create faculty first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Subject selection
        subject_frame = CTkFrame(fields_frame, fg_color="transparent")
        subject_frame.pack(fill="x", pady=10)
        CTkLabel(subject_frame, text="Subject:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        subjects = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, code, name FROM subjects")
                subjects = cursor.fetchall()
        except:
            pass
        
        if subjects:
            subject_options = [f"{s[1]} - {s[2]}" for s in subjects]
            subject_var = StringVar()
            subject_dropdown = CTkOptionMenu(
                subject_frame,
                variable=subject_var,
                values=subject_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            subject_dropdown.pack(fill="x", pady=(5, 0))
            subject_dropdown.set(subject_options[0])
        else:
            CTkLabel(subject_frame, text="No subjects available. Create subjects first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Block selection
        block_frame = CTkFrame(fields_frame, fg_color="transparent")
        block_frame.pack(fill="x", pady=10)
        CTkLabel(block_frame, text="Block:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        blocks = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, year_level, section FROM blocks")
                blocks = cursor.fetchall()
        except:
            pass
        
        if blocks:
            block_options = [f"Year {b[1]} - Section {b[2]}" for b in blocks]
            block_var = StringVar()
            block_dropdown = CTkOptionMenu(
                block_frame,
                variable=block_var,
                values=block_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            block_dropdown.pack(fill="x", pady=(5, 0))
            if block_options:
                block_dropdown.set(block_options[0])
        else:
            CTkLabel(block_frame, text="No blocks available. Create blocks first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Semester
        semester_frame = CTkFrame(fields_frame, fg_color="transparent")
        semester_frame.pack(fill="x", pady=10)
        CTkLabel(semester_frame, text="Semester:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        semester_var = StringVar()
        semester_dropdown = CTkOptionMenu(
            semester_frame,
            variable=semester_var,
            values=["First Semester", "Second Semester", "Summer"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        semester_dropdown.pack(fill="x", pady=(5, 0))
        semester_dropdown.set("First Semester")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Teaching Assignment",
            command=lambda: add_teaching_assignment(
                faculty_var.get() if 'faculty_var' in locals() else None,
                subject_var.get() if 'subject_var' in locals() else None,
                block_var.get() if 'block_var' in locals() else None,
                semester_var.get()
            ),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def add_teaching_assignment(faculty_name, subject_info, block_info, semester):
        if not all([faculty_name, subject_info, block_info]):
            messagebox.showerror("Error", "Please select faculty, subject, and block")
            return
        
        try:
            import db
            with db.connect() as conn:
                # Get faculty ID
                cursor = conn.execute("SELECT id FROM faculty WHERE name = ?", (faculty_name,))
                faculty_id = cursor.fetchone()
                
                if not faculty_id:
                    messagebox.showerror("Error", "Selected faculty member not found")
                    return
                
                # Get subject ID
                subject_code = subject_info.split(" - ")[0]
                cursor = conn.execute("SELECT id FROM subjects WHERE code = ?", (subject_code,))
                subject_id = cursor.fetchone()
                
                if not subject_id:
                    messagebox.showerror("Error", "Selected subject not found")
                    return
                
                # Get block ID
                block_parts = block_info.split(" - Section ")
                year = int(block_parts[0].replace("Year ", ""))
                section = block_parts[1]
                
                cursor = conn.execute("SELECT id FROM blocks WHERE year_level = ? AND section = ?", (year, section))
                block_id = cursor.fetchone()
                
                if not block_id:
                    messagebox.showerror("Error", "Selected block not found")
                    return
                
                # Insert teaching assignment
                conn.execute(
                    "INSERT INTO teaching_assignments (faculty_id, subject_id, block_id, semester) VALUES (?, ?, ?, ?)",
                    (faculty_id[0], subject_id[0], block_id[0], semester)
                )
                conn.commit()
                show_success_message(f"Teaching assignment for {faculty_name} added successfully!")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add teaching assignment: {str(e)}")
    
    def show_enrollment_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Enrollment", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Student selection
        student_frame = CTkFrame(fields_frame, fg_color="transparent")
        student_frame.pack(fill="x", pady=10)
        CTkLabel(student_frame, text="Student:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        students = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM students")
                students = cursor.fetchall()
        except:
            pass
        
        if students:
            student_options = [s[1] for s in students]
            student_var = StringVar()
            student_dropdown = CTkOptionMenu(
                student_frame,
                variable=student_var,
                values=student_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            student_dropdown.pack(fill="x", pady=(5, 0))
            student_dropdown.set(student_options[0])
        else:
            CTkLabel(student_frame, text="No students available. Create students first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Subject selection
        subject_frame = CTkFrame(fields_frame, fg_color="transparent")
        subject_frame.pack(fill="x", pady=10)
        CTkLabel(subject_frame, text="Subject:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        subjects = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, code, name FROM subjects")
                subjects = cursor.fetchall()
        except:
            pass
        
        if subjects:
            subject_options = [f"{s[1]} - {s[2]}" for s in subjects]
            subject_var = StringVar()
            subject_dropdown = CTkOptionMenu(
                subject_frame,
                variable=subject_var,
                values=subject_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            subject_dropdown.pack(fill="x", pady=(5, 0))
            subject_dropdown.set(subject_options[0])
        else:
            CTkLabel(subject_frame, text="No subjects available. Create subjects first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Enrollment",
            command=lambda: add_enrollment(
                student_var.get() if 'student_var' in locals() else None,
                subject_var.get() if 'subject_var' in locals() else None
            ),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
        font=("Arial", 14, "bold"), 
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def add_enrollment(student_name, subject_info):
        if not all([student_name, subject_info]):
            messagebox.showerror("Error", "Please select student and subject")
            return
        
        try:
            import db
            with db.connect() as conn:
                # Get student and their assigned block
                cursor = conn.execute("SELECT id, block_id FROM students WHERE name = ?", (student_name,))
                student_row = cursor.fetchone()
                
                if not student_row:
                    messagebox.showerror("Error", "Selected student not found")
                    return
                student_id, student_block_id = student_row[0], student_row[1]
                if student_block_id is None:
                    messagebox.showerror("Error", "Selected student has no assigned block. Assign a block first in the Students tab.")
                    return
                
                # Get subject ID
                subject_code = subject_info.split(" - ")[0]
                cursor = conn.execute("SELECT id FROM subjects WHERE code = ?", (subject_code,))
                subject_id = cursor.fetchone()
                
                if not subject_id:
                    messagebox.showerror("Error", "Selected subject not found")
                    return
                
                # Check if enrollment already exists
                cursor = conn.execute(
                    "SELECT id FROM enrollments WHERE student_id = ? AND subject_id = ? AND block_id = ?",
                    (student_id, subject_id[0], student_block_id)
                )
                if cursor.fetchone():
                    messagebox.showerror("Error", "Student is already enrolled in this subject for this block")
                    return
                
                # Insert enrollment
                conn.execute(
                    "INSERT INTO enrollments (student_id, subject_id, block_id) VALUES (?, ?, ?)",
                    (student_id, subject_id[0], student_block_id)
                )
                conn.commit()
                show_success_message(f"Enrollment for {student_name} added successfully!")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add enrollment: {str(e)}")
    
    # Show default tab
    show_tab("Students")