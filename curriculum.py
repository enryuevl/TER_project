from customtkinter import *
from tkinter import ttk, messagebox
import db

class CurriculumPage:
    def __init__(self, master, ctx):
        self.master = master
        self.ctx = ctx          # same ctx you use in AccountsDatabasePage
        self.current_curriculum_id = None
        self.current_program_id = None
        self.tab_buttons = {}
        self._build_ui()
        self._load_curricula()

    # ---------- helpers about role/department ----------
    def _is_operator(self):
        return (self.ctx.role or "").lower() in ("operator", "dean") \
               and self.ctx.department_id is not None

    # ---------- UI ----------
    def _build_ui(self):
        for w in self.master.winfo_children():
            w.destroy()

        self.container = CTkFrame(self.master, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title bar (like other pages)
        title_bar = CTkFrame(self.container, fg_color="#BF3131", height=70, corner_radius=10)
        title_bar.pack(fill="x", padx=10, pady=(0, 12))
        CTkLabel(
            title_bar, text="Curriculum Management",
            font=("Poppins", 18, "bold"), text_color="#FFFFFF"
        ).pack(side="left", padx=20, pady=12)

        # Top buttons: Curriculums | Add | Remove
        top_bar = CTkFrame(self.container, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(0, 8))

        CTkButton(
            top_bar, text="Curriculums", state="disabled",
            fg_color="#691612", text_color="#FFFFFF"
        ).pack(side="left", padx=(0, 8))

        CTkButton(
            top_bar, text="Add", width=90,
            fg_color="#BF3131", text_color="#FFFFFF",
            command=self._open_add_curriculum_dialog
        ).pack(side="left", padx=4)

        CTkButton(
            top_bar, text="Remove", width=90,
            fg_color="#AC5353", text_color="#FFFFFF",
            command=self._delete_selected_curriculum
        ).pack(side="left", padx=4)

        # Main split: left list of curricula, right subjects
        main = CTkFrame(self.container, fg_color="#FFFFFF", corner_radius=10)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        main.grid_columnconfigure(0, weight=0, minsize=260)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=0)

        # ---- Left: list of curricula ----
        left = CTkFrame(main, fg_color="#F8F9FA", corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=10)

        CTkLabel(left, text="List of Curriculums",
                 font=("Poppins", 14, "bold"), text_color="#691612")\
            .pack(anchor="w", padx=10, pady=(10, 4))

        self.curr_tree = ttk.Treeview(
            left, columns=("name", "program", "active"),
            show="headings", height=18
        )
        self.curr_tree.heading("name", text="Curriculum")
        self.curr_tree.heading("program", text="Program")
        self.curr_tree.heading("active", text="Active")
        self.curr_tree.column("name", width=140)
        self.curr_tree.column("program", width=80)
        self.curr_tree.column("active", width=60, anchor="center")
        self.curr_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.curr_tree.bind("<<TreeviewSelect>>", self._on_curriculum_selected)

        # ---- Right: subjects in selected curriculum ----
        right = CTkFrame(main, fg_color="#F8F9FA", corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 10), pady=10)

        CTkLabel(right, text="Subjects in Selected Curriculum",
                 font=("Poppins", 14, "bold"), text_color="#691612")\
            .pack(anchor="w", padx=10, pady=(10, 4))

        self.subj_tree = ttk.Treeview(
            right,
            columns=("code", "title", "year", "sem"),
            show="headings", height=18
        )
        for col, text, w in [
            ("code", "Code", 90),
            ("title", "Title", 260),
            ("year", "Year", 50),
            ("sem", "Sem", 70),
        ]:
            self.subj_tree.heading(col, text=text)
            self.subj_tree.column(col, width=w, anchor="w")
        self.subj_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ---- Bottom buttons: add/remove subjects, set active ----
        bottom = CTkFrame(main, fg_color="transparent")
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        CTkButton(
            bottom, text="Add Subjects",
            fg_color="#691612", text_color="#FFFFFF",
            hover_color="#8B1D18",
            command=self._open_subject_picker
        ).pack(side="left", padx=5, pady=5)

        CTkButton(
            bottom, text="Remove Subjects",
            fg_color="#BF3131", text_color="#FFFFFF",
            hover_color="#8B1D18",
            command=self._remove_selected_subjects
        ).pack(side="left", padx=5, pady=5)

        CTkButton(
            bottom, text="Set as Active",
            fg_color="#AC5353", text_color="#FFFFFF",
            hover_color="#8B1D18",
            command=self._set_curriculum_active
        ).pack(side="left", padx=5, pady=5)

        
    # ---------- load data ----------
    def _load_curricula(self):
        self.curr_tree.delete(*self.curr_tree.get_children())
        with db.connect() as conn:
            params = []
            where = []
            sql = """
                SELECT c.id, c.name, p.code, c.is_active, c.program_id
                FROM curricula c
                JOIN programs p ON p.id = c.program_id
            """
            if self._is_operator():
                where.append("p.department_id = ?")
                params.append(self.ctx.department_id)
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY p.code, c.name"

            for cid, name, pcode, active, prog_id in conn.execute(sql, tuple(params)):
                tag = "active" if active else ""
                self.curr_tree.insert(
                    "", "end", iid=str(cid),
                    values=(name, pcode, "Yes" if active else ""),
                    tags=(tag,)
                )
        # remember styles if desired
        self.current_curriculum_id = None
        self.current_program_id = None
        self.subj_tree.delete(*self.subj_tree.get_children())

    def _on_curriculum_selected(self, event=None):
        sel = self.curr_tree.selection()
        if not sel:
            return
        cid = int(sel[0])
        self.current_curriculum_id = cid

        # get program_id for this curriculum
        with db.connect() as conn:
            row = conn.execute(
                "SELECT program_id FROM curricula WHERE id = ?", (cid,)
            ).fetchone()
        self.current_program_id = row[0] if row else None
        self._load_curriculum_subjects()

    def _load_curriculum_subjects(self):
        self.subj_tree.delete(*self.subj_tree.get_children())
        if not self.current_curriculum_id:
            return
        with db.connect() as conn:
            sql = """
                SELECT s.id, s.code, s.title, s.year_level, s.semester
                FROM curriculum_subjects cs
                JOIN subjects s ON s.id = cs.subject_id
                WHERE cs.curriculum_id = ?
                ORDER BY s.year_level, s.semester, s.code
            """
            for sid, code, title, year, sem in conn.execute(sql, (self.current_curriculum_id,)):
                self.subj_tree.insert("", "end", iid=str(sid),
                                      values=(code, title, year, sem))

    # ---------- Add / delete curriculum ----------

    def _delete_selected_curriculum(self):
        sel = self.curr_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a curriculum to remove.")
            return
        cid = int(sel[0])
        if not messagebox.askyesno("Confirm", "Delete this curriculum and all its subject links?"):
            return
        with db.connect() as conn:
            conn.execute("DELETE FROM curricula WHERE id=?", (cid,))
            conn.commit()
        self._load_curricula()

    # ---------- Add/remove subjects to curriculum ----------
    def _open_subject_picker(self):
        if not self.current_curriculum_id or not self.current_program_id:
            messagebox.showwarning("No curriculum", "Select a curriculum first.")
            return

        win = CTkToplevel(self.master)
        win.title("Select Subjects for Curriculum")
        win.geometry("700x520")
        win.grab_set()

        # header
        CTkLabel(win, text="Select Subjects to be added to the curriculum",
                 font=("Poppins", 14, "bold"), text_color="#691612")\
            .pack(pady=(10, 4))

        # show curriculum name
        with db.connect() as conn:
            row = conn.execute("SELECT name FROM curricula WHERE id=?",
                               (self.current_curriculum_id,)).fetchone()
        CTkLabel(win, text=row[0] if row else "",
                 font=("Poppins", 12), text_color="#111827")\
            .pack(pady=(0, 6))

        # scrollable checklist
        scroll = CTkScrollableFrame(win, fg_color="#FFFFFF")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # load all subjects of this program, mark those already in curriculum
        selected_ids = set()
        with db.connect() as conn:
            # current links
            rows = conn.execute(
                "SELECT subject_id FROM curriculum_subjects WHERE curriculum_id=?",
                (self.current_curriculum_id,)
            ).fetchall()
            selected_ids = {r[0] for r in rows}

            subjects = conn.execute("""
                SELECT id, code, title, year_level, semester
                FROM subjects
                WHERE program_id=?
                ORDER BY year_level, semester, code
            """, (self.current_program_id,)).fetchall()

        self._subject_vars = {}   # subject_id -> IntVar

        for sid, code, title, year, sem in subjects:
            var = IntVar(value=1 if sid in selected_ids else 0)
            self._subject_vars[sid] = var
            text = f"[Y{year} {sem}] {code} - {title}"
            CTkCheckBox(
                scroll, text=text, variable=var,
                font=("Poppins", 12)
            ).pack(anchor="w", padx=10, pady=2)

        # bottom buttons inside popup
        btn_row = CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", pady=8)

        CTkButton(
            btn_row, text="Add new subject",
            fg_color="#BF3131", text_color="#FFFFFF",
            command=lambda: self._open_add_subject(win)
        ).pack(side="left", padx=10)

        def finish():
            self._save_subject_selection()
            win.destroy()
            self._load_curriculum_subjects()

        CTkButton(
            btn_row, text="Finish",
            fg_color="#691612", text_color="#FFFFFF",
            command=finish
        ).pack(side="right", padx=10)

    def _save_subject_selection(self):
        chosen = {sid for sid, var in self._subject_vars.items() if var.get() == 1}
        with db.connect() as conn:
            # existing links
            rows = conn.execute(
                "SELECT subject_id FROM curriculum_subjects WHERE curriculum_id=?",
                (self.current_curriculum_id,)
            ).fetchall()
            existing = {r[0] for r in rows}

            to_add = chosen - existing
            to_remove = existing - chosen

            for sid in to_add:
                conn.execute(
                    "INSERT OR IGNORE INTO curriculum_subjects (curriculum_id, subject_id) "
                    "VALUES (?, ?)",
                    (self.current_curriculum_id, sid)
                )

            if to_remove:
                conn.execute(
                    "DELETE FROM curriculum_subjects "
                    "WHERE curriculum_id=? AND subject_id IN (%s)" %
                    ",".join("?" * len(to_remove)),
                    (self.current_curriculum_id, *to_remove)
                )
            conn.commit()


    def _open_add_subject(self, parent):
        """Small dialog from the picker to add a brand-new subject for this program."""
        win = CTkToplevel(parent)
        win.title("Add New Subject")
        win.geometry("400x320")
        win.grab_set()

        CTkLabel(win, text="Add subject to this program",
                 font=("Poppins", 14, "bold"),
                 text_color="#691612").pack(pady=10)

        code_e = CTkEntry(win, placeholder_text="Subject code")
        code_e.pack(fill="x", padx=20, pady=4)

        title_e = CTkEntry(win, placeholder_text="Subject title")
        title_e.pack(fill="x", padx=20, pady=4)

        units_e = CTkEntry(win, placeholder_text="Units (default 3)")
        units_e.pack(fill="x", padx=20, pady=4)

        year_var = StringVar(value="1")
        sem_var = StringVar(value="1st")
        CTkLabel(win, text="Year level").pack(anchor="w", padx=20, pady=(6, 0))
        year_menu = CTkOptionMenu(win, variable=year_var,
                                  values=["1", "2", "3", "4"],
                                  fg_color="#BF3131", button_color="#691612",
                                  text_color="#FFFFFF")
        year_menu.pack(fill="x", padx=20, pady=2)

        CTkLabel(win, text="Semester").pack(anchor="w", padx=20, pady=(6, 0))
        sem_menu = CTkOptionMenu(win, variable=sem_var,
                                 values=["1st", "2nd", "Summer"],
                                 fg_color="#BF3131", button_color="#691612",
                                 text_color="#FFFFFF")
        sem_menu.pack(fill="x", padx=20, pady=2)

        def submit():
            code = code_e.get().strip()
            title = title_e.get().strip()
            if not code or not title:
                messagebox.showerror("Invalid", "Code and title are required.")
                return
            try:
                units = int(units_e.get().strip() or "3")
            except ValueError:
                units = 3

            with db.connect() as conn:
                # get department_id from program
                row = conn.execute(
                    "SELECT department_id FROM programs WHERE id=?",
                    (self.current_program_id,)
                ).fetchone()
                dept_id = row[0] if row else None
                conn.execute("""
                    INSERT INTO subjects (code, title, units, year_level, semester,
                                          program_id, department_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (code, title, units, int(year_var.get()), sem_var.get(),
                      self.current_program_id, dept_id))
                conn.commit()
            win.destroy()
            # reload checklist in parent popup
            self._open_subject_picker()

        CTkButton(win, text="Add Subject", fg_color="#691612",
                  text_color="#FFFFFF", command=submit).pack(pady=12)

    def _remove_selected_subjects(self):
        if not self.current_curriculum_id:
            return
        sel = self.subj_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select subjects to remove.")
            return
        subject_ids = [int(iid) for iid in sel]
        if not messagebox.askyesno("Confirm", "Remove selected subjects from curriculum?"):
            return
        with db.connect() as conn:
            conn.execute(
                f"DELETE FROM curriculum_subjects "
                f"WHERE curriculum_id=? AND subject_id IN ({','.join('?'*len(subject_ids))})",
                (self.current_curriculum_id, *subject_ids)
            )
            conn.commit()
        self._load_curriculum_subjects()

    # ---------- Set active ----------
    def _set_curriculum_active(self):
        if not self.current_curriculum_id:
            messagebox.showwarning("No curriculum", "Select a curriculum first.")
            return
        with db.connect() as conn:
            # get the program_id of this curriculum
            row = conn.execute(
                "SELECT program_id FROM curricula WHERE id=?", (self.current_curriculum_id,)
            ).fetchone()
            if not row:
                return
            prog_id = row[0]
            # deactivate others of the same program
            conn.execute(
                "UPDATE curricula SET is_active=0 WHERE program_id=?",
                (prog_id,)
            )
            conn.execute(
                "UPDATE curricula SET is_active=1 WHERE id=?",
                (self.current_curriculum_id,)
            )
            conn.commit()
        self._load_curricula()

    def _open_add_curriculum_dialog(self):
        win = CTkToplevel(self.master)
        win.title("Add New Curriculum")
        win.geometry("360x260")
        win.grab_set()

        CTkLabel(win, text="Add new curriculum",
                font=("Poppins", 16, "bold"), text_color="#691612")\
            .pack(pady=(15, 5))

        # program dropdown ...
        prog_var = StringVar()
        options, prog_map = [], {}
        with db.connect() as conn:
            sql = "SELECT id, code FROM programs"
            params = []
            if self._is_operator():
                sql += " WHERE department_id=?"
                params.append(self.ctx.department_id)
            sql += " ORDER BY code"
            for pid, code in conn.execute(sql, tuple(params)):
                
                options.append(code)
                prog_map[code] = pid
            
        if not options:
            CTkLabel(
                win,
                text="Create a Program first in Data Management.",
                text_color="#B91C1C"
            ).pack(pady=10)
            return


        CTkLabel(win, text="Program").pack(anchor="w", padx=20)
        prog_menu = CTkOptionMenu(win, variable=prog_var, values=options,
                                fg_color="#BF3131", button_color="#691612",
                                text_color="#FFFFFF")
        prog_menu.pack(fill="x", padx=20, pady=(0, 10))
        prog_var.set(options[0])

        CTkLabel(win, text="Curriculum name").pack(anchor="w", padx=20)
        name_entry = CTkEntry(win, placeholder_text="e.g. 2024 Curriculum")
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        def submit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Invalid", "Curriculum name is required.")
                return

            program_id = prog_map[prog_var.get()]

            # IMPORTANT: only insert into curricula here.
            # Do NOT insert into curriculum_subjects – start empty.
            with db.connect() as conn:
                conn.execute(
                    "INSERT INTO curricula (program_id, name, is_active) "
                    "VALUES (?, ?, 0)",
                    (program_id, name)
                )
                conn.commit()

            win.destroy()
            self._load_curricula()     # refresh left list

        CTkButton(win, text="Add", fg_color="#691612",
                text_color="#FFFFFF", command=submit).pack(pady=10)
