from customtkinter import *
from tkinter import ttk, messagebox, filedialog
import db
import pandas as pd
import datetime
from db import backup_all
import shutil
import os

class AccountsDatabasePage:
    def __init__(self, master, ctx):
        self.master = master
        self.tab_buttons = {}
        self.current_tab = None
        self.sidepanel = None
        self.tree = None
        self.ctx = ctx

        self._build_ui()

    # --- Role/Dept helpers ---
    def _is_operator(self) -> bool:
        # Treat both operator and dean as department-scoped users
        return (self.ctx.role or "").lower() in ("operator", "dean") \
            and self.ctx.department_id is not None

    def _dept_param(self):
        return (self.ctx.department_id,)  # convenience tuple for SQL params

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
        for i, entity in enumerate(["Faculty", "Departments","Programs","Subjects", "Blocks", "Teaching Assignments"]):
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
        # highlight selected tab with red palette alignment
        for tab, btn in self.tab_buttons.items():
            if tab == name:
                btn.configure(
                    fg_color="#691612",    # Dark Crimson active
                    text_color="#FFFFFF",  # White text active
                    hover_color="#BF3131"  # Crimson hover active
                )
            else:
                btn.configure(
                    fg_color="#AC5353",    # Muted Red inactive
                    text_color="#333333",  # Dark text inactive
                    hover_color="#8B1D18"  # Dark Red hover inactive
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
            "Programs": self.show_programs_table,
            "Subjects": self.show_subjects_table,
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
            "Programs": self.build_program_form,
            "Subjects": self.build_subject_form,
            "Blocks": self.build_block_form,
            "Teaching Assignments": self.build_teaching_assignment_form
        }
        builders[entity](self.sidepanel, mode)

 # ---------------- Tables ---------------- #
    def _setup_treeview(self, container, columns, headings, col_widths):
        # Create a frame to hold the tree and scrollbars
        frame = CTkFrame(container, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        # Scrollbars (horizontal + vertical)
        x_scroll = CTkScrollbar(frame, orientation="horizontal")
        x_scroll.pack(side="bottom", fill="x")
        y_scroll = CTkScrollbar(frame, orientation="vertical")
        y_scroll.pack(side="right", fill="y")

        # Treeview widget
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set,
            height=20
        )
        self.tree.pack(fill="both", expand=True)

        # Connect scrollbars
        x_scroll.configure(command=self.tree.xview)
        y_scroll.configure(command=self.tree.yview)

        # ---------- Styling ----------
        style = ttk.Style()
        style.theme_use("default")

        # Base row style
        style.configure(
            "Treeview",
            font=("Arial", 11),
            rowheight=30,
            background="#F3F4F6",   # soft gray background
            foreground="#1F2937"    # neutral dark text
        )

        # Heading style (Crimson)
        style.configure(
            "Treeview.Heading",
            font=("Arial", 12, "bold"),
            foreground="#FFFFFF",
            background="#BF3131"   # Crimson header
        )

        # Hover + selection colors
        style.map(
            "Treeview",
            background=[("selected", "#AC5353")],  # Muted Red
            foreground=[("selected", "#FFFFFF")]
        )
        style.map(
            "Treeview.Heading",
            background=[("hover", "#AC5353")],
            foreground=[("hover", "#FFFFFF")]
        )

        # Define row tags
        self.tree.tag_configure("oddrow", background="#F3F4F6", foreground="#1F2937")
        self.tree.tag_configure("evenrow", background="#EBE8DB", foreground="#1F2937")
        self.tree.tag_configure(
            "section",
            background="#BF3131",  # Crimson
            foreground="#FFFFFF",
            font=("Arial", 12, "bold")
        )

        # Set up headings & column widths
        for col, heading, width in zip(columns, headings, col_widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w")


    def show_faculty_table(self, container, search_entry):
        self._setup_treeview(
            container,
            columns=("Full Name", "Department", "Rank"),
            headings=("Full Name", "Department", "Rank"),
            col_widths=(280, 220, 180),
        )

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            with db.connect() as conn:
                params = []
                where = []
                base = """
                    SELECT f.id,
                        f.full_name,
                        COALESCE(d.name, 'No Department') AS dept_name,
                        COALESCE(f.role, '—') AS rank_label
                    FROM faculty f
                    LEFT JOIN departments d ON d.id = f.department_id
                """

                # operator scope
                if self._is_operator():
                    where.append("f.department_id = ?")
                    params += [self.ctx.department_id]

                # search
                if term and term.strip():
                    where.append("(f.full_name LIKE ? OR COALESCE(d.name,'') LIKE ?)")
                    like = f"%{term}%"
                    params += [like, like]

                if where:
                    base += " WHERE " + " AND ".join(where)

                base += " ORDER BY f.full_name"

                rows = conn.execute(base, tuple(params)).fetchall()
                for fid, fullname, dept, rank_label in rows:
                    self.tree.insert("", "end", iid=str(fid), values=(fullname, dept, rank_label))


        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()


    def show_departments_table(self, container, search_entry):
        self._setup_treeview(container,
            columns=( "Name", "Faculty Count"),
            headings=( "Department Name", "Faculty Members"),
            col_widths=( 300, 150))

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            query = """
                SELECT d.id, d.name, COUNT(f.id)
                FROM departments d LEFT JOIN faculty f ON d.id = f.department_id
            """
            params = ()
            where = []

            if self._is_operator():
                where.append("d.id = ?")
                params += self._dept_param()

            if term:
                where.append("d.name = ?")
                params += (term.strip(),)

            if where:
                query += " WHERE " + " AND ".join(where)

            query += " GROUP BY d.id, d.name ORDER BY d.name"

            with db.connect() as conn:
                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", iid=str(row[0]), values=row[1:])


        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()


    def show_blocks_table(self, container, search_entry):
        self._setup_treeview(
            container,
            columns=("Program", "Year Level", "Section", "Academic Year", "Semester"),
            headings=( "Program", "Year Level", "Section", "AY", "Sem"),
            col_widths=( 120, 100, 100, 140, 100)
        )

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            with db.connect() as conn:
                prog_id = None
                ay, sem = self._parse_term_filters(term)
                if term:
                    prog_id = self._resolve_program_id_by_code(conn, term)

                base = """
                    SELECT b.id, p.code AS program, b.year_level, b.section, b.academic_year, b.semester
                    FROM blocks b
                    JOIN programs p ON p.id = b.program_id
                """

                where, params = [], []

                if self._is_operator():
                    where.append("p.department_id = ?")
                    params += [self.ctx.department_id]

                if prog_id is not None:
                    where.append("b.program_id = ?"); params.append(prog_id)
                if ay:
                    where.append("b.academic_year = ?"); params.append(ay)
                if sem:
                    where.append("b.semester = ?"); params.append(sem)

                if not where and term and term.strip():
                    where.append("(p.code LIKE ? OR b.section LIKE ? OR b.academic_year LIKE ?)")
                    like = f"%{term}%"
                    params += [like, like, like]

                if where:
                    query = base + " WHERE " + " AND ".join(where) + " ORDER BY p.code, b.year_level, b.section"
                else:
                    query = base + " ORDER BY p.code, b.year_level, b.section"

                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", iid=str(row[0]), values=row[1:])


        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()


    def show_teaching_assignments_table(self, container, search_entry):
        self._setup_treeview(
            container,
            columns=( "Code", "Subject Title", "Block", "Professor", "AY", "Sem", "Expected"),
            headings=( "Code", "Subject Title", "Block", "Professor", "AY", "Sem", "Expected"),
            col_widths=( 100, 260, 180, 200, 120, 80, 100)
        )

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            with db.connect() as conn:
                subj_id = None
                ay, sem = self._parse_term_filters(term)
                if term:
                    subj_id = self._resolve_subject_id_by_code(conn, term)

                base = """
                    SELECT 
                        ta.id,
                        s.code,
                        s.title,
                        COALESCE(
                            b.year_level || b.section || ' (' || b.academic_year || ' ' || b.semester || ')',
                            'Merged'
                        ) AS block_label,
                        COALESCE(f.full_name, 'TBA') AS professor,
                        ta.academic_year,
                        ta.semester,
                        ta.expected_students
                    FROM teaching_assignments ta
                    JOIN subjects s     ON s.id = ta.subject_id
                    LEFT JOIN blocks b  ON b.id = ta.block_id
                    LEFT JOIN faculty f ON f.id = ta.teacher_id
                """

                where, params = [], []

                if self._is_operator():
                    where.append("f.department_id = ?")
                    params += [self.ctx.department_id]

                if subj_id is not None:
                    where.append("ta.subject_id = ?"); params.append(subj_id)
                if ay:
                    where.append("ta.academic_year = ?"); params.append(ay)
                if sem:
                    where.append("ta.semester = ?"); params.append(sem)

                if term and term.strip():
                    like = f"%{term}%"
                    where.append("(s.code LIKE ? OR s.title LIKE ? OR COALESCE(f.full_name,'') LIKE ? OR COALESCE(b.section,'') LIKE ? OR ta.academic_year LIKE ?)")
                    params += [like, like, like, like, like]

                if where:
                    query = base + " WHERE " + " AND ".join(where) + " ORDER BY s.code, ta.academic_year, ta.semester, block_label"
                else:
                    query = base + " ORDER BY s.code, ta.academic_year, ta.semester, block_label"

                for row in conn.execute(query, params).fetchall():
                    self.tree.insert("", "end", iid=str(row[0]), values=row[1:])



        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()

    def show_programs_table(self, container, search_entry):
        self._setup_treeview(
            container,
            columns=( "Code", "Name", "Department"),
            headings=( "Code", "Program Name", "Department"),
            col_widths=( 120, 260, 220)
        )

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            base = """
                SELECT p.id, p.code, p.name, d.name AS dept
                FROM programs p
                JOIN departments d ON d.id = p.department_id
            """
            where, params = [], []

            if self._is_operator():
                where.append("p.department_id = ?")
                params += [self.ctx.department_id]

            if term and term.strip():
                like = f"%{term}%"
                where.append("(p.code LIKE ? OR p.name LIKE ? OR d.name LIKE ?)")
                params += [like, like, like]

            if where:
                base += " WHERE " + " AND ".join(where)

            base += " ORDER BY p.code"
            with db.connect() as conn:
                for row in conn.execute(base, params).fetchall():
                    self.tree.insert("", "end", iid=str(row[0]), values=row[1:])


        search_entry.bind("<KeyRelease>", lambda e: load_data(search_entry.get()))
        load_data()

    def show_subjects_table(self, container, search_entry):
        self._setup_treeview(
            container,
            columns=( "Code", "Title", "Units", "Year", "Sem", "Program", "Department"),
            headings=( "Code", "Title", "Units", "Year", "Sem", "Program", "Dept"),
            col_widths=( 110, 280, 70, 70, 90, 120, 160)
        )

        def load_data(term=None):
            self.tree.delete(*self.tree.get_children())
            base = """
                SELECT s.id, s.code, s.title, COALESCE(s.units,3), s.year_level, s.semester,
                    p.code AS program_code,
                    COALESCE(d.name, '—') AS dept_name
                FROM subjects s
                JOIN programs p         ON p.id = s.program_id
                LEFT JOIN departments d ON d.id = s.department_id
            """
            where, params = [], []

            if self._is_operator():
                where.append("s.department_id = ?")
                params += [self.ctx.department_id]

            if term and term.strip():
                like = f"%{term}%"
                where.append("""(
                    s.code LIKE ? OR s.title LIKE ? OR p.code LIKE ? OR
                    CAST(s.year_level AS TEXT) LIKE ? OR s.semester LIKE ? OR
                    COALESCE(d.name,'') LIKE ?
                )""")
                params += [like, like, like, like, like, like]

            if where:
                base += " WHERE " + " AND ".join(where)

            base += " ORDER BY p.code, s.code"
            with db.connect() as conn:
                for row in conn.execute(base, params).fetchall():
                    self.tree.insert("", "end", iid=str(row[0]), values=row[1:])


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

        record_id = int(selected[0])  # iid = id
        if not messagebox.askyesno("Confirm Delete", f"Delete record ID {record_id}?"):
            return

        tab = self.current_tab

        try:
            with db.connect() as conn:
                if tab == "Faculty":
                    if self._is_operator():
                        conn.execute("DELETE FROM faculty WHERE id=? AND department_id=?",
                                    (record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM faculty WHERE id=?", (record_id,))

                elif tab == "Departments":
                    if self._is_operator():
                        # only own dept
                        conn.execute("DELETE FROM departments WHERE id=? AND id=?",
                                    (record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM departments WHERE id=?", (record_id,))

                elif tab == "Programs":
                    if self._is_operator():
                        conn.execute("DELETE FROM programs WHERE id=? AND department_id=?",
                                    (record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM programs WHERE id=?", (record_id,))

                elif tab == "Subjects":
                    if self._is_operator():
                        conn.execute("DELETE FROM subjects WHERE id=? AND department_id=?",
                                    (record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM subjects WHERE id=?", (record_id,))

                elif tab == "Blocks":
                    if self._is_operator():
                        conn.execute("""
                            DELETE FROM blocks
                            WHERE id = ?
                            AND EXISTS (
                                SELECT 1 FROM programs p
                                WHERE p.id = blocks.program_id
                                    AND p.department_id = ?
                            )
                        """, (record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM blocks WHERE id=?", (record_id,))

                elif tab == "Teaching Assignments":
                    if self._is_operator():
                        conn.execute("""
                            DELETE FROM teaching_assignments
                            WHERE id = ?
                            AND EXISTS (
                                SELECT 1
                                FROM teaching_assignments ta
                                JOIN faculty f ON f.id = ta.teacher_id
                                WHERE ta.id = ? AND f.department_id = ?
                            )
                        """, (record_id, record_id, self.ctx.department_id))
                    else:
                        conn.execute("DELETE FROM teaching_assignments WHERE id=?", (record_id,))
                else:
                    messagebox.showerror("Unsupported", f"Delete not configured for {tab}")
                    return

                if conn.total_changes == 0 and self._is_operator():
                    messagebox.showwarning("Not allowed", "You can only delete records in your department.")
                    return

                conn.commit()

            self.show_tab(self.current_tab)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))



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
                SELECT b.id, p.code AS program, b.year_level, b.section, b.academic_year, b.semester
                FROM blocks b JOIN programs p ON p.id = b.program_id
                ORDER BY p.code, b.year_level, b.section
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

        # --- Basic Info ---
        first = CTkEntry(parent, placeholder_text="First Name"); first.pack(fill="x", padx=20, pady=5)
        middle = CTkEntry(parent, placeholder_text="Middle Name"); middle.pack(fill="x", padx=20, pady=5)
        last = CTkEntry(parent, placeholder_text="Last Name"); last.pack(fill="x", padx=20, pady=5)
        suffix = CTkEntry(parent, placeholder_text="Suffix"); suffix.pack(fill="x", padx=20, pady=5)

        # --- Department Dropdown ---
        dept_var, dept_options = StringVar(), []
        with db.connect() as conn:
            rows = conn.execute("SELECT name FROM departments").fetchall()
            dept_options = [r[0] for r in rows]
        if dept_options:
            dept_menu = CTkOptionMenu(
                parent,
                variable=dept_var,
                values=dept_options,
                fg_color="#BF3131",
                button_color="#691612",
                button_hover_color="#8B1D18",
                text_color="#FFFFFF"
            )
            dept_menu.pack(fill="x", padx=20, pady=10)
            dept_var.set(dept_options[0])

        # 🆕 ---- Rank & Sub-rank Dropdowns ----
        RANKS = {
            "Instructor": ["I", "II", "III"],
            "Assistant Professor": ["I", "II", "III", "IV"],
            "Associate Professor": ["I", "II", "III", "IV", "V"],
            "Professor": ["I", "II", "III", "IV", "V", "VI"],
        }

        def split_role(role_text: str):
            """Return (rank, roman) if role is like 'Assistant Professor II'."""
            if not role_text:
                return "Instructor", "I"
            for r in RANKS:
                if role_text.startswith(r):
                    tail = role_text[len(r):].strip()
                    if tail in sum(RANKS.values(), []):
                        return r, tail
                    return r, RANKS[r][0]
            return "Instructor", "I"

        rank_var = StringVar(value="Instructor")
        subrank_var = StringVar(value="I")

        def update_subranks(*_):
            vals = RANKS.get(rank_var.get(), ["I"])
            sub_menu.configure(values=vals)
            if subrank_var.get() not in vals:
                subrank_var.set(vals[0])

        CTkLabel(parent, text="Rank").pack(fill="x", padx=20, pady=(5, 0))
        rank_menu = CTkOptionMenu(parent, variable=rank_var, values=list(RANKS.keys()))
        rank_menu.pack(fill="x", padx=20, pady=2)
        rank_var.trace_add("write", update_subranks)

        CTkLabel(parent, text="Sub-rank").pack(fill="x", padx=20, pady=(5, 0))
        sub_menu = CTkOptionMenu(parent, variable=subrank_var, values=RANKS[rank_var.get()])
        sub_menu.pack(fill="x", padx=20, pady=2)

        # --- Pre-fill for edit ---
        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a faculty to edit.")
                self.sidepanel.destroy()
                return

            record_id = int(selected[0])                       # << use iid as the DB id
            fullname, dept, _rank_label = self.tree.item(selected[0], "values")

            with db.connect() as conn:
                data = conn.execute(
                    "SELECT first_name, middle_name, last_name, suffix, role FROM faculty WHERE id=?",
                    (record_id,)
                ).fetchone()
            if data:
                first.insert(0, data[0] or "")
                middle.insert(0, data[1] or "")
                last.insert(0, data[2] or "")
                suffix.insert(0, data[3] or "")
                dept_var.set(dept)

                # Prefill rank/subrank
                rank_name, roman = split_role(data[4])
                rank_var.set(rank_name)
                update_subranks()
                subrank_var.set(roman)


        # --- Submit Handler ---
        def submit():
            try:
                with db.connect() as conn:
                    dept_id = conn.execute(
                        "SELECT id FROM departments WHERE name=?",
                        (dept_var.get(),)
                    ).fetchone()[0]

                    # 🆕 Combine rank + subrank → role string
                    role_text = f"{rank_var.get()} {subrank_var.get()}"

                    if mode == "add":
                        conn.execute("""
                            INSERT INTO faculty (first_name, middle_name, last_name, suffix, department_id, role)
                            VALUES (?,?,?,?,?,?)
                        """, (
                            first.get().strip(),
                            middle.get().strip() or None,
                            last.get().strip(),
                            suffix.get().strip() or None,
                            dept_id,
                            role_text
                        ))
                    else:
                        conn.execute("""
                            UPDATE faculty
                            SET first_name=?, middle_name=?, last_name=?, suffix=?, department_id=?, role=?
                            WHERE id=?
                        """, (
                            first.get().strip(),
                            middle.get().strip() or None,
                            last.get().strip(),
                            suffix.get().strip() or None,
                            dept_id,
                            role_text,
                            record_id
                        ))

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

        # --- Department Name ---
        name_entry = CTkEntry(parent, placeholder_text="Department Name")
        name_entry.pack(fill="x", padx=20, pady=(10, 6))

        # --- Dean dropdown ---
        CTkLabel(parent, text="Dean (must belong to this department)",
                font=("Arial", 12)).pack(fill="x", padx=20, pady=(4, 0))
        dean_var = StringVar()
        dean_menu = CTkOptionMenu(parent, variable=dean_var, values=["(None for now)"])
        dean_menu.pack(fill="x", padx=20, pady=6)
        dean_var.set("(None for now)")

        # Helpers
        def _faculty_in_department(dept_id: int):
            with db.connect() as conn:
                return conn.execute("""
                    SELECT id, full_name
                    FROM faculty
                    WHERE department_id = ?
                    ORDER BY full_name
                """, (dept_id,)).fetchall()

        def _all_faculty_with_dept_label():
            with db.connect() as conn:
                return conn.execute("""
                    SELECT f.id, f.full_name, COALESCE(d.name, '—') as dept_name
                    FROM faculty f
                    LEFT JOIN departments d ON d.id = f.department_id
                    ORDER BY f.full_name
                """).fetchall()

        # Prefill (Edit)
        record_id = None
        if mode == "edit" and self.tree:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No selection", "Select a department to edit.")
                self.sidepanel.destroy()
                return

            record_id = int(selected[0])  # iid as id
            name, _count = self.tree.item(selected[0], "values")
            name_entry.insert(0, name)

            # Load faculty limited to this department
            rows = _faculty_in_department(record_id)
            dean_options = ["(None)"] + [r[1] for r in rows]
            dean_menu.configure(values=dean_options)
            dean_var.set("(None)")

            # Preselect current dean if any
            with db.connect() as conn:
                row = conn.execute("SELECT dean_id FROM departments WHERE id=?", (record_id,)).fetchone()
            if row and row[0]:
                dean_id = row[0]
                id_to_name = {fid: fname for fid, fname in rows}
                dean_var.set(id_to_name.get(dean_id, "(None)"))

        else:
            # ADD mode: user can pick None (recommended) or any faculty (DB trigger enforces department match)
            rows = _all_faculty_with_dept_label()
            dean_options = ["(None for now)"] + [f"{fname}  —  {dept}" for _, fname, dept in rows]
            dean_menu.configure(values=dean_options)
            dean_var.set("(None for now)")

        def submit():
            try:
                dept_name = name_entry.get().strip()
                if not dept_name:
                    messagebox.showerror("Invalid Input", "Department name is required.")
                    return

                with db.connect() as conn:
                    if mode == "add":
                        # 1) create department (without dean by default)
                        conn.execute("INSERT INTO departments (name) VALUES (?)", (dept_name,))
                        conn.commit()

                        # 2) try to set dean if the user selected a faculty
                        if dean_var.get() != "(None for now)":
                            # map display back to faculty id
                            all_rows = _all_faculty_with_dept_label()
                            display_to_id = {f"{fname}  —  {dept}": fid for fid, fname, dept in all_rows}
                            chosen = dean_var.get()
                            dean_id = display_to_id.get(chosen)

                            # fetch the new department id
                            new_id = conn.execute("SELECT id FROM departments WHERE name=?", (dept_name,)).fetchone()[0]

                            # This UPDATE will succeed only if the chosen faculty already belongs to this dept (DB trigger)
                            try:
                                conn.execute("UPDATE departments SET dean_id=? WHERE id=?", (dean_id, new_id))
                                conn.commit()
                            except Exception as e:
                                # likely trigger: "Dean must belong to the same department"
                                messagebox.showwarning(
                                    "Dean not set",
                                    "The selected dean does not belong to this department yet.\n"
                                    "Department was created successfully; set the dean after assigning the faculty to this department."
                                )

                    else:
                        # EDIT: update name and dean_id (if selected)
                        # resolve dean choice → faculty id (limited to same dept)
                        if dean_var.get() in ("(None)", "(None for now)"):
                            dean_id = None
                        else:
                            rows = _faculty_in_department(record_id)
                            name_to_id = {fname: fid for fid, fname in rows}
                            dean_id = name_to_id.get(dean_var.get())
                            if dean_id is None and dean_var.get():
                                messagebox.showerror("Invalid Dean", "Please choose a dean from this department.")
                                return

                        conn.execute("UPDATE departments SET name=?, dean_id=? WHERE id=?",
                                    (dept_name, dean_id, record_id))
                        conn.commit()

                self.sidepanel.destroy()
                self.show_tab("Departments")

            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)


    def build_block_form(self, parent, mode):
        CTkLabel(parent, text="Block Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        # Program dropdown
        prog_var = StringVar()
        prog_options, prog_map = [], {}
        with db.connect() as conn:
            rows = conn.execute("SELECT id, code FROM programs ORDER BY code").fetchall()
            for pid, pcode in rows:
                prog_options.append(pcode)
                prog_map[pcode] = pid
        if not prog_options:
            CTkLabel(parent, text="Create a Program first.", text_color="#B22222").pack(pady=10)
            return
        prog_menu = CTkOptionMenu(parent, variable=prog_var, values=prog_options)
        prog_menu.pack(fill="x", padx=20, pady=5)
        prog_var.set(prog_options[0])

        # Year Level
        year_var = StringVar(value="1")
        CTkOptionMenu(parent, variable=year_var, values=["1", "2", "3", "4"]).pack(fill="x", padx=20, pady=5)

        # Section
        section_var = StringVar(value="A")
        CTkOptionMenu(parent, variable=section_var, values=["A", "B", "C", "D"]).pack(fill="x", padx=20, pady=5)

        # Academic Year
        sy_entry = CTkEntry(parent, placeholder_text="Academic Year (e.g. 2025-2026)")
        sy_entry.pack(fill="x", padx=20, pady=5)

        # Semester (auto-detected)
        sem_var = StringVar()
        now = datetime.datetime.now()  # <-- you imported the module, so use datetime.datetime
        month = now.month
        # 1st: Aug–Dec, 2nd: Jan–Jun, Summer: Jul
        current_sem = "1st" if 8 <= month <= 12 else ("2nd" if 1 <= month <= 6 else "Summer")
        sem_var.set(current_sem)

        # 🔁 Auto-compute AY from semester & current year
        y = now.year
        if current_sem == "1st":
            ay = f"{y}-{y+1}"
        else:  # "2nd" or "Summer"
            ay = f"{y-1}-{y}"

        # Prefill AY with auto value (user can still override if needed)
        sy_entry.delete(0, "end")
        sy_entry.insert(0, ay)

        CTkLabel(parent, text=f"Semester: {sem_var.get()}",
                font=("Arial", 14), text_color="#333").pack(pady=5)

        # Pre-fill for edit
        record_id = None
        if mode == "edit" and self.tree:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select a block to edit.")
                self.sidepanel.destroy()
                return
            record_id = int(self.tree.selection()[0])     # << use iid, not values[0]

            with db.connect() as conn:
                row = conn.execute("""
                    SELECT program_id, year_level, section, academic_year, semester
                    FROM blocks WHERE id=?
                """, (record_id,)).fetchone()
            if row:
                pid, yl, sec, ay, sem = row
                # invert maps
                inv_prog = {v:k for k,v in prog_map.items()}
                prog_var.set(inv_prog.get(pid, prog_options[0]))
                year_var.set(str(yl)); section_var.set(sec)
                sy_entry.insert(0, ay)
                sem_var.set(sem)

        def submit():
            try:
                program_id = prog_map[prog_var.get()]
                year_level = int(year_var.get())
                section = section_var.get().strip()
                academic_year = sy_entry.get().strip()
                semester = sem_var.get()

                if not academic_year:
                    messagebox.showerror("Invalid Input", "Academic year cannot be empty.")
                    return

                with db.connect() as conn:
                    if mode == "add":
                        #  prevent duplicate blocks (uses the UNIQUE constraint)
                        exists = conn.execute("""
                            SELECT 1 FROM blocks
                            WHERE program_id=? AND year_level=? AND section=? AND academic_year=? AND semester=?
                        """, (program_id, year_level, section, academic_year, semester)).fetchone()
                        if exists:
                            messagebox.showerror("Duplicate", "This block already exists.")
                            return

                        #  do the insert
                        conn.execute("""
                            INSERT INTO blocks (program_id, year_level, section, academic_year, semester)
                            VALUES (?, ?, ?, ?, ?)
                        """, (program_id, year_level, section, academic_year, semester))

                    else:
                        #  update path
                        conn.execute("""
                            UPDATE blocks
                            SET program_id=?, year_level=?, section=?, academic_year=?, semester=?
                            WHERE id=?
                        """, (program_id, year_level, section, academic_year, semester, record_id))

                    conn.commit()

                self.sidepanel.destroy()
                self.show_tab("Blocks")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)

    def build_teaching_assignment_form(self, parent, mode):
        CTkLabel(parent, text="Teaching Assignment Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        # Faculty dropdown
        faculty_var = StringVar()
        faculty_options = ["TBA"]; faculty_map = {"TBA": None}
        with db.connect() as conn:
            for fid, fname in conn.execute("SELECT id, full_name FROM faculty ORDER BY full_name"):
                faculty_options.append(fname); faculty_map[fname] = fid
        CTkOptionMenu(parent, variable=faculty_var, values=faculty_options).pack(fill="x", padx=20, pady=5)
        faculty_var.set("TBA")

        # ---- Subject dropdown (starts disabled/empty) ----
        subject_var = StringVar()
        subject_options = []        # will be populated after block selection
        subject_map = {}            # label -> id, rebuilt each time
        subject_menu = CTkOptionMenu(parent, variable=subject_var, values=["— Select a block first —"])
        subject_menu.pack(fill="x", padx=20, pady=5)
        subject_menu.configure(state="disabled")

        # ---- Block dropdown (select first, then subjects will filter) ----
        block_var = StringVar(); block_options = []; block_map = {}
        with db.connect() as conn:
            for bid, label in conn.execute("""
                SELECT 
                    b.id,
                    p.code || ' - ' || b.year_level || b.section AS block_label
                FROM blocks b
                JOIN programs p ON p.id = b.program_id
                ORDER BY p.code, b.year_level, b.section
            """):
                block_options.append(label)
                block_map[label] = bid

        block_menu = CTkOptionMenu(parent, variable=block_var, values=["Merged"] + block_options)
        block_menu.pack(fill="x", padx=20, pady=5)
        block_var.set("Select Block")

        
        # Academic Year
        ay_entry = CTkEntry(parent, placeholder_text="Academic Year (e.g. 2025-2026)")
        ay_entry.pack(fill="x", padx=20, pady=5)

        # Semester (auto-detected)
        sem_var = StringVar()
        now = datetime.datetime.now()  # <-- you imported the module, so use datetime.datetime
        month = now.month
        # 1st: Aug–Dec, 2nd: Jan–Jun, Summer: Jul
        current_sem = "1st" if 8 <= month <= 12 else ("2nd" if 1 <= month <= 6 else "Summer")
        sem_var.set(current_sem)

        # 🔁 Auto-compute AY from semester & current year
        y = now.year
        if current_sem == "1st":
            ay = f"{y}-{y+1}"
        else:  # "2nd" or "Summer"
            ay = f"{y-1}-{y}"

        # Prefill AY with auto value (user can still override if needed)
        ay_entry.delete(0, "end")
        ay_entry.insert(0, ay)

        CTkLabel(parent, text=f"Semester: {sem_var.get()}",
                font=("Arial", 14), text_color="#333").pack(pady=5)

        # Expected students
        exp_entry = CTkEntry(parent, placeholder_text="Expected Students")
        exp_entry.pack(fill="x", padx=20, pady=5)

        # ---------- Helpers ----------
        def set_subject_menu(values, new_map, placeholder_if_empty="— No subjects available —"):
            """Utility to refresh the subject menu safely."""
            nonlocal subject_map
            subject_map = new_map or {}
            if not values:
                subject_menu.configure(values=[placeholder_if_empty])
                subject_var.set(placeholder_if_empty)
                subject_menu.configure(state="disabled")
            else:
                subject_menu.configure(values=values)
                subject_var.set(values[0])
                subject_menu.configure(state="normal")

        def load_all_subjects():
            """Populate with all subjects (used when 'Merged' is selected)."""
            opts, smap = [], {}
            with db.connect() as conn:
                for sid, label in conn.execute(
                    "SELECT id, code || ' - ' || title FROM subjects ORDER BY code"
                ):
                    opts.append(label); smap[label] = sid
            set_subject_menu(opts, smap, "— No subjects (DB empty) —")

        def load_subjects_for_block_label(blabel: str):
            """Filter subjects by the chosen block's program/year/semester."""
            bid = block_map.get(blabel)
            if not bid:
                set_subject_menu([], {}, "— Invalid block —")
                return
            with db.connect() as conn:
                # get the block's program/year/sem to filter subjects
                prow = conn.execute("""
                    SELECT program_id, year_level, semester
                    FROM blocks WHERE id=?
                """, (bid,)).fetchone()
                if not prow:
                    set_subject_menu([], {}, "— Block not found —"); return
                program_id, year_level, sem = prow
                opts, smap = [], {}
                for sid, label in conn.execute("""
                    SELECT id, code || ' - ' || title
                    FROM subjects
                    WHERE program_id=? AND year_level=? AND semester=?
                    ORDER BY code
                """, (program_id, year_level, sem)):
                    opts.append(label); smap[label] = sid
            set_subject_menu(opts, smap, "— No subjects for this block —")

        # react to block selection to populate subjects
        def on_block_change(*_):
            bval = block_var.get()
            if bval == "Select Block":
                load_all_subjects()
            else:
                load_subjects_for_block_label(bval)

        block_var.trace_add("write", on_block_change)

        # ---------- Edit prefill ----------
        record_id = None
        if mode == "edit" and self.tree:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select a teaching assignment to edit.")
                self.sidepanel.destroy(); return
            record_id = int(self.tree.selection()[0])
            with db.connect() as conn:
                row = conn.execute("""
                    SELECT ta.teacher_id, ta.subject_id, ta.block_id,
                        ta.academic_year, ta.semester, ta.expected_students,
                        f.full_name
                    FROM teaching_assignments ta
                    LEFT JOIN faculty f ON f.id = ta.teacher_id
                    WHERE ta.id=?
                """, (record_id,)).fetchone()
            if row:
                fac_id, subj_id, blk_id, ay, sem, exp, fac_name = row
                faculty_var.set(fac_name if fac_name else "TBA")
                ay_entry.insert(0, ay); sem_var.set(sem); exp_entry.insert(0, str(exp))

                # populate subjects appropriately and select current one
                if blk_id is None:
                    load_all_subjects()
                else:
                    # set block menu to the label matching blk_id
                    inv_blk = {v:k for k,v in block_map.items()}
                    b_label = inv_blk.get(blk_id, "Merged")
                    block_var.set(b_label)
                    # this triggers on_block_change -> loads filtered list
                # after menu is populated, set the current subject by id
                # build inverse map (id -> label)
                inv_subj = None
                if subject_map:
                    inv_subj = {v:k for k,v in subject_map.items()}
                # If subject_menu hasn’t loaded yet (race), force load based on blk_id
                if not inv_subj:
                    if blk_id is None:
                        load_all_subjects()
                    else:
                        load_subjects_for_block_label(b_label)
                    inv_subj = {v:k for k,v in subject_map.items()}
                if subj_id in (subject_map.values()):
                    subject_var.set(inv_subj.get(subj_id, subject_var.get()))
                subject_menu.configure(state="disabled")  # keep consistent with your previous behavior

        # ---------- Submit ----------
        def submit():
            try:
                # Validate subject selected
                chosen = subject_var.get()
                if chosen not in subject_map:
                    messagebox.showerror("Invalid Input", "Please select a subject after choosing a block.")
                    return

                # Expected students must be integer (no strings)
                raw_exp = exp_entry.get().strip()
                if raw_exp == "":
                    messagebox.showerror("Invalid Input", "Expected students is required.")
                    return
                try:
                    expected = int(raw_exp)
                    if expected < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid Input", "Expected students must be a whole number (0 or greater).")
                    return

                faculty_id = faculty_map.get(faculty_var.get())
                
                if faculty_id is None:
                    messagebox.showerror("Invalid Input", "Please select a teacher before adding a teaching assignment.")
                    return
                
                subject_id = subject_map[chosen]
                block_id = None if block_var.get() == "Merged" else block_map[block_var.get()]
                academic_year = ay_entry.get().strip()
                semester = sem_var.get()
                if not academic_year:
                    messagebox.showerror("Invalid Input", "Academic year is required.")
                    return

                with db.connect() as conn:
                    # integrity check: if there is a block, ensure block & subject align
                    if block_id is not None:
                        valid = conn.execute("""
                            SELECT 1
                            FROM blocks b
                            JOIN subjects s
                            ON s.program_id = b.program_id
                            AND s.year_level = b.year_level
                            AND s.semester   = b.semester
                            WHERE b.id = ? AND s.id = ?
                        """, (block_id, subject_id)).fetchone()
                        if not valid:
                            messagebox.showerror("Invalid", "Block and subject do not match in program/year/semester.")
                            return

                    if mode == "add":
                        conn.execute("""
                            INSERT INTO teaching_assignments
                                (teacher_id, subject_id, block_id, academic_year, semester, expected_students)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (faculty_id, subject_id, block_id, academic_year, semester, expected))
                    else:
                        conn.execute("""
                            UPDATE teaching_assignments
                            SET teacher_id=?, academic_year=?, semester=?, expected_students=?
                            WHERE id=?
                        """, (faculty_id, academic_year, semester, expected, record_id))
                    conn.commit()

                self.sidepanel.destroy()
                self.show_tab("Teaching Assignments")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)

    
    def build_program_form(self, parent, mode):
        CTkLabel(parent, text="Program Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        code_e = CTkEntry(parent, placeholder_text="Program Code (e.g., BSIT)")
        code_e.pack(fill="x", padx=20, pady=5)

        name_e = CTkEntry(parent, placeholder_text="Program Name")
        name_e.pack(fill="x", padx=20, pady=5)

        dept_var = StringVar()
        dept_opts, dept_map = [], {}
        with db.connect() as conn:
            for did, dname in conn.execute("SELECT id, name FROM departments ORDER BY name"):
                dept_opts.append(dname); dept_map[dname] = did
        if not dept_opts:
            CTkLabel(parent, text="Create a Department first.", text_color="#B22222").pack(pady=10)
            return
        CTkOptionMenu(parent, variable=dept_var, values=dept_opts).pack(fill="x", padx=20, pady=5)
        dept_var.set(dept_opts[0])

        record_id = None
        if mode == "edit" and self.tree:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select a program to edit.")
                self.sidepanel.destroy(); return

            record_id = int(sel[0])                                # ← use iid
            code, name, dept = self.tree.item(sel[0], "values")    # ← visibles
            code_e.insert(0, code); name_e.insert(0, name); dept_var.set(dept)


        def submit():
            try:
                code = code_e.get().strip()
                name = name_e.get().strip()
                dept_id = dept_map[dept_var.get()]
                if not code or not name:
                    messagebox.showerror("Invalid Input", "Code and Name are required.")
                    return
                with db.connect() as conn:
                    if mode == "add":
                        conn.execute("INSERT INTO programs (code, name, department_id) VALUES (?,?,?)",
                                    (code, name, dept_id))
                    else:
                        conn.execute("UPDATE programs SET code=?, name=?, department_id=? WHERE id=?",
                                    (code, name, dept_id, record_id))
                    conn.commit()
                self.sidepanel.destroy()
                self.show_tab("Programs")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)



    def build_subject_form(self, parent, mode):
        CTkLabel(parent, text="Subject Form", font=("Arial", 18, "bold"),
                text_color="#691612").pack(pady=10)

        code_e  = CTkEntry(parent, placeholder_text="Subject Code (unique)")
        title_e = CTkEntry(parent, placeholder_text="Subject Title")
        units_e = CTkEntry(parent, placeholder_text="Units (default 3)")
        code_e.pack(fill="x", padx=20, pady=5)
        title_e.pack(fill="x", padx=20, pady=5)
        units_e.pack(fill="x", padx=20, pady=5)

        year_var = StringVar(value="1")
        CTkOptionMenu(parent, variable=year_var, values=["1","2","3","4"]).pack(fill="x", padx=20, pady=5)

        sem_var = StringVar(value="1st")
        CTkOptionMenu(parent, variable=sem_var, values=["1st","2nd","Summer"]).pack(fill="x", padx=20, pady=5)

        # Program dropdown (required)
        prog_var, prog_opts, prog_map = StringVar(), [], {}
        with db.connect() as conn:
            for pid, pcode in conn.execute("SELECT id, code FROM programs ORDER BY code"):
                prog_opts.append(pcode); prog_map[pcode] = pid
        if not prog_opts:
            CTkLabel(parent, text="Create a Program first.", text_color="#B22222").pack(pady=10)
            return
        CTkOptionMenu(parent, variable=prog_var, values=prog_opts).pack(fill="x", padx=20, pady=5)
        prog_var.set(prog_opts[0])

        # Optional department shortcut
        dept_var, dept_opts, dept_map = StringVar(), ["(none)"], {"(none)": None}
        with db.connect() as conn:
            for did, dname in conn.execute("SELECT id, name FROM departments ORDER BY name"):
                dept_opts.append(dname); dept_map[dname] = did
        CTkOptionMenu(parent, variable=dept_var, values=dept_opts).pack(fill="x", padx=20, pady=5)
        dept_var.set("(none)")

        record_id = None
        if mode == "edit" and self.tree:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select a subject to edit.")
                self.sidepanel.destroy(); return

            record_id = int(sel[0])                                 # ← use iid
            code, title, units, year_lv, sem, prog_code, dept_name = self.tree.item(sel[0], "values")
            code_e.insert(0, code); title_e.insert(0, title)
            units_e.insert(0, str(units)); year_var.set(str(year_lv))
            sem_var.set(sem); prog_var.set(prog_code)
            dept_var.set(dept_name if dept_name != "—" else "(none)")


        def submit():
            try:
                code  = code_e.get().strip()
                title = title_e.get().strip()
                units = int(units_e.get().strip()) if units_e.get().strip() else 3
                year_level = int(year_var.get())
                semester   = sem_var.get()
                program_id = prog_map[prog_var.get()]
                department_id = dept_map[dept_var.get()]
                if not code or not title:
                    messagebox.showerror("Invalid Input", "Code and Title are required."); return
                with db.connect() as conn:
                    if mode == "add":
                        conn.execute("""
                            INSERT INTO subjects (code, title, units, year_level, semester, program_id, department_id)
                            VALUES (?,?,?,?,?,?,?)
                        """, (code, title, units, year_level, semester, program_id, department_id))
                    else:
                        conn.execute("""
                            UPDATE subjects
                            SET code=?, title=?, units=?, year_level=?, semester=?, program_id=?, department_id=?
                            WHERE id=?
                        """, (code, title, units, year_level, semester, program_id, department_id, record_id))
                    conn.commit()
                self.sidepanel.destroy()
                self.show_tab("Subjects")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(parent, text="Save", fg_color="#691612", command=submit).pack(pady=20)
    
    # ---------------- Query helpers---------------- #
    def _resolve_program_id_by_code(self, conn, code: str):
        row = conn.execute("SELECT id FROM programs WHERE code = ?", (code.strip(),)).fetchone()
        return row[0] if row else None

    def _resolve_subject_id_by_code(self, conn, code: str):
        row = conn.execute("SELECT id FROM subjects WHERE code = ?", (code.strip(),)).fetchone()
        return row[0] if row else None

    def _resolve_department_id_by_name(self, conn, name: str):
        row = conn.execute("SELECT id FROM departments WHERE name = ?", (name.strip(),)).fetchone()
        return row[0] if row else None

    def _parse_term_filters(self, term: str):
        """
        Return (academic_year, semester) if term matches either, else (None, None).
        AY pattern: 'YYYY-YYYY'
        Semester: case-insensitive '1st','2nd','Summer'
        """
        t = (term or "").strip()
        ay = t if len(t) == 9 and t[0:4].isdigit() and t[4] == '-' and t[5:9].isdigit() else None
        sem = t.capitalize() if t.lower() in ("1st","2nd","summer") else None
        return ay, sem

    # ---------------- Backup / Restore ---------------- #
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


