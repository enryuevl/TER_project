from customtkinter import *
from tkinter import ttk, messagebox, filedialog
import db
import pandas as pd
import datetime
from db import backup_all
import shutil

class AccountsDatabasePage:
    def __init__(self, master):
        self.master = master
        self.tab_buttons = {}
        self.current_tab = None
        self.sidepanel = None
        self.tree = None

        self._build_ui()

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.container = CTkFrame(self.master, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        CTkLabel(self.container, text="Faculty, Departments & Blocks Manager",
                 font=("Arial", 24, "bold"), text_color="#691612").pack(pady=(0, 20))

        # Tabs
        self.tab_frame = CTkFrame(self.container, fg_color="transparent")
        self.tab_frame.pack(fill="x", pady=(0, 10))

        self.content_frame = CTkFrame(self.container, fg_color="#FFFFFF", corner_radius=10)
        self.content_frame.pack(fill="both", expand=True)

        self.controls_frame = CTkFrame(self.container, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=(10, 0))

        # Tab buttons
        for i, entity in enumerate(["Faculty", "Departments", "Blocks", "Teaching Assignments"]):
            btn = CTkButton(
                self.tab_frame, text=entity,
                command=lambda e=entity: self.show_tab(e),
                fg_color="#AC5353" if i == 0 else "#F1F3F5",
                text_color="#FFFFFF" if i == 0 else "#333333",
                hover_color="#BF3131" if i == 0 else "#E9ECEF",
                width=160, height=35, corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons[entity] = btn

        self.show_tab("Faculty")

    # ---------------- Tabs ---------------- #
    def show_tab(self, name):
        self.current_tab = name
        # highlight selected tab
        for tab, btn in self.tab_buttons.items():
            btn.configure(
                fg_color="#AC5353" if tab == name else "#F1F3F5",
                text_color="#FFFFFF" if tab == name else "#333333"
            )

        for w in self.content_frame.winfo_children():
            w.destroy()

        # Header
        header_frame = CTkFrame(self.content_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)

        CTkLabel(header_frame, text=f"{name} Table",
                 font=("Arial", 20, "bold"), text_color="#691612").pack(side="left")

        search_entry = CTkEntry(header_frame, placeholder_text="Search...",
                                fg_color="#F8F9FA", width=200, height=32)
        search_entry.pack(side="right", padx=(0, 10))

        backup_btn = CTkButton(
        header_frame, text="Backup Database",
        command=self.backup_database,
        fg_color="#691612", hover_color="#AC5353",
        text_color="#FFFFFF", width=160, height=32
    )
        backup_btn.pack(side="right", padx=10)

        restore_btn = CTkButton(
        header_frame, text="Load Backup",
        command=self.load_backup,
        fg_color="#BF3131",      # Crimson
        hover_color="#8B1D18",   # Dark Red hover
        text_color="#FFFFFF",
        width=160, height=32
    )
        restore_btn.pack(side="right", padx=10)


        # Table
        table_container = CTkFrame(self.content_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        table_loaders = {
            "Faculty": self.show_faculty_table,
            "Departments": self.show_departments_table,
            "Blocks": self.show_blocks_table,
            "Teaching Assignments": self.show_teaching_assignments_table
        }

        table_loaders[name](table_container, search_entry)

        # Controls
        for w in self.controls_frame.winfo_children():
            w.destroy()
        for label, color in [
            ("Add", "#691612"),    # Dark Crimson
            ("Edit", "#BF3131"),   # Crimson
            ("Delete", "#B22222")  # Firebrick
        ]:
            CTkButton(
                self.controls_frame,
                text=f"{label} {name[:0]}",
                fg_color=color,
                hover_color="#8B1D18",   # Dark Red hover
                text_color="#FFFFFF",
                command=(lambda l=label: self._handle_control(name, l.lower()))
            ).pack(side="left", padx=5)

    def _handle_control(self, entity, action):
        if action in ["add", "edit"]:
            self.open_sidepanel(entity, mode=action)
        elif action == "delete":
            self.delete_selected()

    # ---------------- Side Panel ---------------- #
    def open_sidepanel(self, entity, mode="add"):
        if self.sidepanel and self.sidepanel.winfo_exists():
            self.sidepanel.destroy()
        self.sidepanel = CTkToplevel(self.master)
        self.sidepanel.title(f"{mode.title()} {entity[:-1]}")
        self.sidepanel.geometry("400x500")
        self.sidepanel.grab_set()

        builders = {
            "Faculty": self.build_faculty_form,
            "Departments": self.build_department_form,
            "Blocks": self.build_block_form,
            "Teaching Assignments": self.build_teaching_assignment_form
        }
        builders[entity](self.sidepanel, mode)

    # ---------------- Tables ---------------- #
    def _setup_treeview(self, container, columns, headings, col_widths):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30)
        style.configure("Treeview.Heading", background="#F8F9FA",
                        foreground="#691612", font=("Arial", 12, "bold"))

        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(container, columns=columns,
                                 show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.configure(command=self.tree.yview)
        self.tree.pack(fill="both", expand=True)

        for col, heading, width in zip(columns, headings, col_widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center" if col == "ID" else "w")

    def show_faculty_table(self, container, search_entry):
        self._setup_treeview(container,
            columns=("ID", "Full Name", "Department"),
            headings=("ID", "Full Name", "Department"),
            col_widths=(60, 280, 200))

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            query = """
                SELECT f.id, f.full_name, COALESCE(d.name, 'No Department')
                FROM faculty f LEFT JOIN departments d ON f.department_id = d.id
            """
            params = ()
            if term:
                query += " WHERE f.full_name LIKE ? OR d.name LIKE ?"
                params = (f"%{term}%", f"%{term}%")
            query += " ORDER BY f.full_name"
            with db.connect() as conn:
                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", values=row)

        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()

    def show_departments_table(self, container, search_entry):
        self._setup_treeview(container,
            columns=("ID", "Name", "Faculty Count"),
            headings=("ID", "Department Name", "Faculty Members"),
            col_widths=(80, 300, 150))

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            query = """
                SELECT d.id, d.name, COUNT(f.id)
                FROM departments d LEFT JOIN faculty f ON d.id = f.department_id
            """
            params = ()
            if term:
                query += " WHERE d.name LIKE ?"
                params = (f"%{term}%",)
            query += " GROUP BY d.id, d.name ORDER BY d.name"
            with db.connect() as conn:
                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", values=row)

        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()

    def show_blocks_table(self, container, search_entry):
        self._setup_treeview(container,
            columns=("ID", "Year Level", "Section", "Students"),
            headings=("ID", "Year Level", "Section", "Students"),
            col_widths=(60, 100, 100, 120))

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            query = "SELECT id, year_level, section, num_students FROM blocks"
            params = ()
            if term:
                query += " WHERE section LIKE ?"
                params = (f"%{term}%",)
            query += " ORDER BY year_level, section"
            with db.connect() as conn:
                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", values=row)

        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()

    def show_teaching_assignments_table(self, container, search_entry):
        self._setup_treeview(container,
            columns=("ID", "Subject Code", "Subject Name", "Block", "Professor", "Students"),
            headings=("ID", "Code", "Subject Name", "Block", "Professor", "Students"),
            col_widths=(50, 100, 250, 150, 200, 100))

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            query = """
                SELECT 
                    ta.id,
                    s.code AS subject_code,
                    s.name AS subject_name,
                    b.year_level || b.section || ' (' || b.academic_year || ' ' || b.semester || ')' AS block_label,
                    COALESCE(f.full_name, 'TBA') AS professor,
                    b.num_students AS students
                FROM teaching_assignments ta
                JOIN subjects s ON ta.subject_id = s.id
                JOIN blocks b ON ta.block_id = b.id
                LEFT JOIN faculty f ON ta.faculty_id = f.id
            """
            params = ()
            if term:
                query += """ 
                    WHERE s.code LIKE ? OR s.name LIKE ? 
                    OR f.full_name LIKE ? OR b.section LIKE ?
                """
                params = (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%")
            query += " ORDER BY s.code, b.year_level, b.section"

            with db.connect() as conn:
                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", values=row)

        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()


    # ---------------- Delete ---------------- #
    def delete_selected(self):
        if not self.tree:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a record to delete.")
            return
        record_id = self.tree.item(selected[0], "values")[0]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete record ID {record_id}?")
        if not confirm:
            return

        table_map = {
            "Faculty": "faculty",
            "Departments": "departments",
            "Blocks": "blocks"
        }
        with db.connect() as conn:
            conn.execute(f"DELETE FROM {table_map[self.current_tab]} WHERE id=?", (record_id,))
            conn.commit()
        self.show_tab(self.current_tab)

    # ---------------- Export ---------------- #
    def export_table_data(self, table_name):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")],
            initialfile=f"{table_name.lower()}_export"
        )
        if not file_path:
            return

        queries = {
            "Faculty": """
                SELECT f.id, f.first_name, f.middle_name, f.last_name, f.suffix, f.full_name,
                       COALESCE(d.name, 'No Department') as dept_name
                FROM faculty f LEFT JOIN departments d ON f.department_id = d.id
                ORDER BY f.full_name
            """,
            "Departments": """
                SELECT d.id, d.name, COUNT(f.id) as faculty_count
                FROM departments d LEFT JOIN faculty f ON d.id = f.department_id
                GROUP BY d.id, d.name ORDER BY d.name
            """,
            "Blocks": """
                SELECT id, year_level, section, num_students
                FROM blocks ORDER BY year_level, section
            """
        }

        with db.connect() as conn:
            df = pd.read_sql_query(queries[table_name], conn)

        if file_path.endswith('.csv'):
            df.to_csv(file_path, index=False)
        else:
            df.to_excel(file_path, index=False)

        messagebox.showinfo("Export Successful", f"{table_name} exported to {file_path}")

    # ---------------- Forms ---------------- #
    def build_faculty_form(self, parent, mode):
        CTkLabel(parent, text="Faculty Form", font=("Arial", 18, "bold"),
                    text_color="#691612").pack(pady=10)

        first = CTkEntry(parent, placeholder_text="First Name"); first.pack(fill="x", padx=20, pady=5)
        middle = CTkEntry(parent, placeholder_text="Middle Name"); middle.pack(fill="x", padx=20, pady=5)
        last = CTkEntry(parent, placeholder_text="Last Name"); last.pack(fill="x", padx=20, pady=5)
        suffix = CTkEntry(parent, placeholder_text="Suffix"); suffix.pack(fill="x", padx=20, pady=5)

        dept_var, dept_options = StringVar(), []
        with db.connect() as conn:
            rows = conn.execute("SELECT name FROM departments").fetchall()
            dept_options = [r[0] for r in rows]
        if dept_options:
            dept_menu = CTkOptionMenu(
                parent,
                variable=dept_var,
                values=dept_options,
                fg_color="#BF3131",          # Crimson main background
                button_color="#691612",      # Dark Crimson button
                button_hover_color="#8B1D18",# Dark Red hover
                text_color="#FFFFFF"         # White text
   
            )
            dept_menu.pack(fill="x", padx=20, pady=10)
            dept_var.set(dept_options[0])
        # Pre-fill for edit
        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a faculty to edit.")
                self.sidepanel.destroy()
                return
            record = self.tree.item(selected[0], "values")
            record_id, fullname, dept = record
            with db.connect() as conn:
                data = conn.execute("SELECT first_name, middle_name, last_name, suffix FROM faculty WHERE id=?", (record_id,)).fetchone()
            if data:
                first.insert(0, data[0] or "")
                middle.insert(0, data[1] or "")
                last.insert(0, data[2] or "")
                suffix.insert(0, data[3] or "")
                dept_var.set(dept)

        def submit():
            try:
                with db.connect() as conn:
                    dept_id = conn.execute("SELECT id FROM departments WHERE name=?", (dept_var.get(),)).fetchone()[0]
                    if mode == "add":
                        conn.execute("""
                            INSERT INTO faculty (first_name, middle_name, last_name, suffix, department_id)
                            VALUES (?,?,?,?,?)""",
                            (first.get().strip(), middle.get().strip() or None,
                                last.get().strip(), suffix.get().strip() or None, dept_id))
                    else:
                        conn.execute("""
                            UPDATE faculty SET first_name=?, middle_name=?, last_name=?, suffix=?, department_id=?
                            WHERE id=?""",
                            (first.get().strip(), middle.get().strip() or None,
                                last.get().strip(), suffix.get().strip() or None, dept_id, record_id))
                    conn.commit()
                self.sidepanel.destroy()
                self.show_tab("Faculty")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612",
                    command=submit).pack(pady=20)

    def build_department_form(self, parent, mode):
        CTkLabel(parent, text="Department Form", font=("Arial", 18, "bold"),
                    text_color="#691612").pack(pady=10)

        name_entry = CTkEntry(parent, placeholder_text="Department Name")
        name_entry.pack(fill="x", padx=20, pady=10)

        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a department to edit.")
                self.sidepanel.destroy()
                return
            record = self.tree.item(selected[0], "values")
            record_id, name, count = record
            name_entry.insert(0, name)

        def submit():
            try:
                with db.connect() as conn:
                    if mode == "add":
                        conn.execute("INSERT INTO departments (name) VALUES (?)", (name_entry.get().strip(),))
                    else:
                        conn.execute("UPDATE departments SET name=? WHERE id=?",
                                        (name_entry.get().strip(), record_id))
                    conn.commit()
                self.sidepanel.destroy()
                self.show_tab("Departments")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612",
                    command=submit).pack(pady=20)

    def build_block_form(self, parent, mode):
        CTkLabel(parent, text="Block Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        # Year Level dropdown (1–4)
        year_var = StringVar()
        year_menu = CTkOptionMenu(parent, variable=year_var, values=["1", "2", "3", "4"])
        year_menu.pack(fill="x", padx=20, pady=5)
        year_var.set("1")  # default

        # Section dropdown (A–D)
        section_var = StringVar()
        section_menu = CTkOptionMenu(parent, variable=section_var, values=["A", "B", "C", "D"])
        section_menu.pack(fill="x", padx=20, pady=5)
        section_var.set("A")  # default

        # School Year entry (e.g. "2024-2025")
        sy_entry = CTkEntry(parent, placeholder_text="Academic Year (e.g. 2024-2025)")
        sy_entry.pack(fill="x", padx=20, pady=5)

        # Semester is determined automatically
        sem_var = StringVar()
        month = datetime.datetime.now().month
        if 8 <= month <= 12:
            sem_var.set("1st")
        elif 1 <= month <= 6:
            sem_var.set("2nd")
        else:
            sem_var.set("Summer")  # Optional rule for July

        sem_label = CTkLabel(parent, text=f"Semester: {sem_var.get()}",
                            font=("Arial", 14), text_color="#333333")
        sem_label.pack(pady=5)

        # Number of students entry
        num_students_entry = CTkEntry(parent, placeholder_text="Number of Students")
        num_students_entry.pack(fill="x", padx=20, pady=5)

        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a block to edit.")
                self.sidepanel.destroy()
                return
            record = self.tree.item(selected[0], "values")
            record_id, year, section, num_students = record[:4]
            year_var.set(str(year))
            section_var.set(section)
            num_students_entry.insert(0, num_students)
            # if you add school year + sem to tree columns, preload them here too

        def submit():
            try:
                # Validate num_students
                try:
                    num_students = int(num_students_entry.get().strip())
                except ValueError:
                    messagebox.showerror("Invalid Input", "Number of students must be an integer.")
                    return

                academic_year = sy_entry.get().strip()
                if not academic_year:
                    messagebox.showerror("Invalid Input", "Academic year cannot be empty.")
                    return

                with db.connect() as conn:
                    if mode == "add":
                        # Insert the block
                        cursor = conn.execute("""
                            INSERT INTO blocks (year_level, section, academic_year, semester, num_students)
                            VALUES (?,?,?,?,?)
                        """, (int(year_var.get()), section_var.get(), academic_year, sem_var.get(), num_students))
                        block_id = cursor.lastrowid

                        # Auto-create teaching assignments (faculty = NULL / TBA)
                        subjects = conn.execute("""
                            SELECT id FROM subjects 
                            WHERE year_level=? AND semester=?
                        """, (int(year_var.get()), sem_var.get())).fetchall()

                        for subj in subjects:
                            conn.execute("""
                                INSERT INTO teaching_assignments (faculty_id, subject_id, block_id)
                                VALUES (NULL, ?, ?)
                            """, (subj[0], block_id))

                    else:
                        # Update existing block
                        conn.execute("""
                            UPDATE blocks 
                            SET year_level=?, section=?, academic_year=?, semester=?, num_students=? 
                            WHERE id=?
                        """, (int(year_var.get()), section_var.get(), academic_year, sem_var.get(), num_students, record_id))

                    conn.commit()

                self.sidepanel.destroy()
                self.show_tab("Blocks")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)

    def build_teaching_assignment_form(self, parent, mode):
        CTkLabel(parent, text="Teaching Assignment Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        # Faculty dropdown (from faculty table)
        faculty_var = StringVar()
        faculty_options = ["TBA"]
        faculty_map = {"TBA": None}
        with db.connect() as conn:
            rows = conn.execute("SELECT id, full_name FROM faculty ORDER BY full_name").fetchall()
            for fid, fname in rows:
                faculty_options.append(fname)
                faculty_map[fname] = fid

        faculty_menu = CTkOptionMenu(parent, variable=faculty_var, values=faculty_options)
        faculty_menu.pack(fill="x", padx=20, pady=5)
        faculty_var.set("TBA")

        # Subject dropdown (will be disabled in edit mode)
        subject_var = StringVar()
        subject_options = []
        subject_map = {}
        with db.connect() as conn:
            rows = conn.execute("SELECT id, code || ' - ' || name FROM subjects ORDER BY code").fetchall()
            for sid, label in rows:
                subject_options.append(label)
                subject_map[label] = sid
        subject_menu = CTkOptionMenu(parent, variable=subject_var, values=subject_options)
        subject_menu.pack(fill="x", padx=20, pady=5)
        if subject_options:
            subject_var.set(subject_options[0])

        # Block dropdown (will be disabled in edit mode)
        block_var = StringVar()
        block_options = []
        block_map = {}
        with db.connect() as conn:
            rows = conn.execute("""
                SELECT id, year_level || section || ' (' || academic_year || ' ' || semester || ')' 
                FROM blocks ORDER BY year_level, section
            """).fetchall()
            for bid, label in rows:
                block_options.append(label)
                block_map[label] = bid
        block_menu = CTkOptionMenu(parent, variable=block_var, values=block_options)
        block_menu.pack(fill="x", padx=20, pady=5)
        if block_options:
            block_var.set(block_options[0])

        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a teaching assignment to edit.")
                self.sidepanel.destroy()
                return

            record = self.tree.item(selected[0], "values")
            record_id = record[0]  # ✅ always reference the assignment ID

            with db.connect() as conn:
                row = conn.execute("""
                    SELECT ta.faculty_id, ta.subject_id, ta.block_id, f.full_name
                    FROM teaching_assignments ta
                    LEFT JOIN faculty f ON ta.faculty_id = f.id
                    WHERE ta.id = ?
                """, (record_id,)).fetchone()

                if row:
                    fac_id, subj_id, blk_id, fac_name = row

                    # Pre-fill professor
                    faculty_var.set(fac_name if fac_name else "TBA")

                    # Pre-fill subject (but lock dropdown)
                    for k, v in subject_map.items():
                        if v == subj_id:
                            subject_var.set(k)
                            break
                    subject_menu.configure(state="disabled")

                    # Pre-fill block (but lock dropdown)
                    for k, v in block_map.items():
                        if v == blk_id:
                            block_var.set(k)
                            break
                    block_menu.configure(state="disabled")

        def submit():
            try:
                faculty_id = faculty_map.get(faculty_var.get())  # can be None (TBA)

                with db.connect() as conn:
                    if mode == "add":
                        # Add new assignment
                        conn.execute("""
                            INSERT INTO teaching_assignments (faculty_id, subject_id, block_id)
                            VALUES (?, ?, ?)
                        """, (
                            faculty_id,
                            subject_map[subject_var.get()],
                            block_map[block_var.get()]
                        ))
                    else:
                        # ✅ Update only the professor for this assignment ID
                        conn.execute("""
                            UPDATE teaching_assignments 
                            SET faculty_id=? 
                            WHERE id=?
                        """, (faculty_id, record_id))
                    conn.commit()

                self.sidepanel.destroy()
                self.show_tab("Teaching Assignments")  # refresh table

            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)


    #backup function
    def backup_database(self):
        try:
            backup_dir = db.backup_all()  # calls your db.py backup_all()
            messagebox.showinfo("Backup Successful", f"Backup saved in:\n{backup_dir}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def load_backup(self):
        try:
            file_path = filedialog.askopenfilename(
                title="Select Backup File",
                filetypes=[("Backup Files", "*.sqlite *.pkl"), ("All Files", "*.*")]
            )
            if not file_path:
                return  # cancelled

            documents_folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork")

            if file_path.endswith(".sqlite"):
                target = os.path.join(documents_folder, "ter_db2.sqlite")
            elif file_path.endswith(".pkl"):
                target = os.path.join(documents_folder, "results.pkl")
            else:
                messagebox.showerror("Invalid File", "Please select a .sqlite or .pkl backup file.")
                return

            shutil.copy2(file_path, target)
            messagebox.showinfo("Restore Successful", f"Backup restored from:\n{file_path}")

            # 🔄 refresh UI after restore
            self.show_tab(self.current_tab)

        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))


