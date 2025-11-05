
from customtkinter import *
from tkinter import messagebox
import datetime
import db

# ---------- Helpers: ensure tables for curriculum grouping ----------

def ensure_curriculum_tables():
    with db.connect() as conn:
        db.migrate_to_current_schema(conn)


class CurriculumLoadMixin:

    # ---------------- Tab entry ---------------- #
    def show_curriculum_load_tab(self, container, _search_entry_unused=None):
        ensure_curriculum_tables()

        self._curr = {
            "program_map": {},        # name -> id
            "program_names": [],
            "selected_subject_ids": set(),
            "selected_subject_rows": {},  # subject_id -> (code, title, year)
        }

        # layout frames
        root = CTkFrame(container, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=20, pady=10)
        root.grid_columnconfigure((0,1,2), weight=1)
        root.grid_rowconfigure(2, weight=1)

        # Title row
        header = CTkFrame(root, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        CTkLabel(header, text="Curriculum & Load Manager", font=("Poppins",18,"bold"), text_color="#691612").pack(anchor="w", pady=(0,6))

        # Filters row: Program, AY, Sem
        filters = CTkFrame(root, fg_color="transparent")
        filters.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0,8))
        for i in range(6):
            filters.grid_columnconfigure(i, weight=1)

        CTkLabel(filters, text="Program").grid(row=0, column=0, sticky="w")
        self._c_prog_var = StringVar()
        self._c_prog_menu = CTkOptionMenu(filters, variable=self._c_prog_var, values=["Loading..."])
        self._apply_dropdown_theme(self._c_prog_menu)
        self._c_prog_menu.grid(row=1, column=0, sticky="ew", padx=(0,8))

        CTkLabel(filters, text="Academic Year").grid(row=0, column=2, sticky="w")
        self._c_ay_entry = CTkEntry(filters, placeholder_text="YYYY-YYYY")
        self._c_ay_entry.grid(row=1, column=2, sticky="ew", padx=(0,8))

        CTkLabel(filters, text="Semester").grid(row=0, column=3, sticky="w")
        self._c_sem_var = StringVar(value=self._guess_semester())
        self._c_sem_menu = CTkOptionMenu(filters, variable=self._c_sem_var, values=["1st","2nd","Summer"])
        self._apply_dropdown_theme(self._c_sem_menu)
        self._c_sem_menu.grid(row=1, column=3, sticky="ew")

        # Main panes
        left = CTkFrame(root, fg_color="#FFFFFF", corner_radius=10)
        right = CTkFrame(root, fg_color="#FFFFFF", corner_radius=10)
        left.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0,8))
        right.grid(row=2, column=2, sticky="nsew", padx=(8,0))

        # Left: checklist of subjects for program/sem
        CTkLabel(left, text="Subjects in this Program & Semester", font=("Poppins",14,"bold")).pack(anchor="w", padx=14, pady=(12,6))
        self._c_list_frame = CTkScrollableFrame(left, fg_color="#FFFFFF")
        self._c_list_frame.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self._c_check_vars = {}  # subject_id -> IntVar

        # Right: selected buckets by year level
        CTkLabel(right, text="Selected Subjects", font=("Poppins",14,"bold")).pack(anchor="w", padx=14, pady=(12,6))
        self._c_sel_list = CTkScrollableFrame(right, fg_color="#FFFFFF")
        self._c_sel_list.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # Bottom buttons
        actions = CTkFrame(root, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8,0))
        actions.grid_columnconfigure((0,1,2,3), weight=1)

        self._c_add_curr_btn = CTkButton(actions, text="Add Curriculum", fg_color="#691612", command=self._open_load_dialog)
        self._c_add_curr_btn.grid(row=0, column=0, sticky="w")

        self._c_add_subject_btn = CTkButton(actions, text="Add Subject", fg_color="#BF3131", command=self._open_add_subject_dialog)
        self._c_add_subject_btn.grid(row=0, column=1, sticky="w", padx=(8,0))

        self._c_refresh_btn = CTkButton(actions, text="Refresh", fg_color="#AC5353", command=self._refresh_subject_list)
        self._c_refresh_btn.grid(row=0, column=2, sticky="w", padx=(8,0))

        # Load initial data
        self._populate_programs()
        self._prefill_ay()
        self._c_prog_menu.configure(command=lambda *_: self._refresh_subject_list())
        self._c_sem_menu.configure(command=lambda *_: self._refresh_subject_list())
        self._refresh_subject_list()

    # ---------- Small helpers ----------
    def _guess_semester(self):
        m = datetime.datetime.now().month
        return "1st" if 8 <= m <= 12 else ("2nd" if 1 <= m <= 6 else "Summer")

    def _prefill_ay(self):
        y = datetime.datetime.now().year
        sem = self._c_sem_var.get()
        ay = f"{y}-{y+1}" if sem == "1st" else f"{y-1}-{y}"
        self._c_ay_entry.delete(0, "end")
        self._c_ay_entry.insert(0, ay)

    def _populate_programs(self):
        try:
            with db.connect() as conn:
                rows = conn.execute("SELECT id, code FROM programs ORDER BY code").fetchall()
            names = []
            self._curr["program_map"].clear()
            for pid, code in rows:
                names.append(code)
                self._curr["program_map"][code] = pid
            if not names:
                names = ["(No programs)"]
            self._c_prog_menu.configure(values=names)
            self._c_prog_var.set(names[0])
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def _refresh_subject_list(self):
        # clear scroller
        for w in self._c_list_frame.winfo_children():
            w.destroy()
        for w in self._c_sel_list.winfo_children():
            w.destroy()
        self._c_check_vars.clear()
        self._curr["selected_subject_ids"].clear()
        self._curr["selected_subject_rows"].clear()

        prog_code = self._c_prog_var.get()
        sem = self._c_sem_var.get()
        if prog_code == "(No programs)":
            return
        pid = self._curr["program_map"].get(prog_code)
        if not pid:
            return
        try:
            with db.connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, code, title, year_level
                    FROM subjects
                    WHERE program_id=? AND semester=?
                    ORDER BY year_level, code
                    """,
                    (pid, sem)
                ).fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        # group by year
        groups = {}
        for sid, code, title, year in rows:
            groups.setdefault(year, []).append((sid, code, title, year))

        # build checklist
        for year in sorted(groups.keys()):
            CTkLabel(self._c_list_frame, text=f"Year {year}", font=("Poppins",13,"bold")).pack(anchor="w", padx=8, pady=(10,2))
            for sid, code, title, y in groups[year]:
                iv = IntVar(value=0)
                self._c_check_vars[sid] = iv
                def _mk(sid=sid, code=code, title=title, y=y):
                    def on_toggle():
                        if self._c_check_vars[sid].get():
                            self._curr["selected_subject_ids"].add(sid)
                            self._curr["selected_subject_rows"][sid] = (code, title, y)
                        else:
                            self._curr["selected_subject_ids"].discard(sid)
                            self._curr["selected_subject_rows"].pop(sid, None)
                        self._refresh_selected_panel()
                    return on_toggle
                cb = CTkCheckBox(
                    self._c_list_frame,
                    text=f"{code} — {title}",
                    variable=iv,          
                    onvalue=1, offvalue=0,
                    command=_mk()
                )

                cb.pack(fill="x", padx=12, pady=2)

        self._refresh_selected_panel()

    def _refresh_selected_panel(self):
        for w in self._c_sel_list.winfo_children():
            w.destroy()
        # bucket by year
        buckets = {}
        for sid, (code, title, y) in self._curr["selected_subject_rows"].items():
            buckets.setdefault(y, []).append((sid, code, title))
        if not buckets:
            CTkLabel(self._c_sel_list, text="No subjects selected.").pack(pady=12)
            return
        for year in sorted(buckets.keys()):
            box = CTkFrame(self._c_sel_list, fg_color="#F8F9FA", corner_radius=8)
            box.pack(fill="x", padx=8, pady=(8,4))
            CTkLabel(box, text=f"Year {year}", font=("Poppins",12,"bold")).pack(anchor="w", padx=10, pady=(8,4))
            for sid, code, title in buckets[year]:
                CTkLabel(box, text=f"• {code} — {title}").pack(anchor="w", padx=16, pady=2)

    # ---------- Dialogs ----------
    def _open_add_subject_dialog(self):
        dlg = CTkToplevel(self.master)
        dlg.title("Add new subject")
        dlg.geometry("420x520")
        dlg.grab_set()
        CTkLabel(dlg, text="Add new subject", font=("Poppins",16,"bold")).pack(pady=(12,6))

        code_e  = CTkEntry(dlg, placeholder_text="Course code")
        title_e = CTkEntry(dlg, placeholder_text="Course title")
        units_e = CTkEntry(dlg, placeholder_text="Units (e.g., 3)")
        code_e.pack(fill="x", padx=18, pady=6)
        title_e.pack(fill="x", padx=18, pady=6)
        units_e.pack(fill="x", padx=18, pady=6)

        CTkLabel(dlg, text="Year level").pack(anchor="w", padx=18)
        yvar = StringVar(value="1")
        ymenu = CTkOptionMenu(dlg, variable=yvar, values=["1","2","3","4"]) ; self._apply_dropdown_theme(ymenu)
        ymenu.pack(fill="x", padx=18, pady=6)

        CTkLabel(dlg, text="Program").pack(anchor="w", padx=18)
        pvar = StringVar()
        pnames = list(self._curr["program_map"].keys())
        if not pnames: pnames=["(No programs)"]
        pmenu = CTkOptionMenu(dlg, variable=pvar, values=pnames) ; self._apply_dropdown_theme(pmenu)
        pmenu.pack(fill="x", padx=18, pady=6)
        pvar.set(self._c_prog_var.get() if self._c_prog_var.get() in pnames else pnames[0])

        CTkLabel(dlg, text="Department").pack(anchor="w", padx=18)
        dvar = StringVar()
        # fetch depts
        with db.connect() as conn:
            depts = [r[0] for r in conn.execute("SELECT name FROM departments ORDER BY name").fetchall()]
        if not depts: depts=["(none)"]
        dmenu = CTkOptionMenu(dlg, variable=dvar, values=depts) ; self._apply_dropdown_theme(dmenu)
        dmenu.pack(fill="x", padx=18, pady=6)
        dvar.set(depts[0])

        CTkLabel(dlg, text="Semester").pack(anchor="w", padx=18)
        svar = StringVar(value=self._c_sem_var.get())
        smenu = CTkOptionMenu(dlg, variable=svar, values=["1st","2nd","Summer"]) ; self._apply_dropdown_theme(smenu)
        smenu.pack(fill="x", padx=18, pady=6)

        def submit():
            try:
                code = code_e.get().strip(); title = title_e.get().strip()
                if not code or not title:
                    messagebox.showerror("Invalid", "Code and title are required.", parent=dlg); return
                units = int(units_e.get().strip() or 3)
                year  = int(yvar.get())
                prog_id = self._curr["program_map"].get(pvar.get())
                if not prog_id:
                    messagebox.showerror("Invalid", "Pick a valid program.", parent=dlg); return
                with db.connect() as conn:
                    dept_id = None
                    row = conn.execute("SELECT id FROM departments WHERE name=?", (dvar.get(),)).fetchone()
                    if row: dept_id = row[0]
                    conn.execute(
                        """
                        INSERT INTO subjects (code, title, units, year_level, semester, program_id, department_id)
                        VALUES (?,?,?,?,?,?,?)
                        """,
                        (code, title, units, year, svar.get(), prog_id, dept_id)
                    )
                    conn.commit()
                dlg.destroy()
                self._refresh_subject_list()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=dlg)

        CTkButton(dlg, text="Add Subject", fg_color="#691612", command=submit).pack(pady=14)

    def _open_load_dialog(self):
        # verify selection
        if not self._curr["selected_subject_ids"]:
            messagebox.showwarning("No subjects", "Select one or more subjects first.")
            return

        prog_code = self._c_prog_var.get()
        pid = self._curr["program_map"].get(prog_code)
        ay = self._c_ay_entry.get().strip()
        sem = self._c_sem_var.get()

        if not ay:
            messagebox.showerror("Missing AY", "Please enter an academic year (e.g., 2025-2026).")
            return

        # check if a curriculum already exists for this program + AY + semester
        with db.connect() as conn:
            row = conn.execute(
                "SELECT id FROM curriculum WHERE program_id=? AND academic_year=? AND semester=?",
                (pid, ay, sem)
            ).fetchone()

            if row:
                curr_id = row[0]
                # 🟡 Curriculum already exists — prompt user
                choice = messagebox.askyesno(
                    "Curriculum Exists",
                    f"A curriculum for {prog_code} ({ay} • {sem}) already exists.\n\n"
                    "Do you want to edit the existing one instead?"
                )
                if not choice:
                    # user cancelled → abort
                    return
                else:
                    # open existing record for editing
                    self._show_assignment_dialog(curr_id, ay, sem)
                    return

            # else — create new curriculum record
            conn.execute(
                "INSERT INTO curriculum (program_id, academic_year, semester) VALUES (?,?,?)",
                (pid, ay, sem)
            )
            curr_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()

            # attach selected subjects to this new curriculum
            for sid in self._curr["selected_subject_ids"]:
                conn.execute(
                    "INSERT OR IGNORE INTO curriculum_subjects (curriculum_id, subject_id) VALUES (?,?)",
                    (curr_id, sid)
                )
            conn.commit()

        # open the assignment dialog for the new curriculum
        self._show_assignment_dialog(curr_id, ay, sem)


    def _show_assignment_dialog(self, curriculum_id: int, ay: str, sem: str):
        dlg = CTkToplevel(self.master)
        dlg.title("Teaching assignment panel")
        dlg.geometry("900x560")
        dlg.grab_set()

        # layout
        dlg.grid_columnconfigure((0,1), weight=1)
        dlg.grid_rowconfigure(1, weight=1)

        CTkLabel(dlg, text="Curriculum", font=("Poppins",14,"bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10,4))
        CTkLabel(dlg, text=f"AY {ay} • {sem}").grid(row=0, column=1, sticky="e", padx=12, pady=(10,4))

        left = CTkFrame(dlg, fg_color="#FFFFFF", corner_radius=10)
        right = CTkFrame(dlg, fg_color="#FFFFFF", corner_radius=10)
        left.grid(row=1, column=0, sticky="nsew", padx=(12,6), pady=8)
        right.grid(row=1, column=1, sticky="nsew", padx=(6,12), pady=8)
        right.grid_rowconfigure(1, weight=1)

        # Left: list subjects in this curriculum
        lscroll = CTkScrollableFrame(left, fg_color="#FFFFFF")
        lscroll.pack(fill="both", expand=True, padx=8, pady=8)

        with db.connect() as conn:
            subs = conn.execute(
                """
                SELECT s.id, s.code, s.title
                FROM curriculum_subjects cs
                JOIN subjects s ON s.id = cs.subject_id
                WHERE cs.curriculum_id=?
                ORDER BY s.year_level, s.code
                """,
                (curriculum_id,)
            ).fetchall()
        for sid, code, title in subs:
            b = CTkButton(lscroll, text=f"{code} — {title}", fg_color="#F3F4F6", text_color="#1F2937",
                          hover_color="#E9ECEF", command=lambda s=sid: fill_subject(s))
            b.pack(fill="x", padx=6, pady=4)

        # Right: assignment form
        form = CTkFrame(right, fg_color="#F8F9FA", corner_radius=10)
        form.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,6))
        form.grid_columnconfigure((0,1,2), weight=1)

        sub_title_var = StringVar()
        CTkEntry(form, textvariable=sub_title_var, state="disabled").grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10,6))

        CTkLabel(form, text="Faculty").grid(row=1, column=0, sticky="w", padx=10)
        fac_var = StringVar()
        with db.connect() as conn:
            facs = [r[0] for r in conn.execute("SELECT full_name FROM faculty ORDER BY full_name").fetchall()]
        if not facs: facs=["TBA"]
        fac_menu = CTkOptionMenu(form, variable=fac_var, values=facs) ; self._apply_dropdown_theme(fac_menu)
        fac_menu.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,6))

        CTkLabel(form, text="Block").grid(row=1, column=1, sticky="w", padx=10)
        blk_var = StringVar()
        with db.connect() as conn:
            blocks = [ f"{r[0]} {r[1]}" for r in conn.execute(
                "SELECT year_level, section FROM blocks ORDER BY year_level, section").fetchall()]
        if not blocks: blocks=["Merged"]
        blk_menu = CTkOptionMenu(form, variable=blk_var, values=blocks) ; self._apply_dropdown_theme(blk_menu)
        blk_menu.grid(row=2, column=1, sticky="ew", padx=10, pady=(0,6))

        CTkLabel(form, text="Expected students").grid(row=1, column=2, sticky="w", padx=10)
        exp_e = CTkEntry(form, placeholder_text="e.g., 35")
        exp_e.grid(row=2, column=2, sticky="ew", padx=10, pady=(0,6))

        def resolve_ids(fac_name: str, block_label: str, subject_id: int):
            with db.connect() as conn:
                fac_id = conn.execute(
                    "SELECT id FROM faculty WHERE full_name=?",
                    (fac_name,)
                ).fetchone()
                fac_id = fac_id[0] if fac_id else None

                blk_id = None
                if block_label and block_label != "Merged":
                    # block_label looks like "3 C" -> year, section
                    parts = block_label.split()
                    if len(parts) >= 2:
                        yl, sec = parts[0], parts[1]

                        # find the subject's program & semester first
                        prow = conn.execute(
                            "SELECT program_id, semester FROM subjects WHERE id=?",
                            (subject_id,)
                        ).fetchone()
                        if prow:
                            program_id, subj_sem = prow
                            # AY is from the dialog scope; sem is same as curriculum sem
                            blk = conn.execute("""
                                SELECT id FROM blocks
                                WHERE program_id=? AND year_level=? AND section=? 
                                    AND academic_year=? AND semester=?
                            """, (program_id, yl, sec, ay, sem)).fetchone()
                            if blk:
                                blk_id = blk[0]
            return fac_id, blk_id


        # Bottom right: list of created assignments
        list_box = CTkScrollableFrame(right, fg_color="#FFFFFF")
        list_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6,10))

        current_subject = {"id": None, "label": ""}

        def fill_subject(sid: int):
            with db.connect() as conn:
                row = conn.execute("SELECT code, title FROM subjects WHERE id=?", (sid,)).fetchone()
            if row:
                sub_title_var.set(f"{row[0]} — {row[1]}")
                current_subject["id"] = sid
                current_subject["label"] = sub_title_var.get()

        def add_assignment():
            try:
                if not current_subject["id"]:
                    messagebox.showwarning("Pick a subject", "Select a subject on the left first.", parent=dlg); return
                exp = int(exp_e.get().strip())
                fac_name = fac_var.get(); blk_label = blk_var.get(); sid = current_subject["id"]
                fac_id, blk_id = resolve_ids(fac_name, blk_label, sid)
                with db.connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO teaching_assignments (teacher_id, subject_id, block_id, academic_year, semester, expected_students)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (fac_id, sid, blk_id, ay, sem, exp)
                    )
                    conn.commit()
                CTkLabel(list_box, text=f"✓ {current_subject['label']} • {fac_name} • {blk_label} • {exp} stud.").pack(anchor="w", padx=8, pady=4)
                # reset qty
                exp_e.delete(0, "end")
            except ValueError:
                messagebox.showerror("Invalid", "Expected students must be a whole number.", parent=dlg)
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=dlg)

        CTkButton(form, text="Finish (add assignment)", fg_color="#691612", command=add_assignment).grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(6,10))

        CTkButton(dlg, text="Close", fg_color="#AC5353", command=dlg.destroy).grid(row=2, column=1, sticky="e", padx=12, pady=(0,12))

