from customtkinter import *
from PIL import Image
import db, utils
from pathlib import Path
import os
import humanize
import subprocess
import sys
import pickle
import datetime


class HomePage:
    def __init__(self, master):
        self.master = master
        self._build_ui()

    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        # --- Main background ---
        home_frame = CTkFrame(master=self.master, fg_color="#F5F5F5")
        home_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Top Navigation Bar ---
        top_nav = CTkFrame(home_frame, fg_color="#BF3131", height=70, corner_radius=10)
        top_nav.pack(fill="x", padx=10, pady=(0, 20))

        CTkLabel(
            top_nav,
            text="Dashboard",
            font=("Poppins", 22, "bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=25, pady=10)

        # === Two-column content row ===
        content_row = CTkFrame(home_frame, fg_color="transparent")
        content_row.pack(fill="both", expand=True, padx=10)

        # Left (main) column
        left_col = CTkFrame(content_row, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)

        # Right sidebar (activity logs)
        right_sidebar = CTkFrame(content_row, fg_color="#FFFFFF", corner_radius=14, width=420)
        right_sidebar.pack(side="right", fill="y", padx=(10, 0))
        right_sidebar.pack_propagate(False)

        # Build left column sections
        self._build_stats(left_col)       # KPIs row
        self._build_reports(left_col)     # Students per Faculty/Subject
        self._build_archive(left_col)     # Archive (bigger)
        self._build_table(left_col)       # Recent Evaluations

        # Build right activity sidebar
        self._build_activity_sidebar(right_sidebar)

    # ---------------- STATS ROW ----------------
    def _build_stats(self, parent):
        # Outer container for filters + KPI cards
        stats_container = CTkFrame(parent, fg_color="transparent")
        stats_container.pack(fill="x", pady=(0, 20))

        # ---------- FILTER ROW (Department scope) ----------
        filter_row = CTkFrame(stats_container, fg_color="transparent")
        filter_row.pack(fill="x", padx=10, pady=(0, 8))

        self.dept_var = StringVar()
        dept_names = []
        self._dept_name_to_id = {}

        try:
            with db.connect() as conn:
                rows = conn.execute("SELECT id, name FROM departments ORDER BY name").fetchall()
                dept_names = [r[1] for r in rows]
                self._dept_name_to_id = {r[1]: r[0] for r in rows}
        except Exception:
            dept_names = ["No Departments"]
            self._dept_name_to_id = {}

        CTkLabel(
            filter_row,
            text="Filter by Department",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            fg_color="#BF3131",
            corner_radius=8,
            padx=8,
            pady=2
        ).pack(side="left", padx=(0, 12))
        
        
        self.dept_menu = CTkOptionMenu(
            filter_row,
            variable=self.dept_var,
            values=dept_names if dept_names else ["No Departments"],
            fg_color="#BF3131",
            button_color="#691612",
            button_hover_color="#8E1616",
            text_color="#FFFFFF",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#333333",
            dropdown_hover_color="#F3D0D0",
            width=220,
        )
        self.dept_menu.pack(side="left")

        # ---------- KPI CARDS ROW ----------
        cards_frame = CTkFrame(stats_container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(4, 0))

        # Card 1 – Pending evaluations
        self.card_uncompleted = CTkFrame(
            cards_frame, fg_color="#FFFFFF", corner_radius=14, width=220, height=120
        )
        self.card_uncompleted.pack(side="left", padx=10, expand=True, fill="both")
        self.card_uncompleted.pack_propagate(False)

        CTkFrame(self.card_uncompleted, fg_color="#AC5353", height=4, corner_radius=14)\
            .pack(fill="x", side="top")

        CTkLabel(
            self.card_uncompleted,
            text="Pending Evaluations",
            font=("Poppins", 14, "bold"),
            text_color="#691612",
        ).pack(pady=(10, 5))
        self.lbl_uncompleted = CTkLabel(
            self.card_uncompleted,
            text="0",
            font=("Poppins", 28, "bold"),
            text_color="#212529",
        )
        self.lbl_uncompleted.pack()

        # Card 2 – Completed evaluations
        self.card_completed = CTkFrame(
            cards_frame, fg_color="#FFFFFF", corner_radius=14, width=220, height=120
        )
        self.card_completed.pack(side="left", padx=10, expand=True, fill="both")
        self.card_completed.pack_propagate(False)

        CTkFrame(self.card_completed, fg_color="#AC5353", height=4, corner_radius=14)\
            .pack(fill="x", side="top")

        CTkLabel(
            self.card_completed,
            text="Completed Evaluations",
            font=("Poppins", 14, "bold"),
            text_color="#691612",
        ).pack(pady=(10, 5))
        self.lbl_completed = CTkLabel(
            self.card_completed,
            text="0",
            font=("Poppins", 28, "bold"),
            text_color="#212529",
        )
        self.lbl_completed.pack()

        # ---------- init + hook up ----------
        if dept_names:
            self.dept_var.set(dept_names[0])
        else:
            self.dept_var.set("No Departments")

        def on_dept_change(choice):
            self._refresh_counts()

        self.dept_menu.configure(command=on_dept_change)
        self._refresh_counts()


    def _refresh_counts(self):
        dept_name = self.dept_var.get()
        dept_id = self._dept_name_to_id.get(dept_name)
        total_expected = 0
        completed = 0

        # Expected (sum of expected_students) for department
        try:
            if dept_id is not None:
                with db.connect() as conn:
                    row = conn.execute("""
                        SELECT COALESCE(SUM(ta.expected_students), 0)
                        FROM teaching_assignments ta
                        JOIN faculty f ON f.id = ta.teacher_id
                        WHERE f.department_id = ?
                    """, (dept_id,)).fetchone()
                    total_expected = int(row[0] or 0)
        except Exception:
            total_expected = 0

        # Completed = number of Student scans for teachers in this department
        try:
            db_path = db.get_default_db_path()
            base_dir = os.path.dirname(db_path)
            pkl_path = os.path.join(
                base_dir,
                db.PKL_FILENAME if hasattr(db, "PKL_FILENAME") else "results.pkl",
            )

            if os.path.exists(pkl_path):
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                processed_results = (
                    data["results"] if isinstance(data, dict) and "results" in data else data
                )

                teacher_names = set()
                with db.connect() as conn:
                    rows = conn.execute(
                        "SELECT full_name FROM faculty WHERE department_id = ?",
                        (dept_id,),
                    ).fetchall()
                    teacher_names = {r[0] for r in rows}

                for tname, raters in (processed_results or {}).items():
                    if tname not in teacher_names:
                        continue
                    if isinstance(raters, dict) and "Student" in raters and isinstance(
                        raters["Student"], list
                    ):
                        completed += len(raters["Student"])
        except Exception:
            completed = 0

        uncompleted = max(total_expected - completed, 0)

        self.lbl_uncompleted.configure(text=str(uncompleted))
        self.lbl_completed.configure(text=str(completed))

    # ---------------- REPORTS SECTION ----------------
    def _build_reports(self, parent):
        """List: evaluations left per Faculty / Subject (current AY/Sem scope optional)."""
        reports_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=360)
        reports_frame.pack(fill="x", padx=10, pady=(0, 20))
        reports_frame.pack_propagate(False)

        # Header
        header = CTkFrame(reports_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        CTkLabel(
            header,
            text="Evaluation Load by Subject",
            font=("Poppins", 18, "bold"),
            text_color="#691612",
        ).pack(side="left")

        # Filters row
        filter_row = CTkFrame(reports_frame, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(0, 6))

        # Department filter
        try:
            with db.connect() as conn:
                dept_rows = conn.execute("SELECT id, name FROM departments ORDER BY name").fetchall()
            dept_values = ["All Departments"] + [r[1] for r in dept_rows]
            dept_name_to_id = {r[1]: r[0] for r in dept_rows}
        except Exception:
            dept_values, dept_name_to_id = ["All Departments"], {}

        dept_var = StringVar(value=dept_values[0])
        dept_menu = CTkOptionMenu(
            filter_row,
            variable=dept_var,
            values=dept_values,
            fg_color="#BF3131",
            button_color="#691612",
            button_hover_color="#8E1616",
            text_color="#FFFFFF",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#333333",
            dropdown_hover_color="#F3D0D0",
            width=180,
        )
        dept_menu.pack(side="left", padx=(0, 10))

        # Semester filter
        sem_var = StringVar(value="1st")
        sem_menu = CTkOptionMenu(
            filter_row,
            variable=sem_var,
            values=["1st", "2nd", "Summer"],
            fg_color="#BF3131",
            button_color="#691612",
            button_hover_color="#8E1616",
            text_color="#FFFFFF",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#333333",
            dropdown_hover_color="#F3D0D0",
            width=140,
        )
        sem_menu.pack(side="left", padx=(0, 10))

        # AY input
        ay_entry = CTkEntry(
            filter_row,
            placeholder_text="AY (e.g., 2025-2026)",
            width=180,
        )
        ay_entry.pack(side="left", padx=(0, 10))

        now = datetime.datetime.now()
        y = now.year
        default_sem = "1st" if 8 <= now.month <= 12 else ("2nd" if 1 <= now.month <= 6 else "Summer")
        sem_var.set(default_sem)
        ay_entry.insert(0, f"{y}-{y+1}" if default_sem == "1st" else f"{y-1}-{y}")

        refresh_btn = CTkButton(
            filter_row,
            text="Refresh",
            fg_color="#AC5353",
            hover_color="#BF3131",
            text_color="#FFFFFF",
            corner_radius=8,
            width=120,
        )
        refresh_btn.pack(side="right")

        # Table container
        table = CTkFrame(reports_frame, fg_color="#F5F5F5", corner_radius=10)
        table.pack(fill="both", expand=True, padx=20, pady=(6, 12))

        head = CTkFrame(table, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(10, 6))
        headers = ["Subject", "Program", "AY", "Sem", "Expected (Σ)", "Completed (Σ)", "Remaining (Σ)"]
        widths = [320, 120, 110, 70, 130, 130, 110]
        for i, (h, w) in enumerate(zip(headers, widths)):
            CTkLabel(
                head,
                text=h,
                font=("Poppins", 12, "bold"),
                text_color="#495057",
                width=w,
                anchor="w",
            ).grid(row=0, column=i, sticky="w", padx=6)

        body = CTkScrollableFrame(table, fg_color="#FFFFFF", corner_radius=8)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def load_list():
            for w in body.winfo_children():
                w.destroy()

            dept_id = (
                dept_name_to_id.get(dept_var.get()) if dept_var.get() != "All Departments" else None
            )
            ay = ay_entry.get().strip()
            sem = sem_var.get().strip()

            with db.connect() as conn:
                where = []
                params = []
                base = """
                    SELECT
                        s.code              AS subj_code,
                        s.title             AS subj_title,
                        p.code              AS program_code,
                        ta.academic_year    AS ay,
                        ta.semester         AS sem,
                        SUM(COALESCE(ta.expected_students, 0)) AS expected_sum
                    FROM teaching_assignments ta
                    JOIN subjects  s ON s.id = ta.subject_id
                    JOIN programs  p ON p.id = s.program_id
                    LEFT JOIN faculty f ON f.id = ta.teacher_id
                """
                if dept_id is not None:
                    where.append("f.department_id = ?")
                    params.append(dept_id)
                if ay:
                    where.append("ta.academic_year = ?")
                    params.append(ay)
                if sem:
                    where.append("ta.semester = ?")
                    params.append(sem)

                if where:
                    base += " WHERE " + " AND ".join(where)

                base += """
                    GROUP BY s.id, ta.academic_year, ta.semester
                    ORDER BY s.code
                """

                rows = conn.execute(base, params).fetchall()

            completed_index = self._compute_completed_by_subject_totals()

            if not rows:
                CTkLabel(
                    body,
                    text="No teaching assignments found for the selected filters.",
                    font=("Poppins", 12),
                    text_color="#6B7280",
                ).pack(pady=12)
                return

            for i, (subj_code, subj_title, program_code, ayx, semx, expected_sum) in enumerate(
                rows, start=1
            ):
                code_key = ((subj_code or "").upper(), (ayx or "").strip(), (semx or "").strip())
                fallback = ((subj_code or "").upper(), None, None)
                completed = int(
                    completed_index.get(code_key, completed_index.get(fallback, 0))
                )
                left = max(int(expected_sum) - completed, 0)

                row = CTkFrame(body, fg_color="#F8F9FA" if i % 2 == 0 else "#FFFFFF")
                row.pack(fill="x", padx=6, pady=3)

                vals = [
                    f"{subj_code} — {subj_title}",
                    program_code,
                    ayx,
                    semx,
                    str(expected_sum),
                    str(completed),
                    str(left),
                ]
                for c, (txt, w) in enumerate(zip(vals, widths)):
                    CTkLabel(
                        row,
                        text=txt,
                        font=("Poppins", 12),
                        width=w,
                        anchor="w",
                        text_color="#212529",
                    ).grid(row=0, column=c, padx=6, sticky="w")

        dept_menu.configure(command=lambda *_: load_list())
        sem_menu.configure(command=lambda *_: load_list())
        refresh_btn.configure(command=load_list)

        load_list()

    # ---------------- ARCHIVE SECTION (BIGGER) ----------------
    def _build_archive(self, parent):
        """Archive section: Old Teaching Efficiency Ratings"""
        archive_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=400)
        archive_frame.pack(fill="x", padx=10, pady=(0, 20))
        archive_frame.pack_propagate(False)

        header_frame = CTkFrame(archive_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(
            header_frame,
            text="Archived TER Files",
            font=("Poppins", 18, "bold"),
            text_color="#691612",
        ).pack(side="left")

        try:
            base_dir = Path(os.path.dirname(db.get_default_db_path()))
        except Exception:
            base_dir = Path(os.path.expanduser("~")) / "Documents" / "MyWork"
        archived_root = base_dir / "Archived"

        table_area = CTkFrame(archive_frame, fg_color="#F5F5F5")
        table_area.pack(fill="both", expand=True, padx=20, pady=10)

        rows = []
        if archived_root.exists():
            for p in archived_root.rglob("*.zip"):
                dept = (
                    p.parent.parent.name if p.parent.parent != archived_root else "(Unknown Dept)"
                )
                ay = p.parent.name
                size = p.stat().st_size
                rows.append((p, dept, ay, p.name, size))

            rows.sort(key=lambda r: r[0].stat().st_mtime, reverse=True)
            rows = rows[:50]
        else:
            archived_root.mkdir(parents=True, exist_ok=True)

        header = CTkFrame(table_area, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        for i, h in enumerate(["Department", "Academic Year", "Archive File", "Size", "Open"]):
            CTkLabel(
                header,
                text=h,
                font=("Poppins", 12, "bold"),
                text_color="#495057",
            ).grid(row=0, column=i, padx=6, sticky="w")

        list_frame = CTkScrollableFrame(table_area, fg_color="#FFFFFF", corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def open_folder(path: Path):
            try:
                if sys.platform.startswith("win"):
                    os.startfile(path.parent)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path.parent])
                else:
                    subprocess.run(["xdg-open", path.parent])
            except Exception:
                pass

        if not rows:
            CTkLabel(
                list_frame,
                text="No archived files yet. Use the 'Archive this Semester' button in Results.",
                font=("Poppins", 13),
                text_color="#6C757D",
            ).pack(pady=16)
        else:
            for r, (zip_path, dept, ay, fname, size) in enumerate(rows, start=1):
                row = CTkFrame(list_frame, fg_color="#F8F9FA" if r % 2 == 0 else "#FFFFFF")
                row.pack(fill="x", padx=6, pady=3)

                CTkLabel(row, text=dept, font=("Poppins", 12)).grid(
                    row=0, column=0, padx=6, sticky="w"
                )
                CTkLabel(row, text=ay, font=("Poppins", 12)).grid(
                    row=0, column=1, padx=6, sticky="w"
                )
                CTkLabel(row, text=fname, font=("Poppins", 12)).grid(
                    row=0, column=2, padx=6, sticky="w"
                )

                try:
                    size_text = humanize.naturalsize(size, binary=True)
                except Exception:
                    size_text = f"{size/1024:.1f} KB"
                CTkLabel(row, text=size_text, font=("Poppins", 12)).grid(
                    row=0, column=3, padx=6, sticky="w"
                )

                CTkButton(
                    row,
                    text="Open",
                    width=80,
                    fg_color="#AC5353",
                    hover_color="#BF3131",
                    text_color="#FFFFFF",
                    corner_radius=8,
                    command=lambda p=zip_path: open_folder(p),
                ).grid(row=0, column=4, padx=6, pady=4)

    # ---------------- RECENT EVALUATIONS ----------------
    def _build_table(self, parent):
        table_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=300)
        table_frame.pack(fill="x", padx=10, pady=(0, 20))
        table_frame.pack_propagate(False)

        header = CTkFrame(table_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(
            header,
            text="Recent Evaluation Summaries",
            font=("Poppins", 18, "bold"),
            text_color="#691612",
        ).pack(side="left")

        CTkButton(
            header,
            text="View All",
            fg_color="#AC5353",
            hover_color="#BF3131",
            text_color="#FFFFFF",
            corner_radius=8,
            width=100,
        ).pack(side="right")

        table_area = CTkFrame(table_frame, fg_color="#F5F5F5", corner_radius=10)
        table_area.pack(fill="both", expand=True, padx=20, pady=10)

        CTkLabel(
            table_area,
            text="Recent evaluation results will appear here after processing.",
            font=("Poppins", 14),
            text_color="#6C757D",
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- ACTIVITY SIDEBAR ----------------
    def _build_activity_sidebar(self, parent):
        header = CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        CTkLabel(
            header,
            text="Activity Logs",
            font=("Poppins", 18, "bold"),
            text_color="#691612",
        ).pack(side="left")

        u = utils.get_current_user()
        dept_id = u.get("department_id")

        scope = CTkFrame(parent, fg_color="#F5F5F5", corner_radius=10)
        scope.pack(fill="x", padx=16, pady=(0, 8))
        CTkLabel(
            scope,
            text=f"Department ID: {dept_id if dept_id is not None else '—'}",
            font=("Poppins", 12),
            text_color="#6C757D",
        ).pack(side="left", padx=10, pady=8)

        list_frame = CTkScrollableFrame(parent, fg_color="#FFFFFF", corner_radius=12)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        rows = []
        if dept_id is not None:
            rows = db.fetch_activity_logs(limit=50, where="department_id = ?", params=(dept_id,))

        if not rows:
            CTkLabel(
                list_frame,
                text="No activity recorded for this department yet.",
                font=("Poppins", 13),
                text_color="#6B7280",
            ).pack(anchor="w", padx=10, pady=8)
            return

        for (ts, action, who, role, teacher, rater, fname, details_json) in rows:
            row = CTkFrame(list_frame, fg_color="#F8F9FA", corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)

            CTkLabel(
                row,
                text=f"{ts} · {action}",
                font=("Poppins", 12, "bold"),
                text_color="#212529",
            ).pack(anchor="w", padx=10, pady=(8, 2))

            who_txt = who or "—"
            role_txt = role or "—"
            teacher_txt = teacher or "—"
            rater_txt = f"[{rater}]" if rater else ""
            CTkLabel(
                row,
                text=f"{who_txt} ({role_txt}) → {teacher_txt} {rater_txt}",
                font=("Poppins", 12),
                text_color="#495057",
            ).pack(anchor="w", padx=10, pady=(0, 8))

    # ---------------- HELPERS (unchanged logic) ----------------
    def _compute_completed_by_subject(self):
        index = {}
        try:
            db_path = db.get_default_db_path()
            base_dir = os.path.dirname(db_path)
            pkl_path = os.path.join(base_dir, getattr(db, "PKL_FILENAME", "results.pkl"))
            if not os.path.exists(pkl_path):
                return index

            import pickle, re
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            processed_results = (
                data["results"] if isinstance(data, dict) and "results" in data else data
            )

            def norm_code(s):
                return (s or "").strip().upper()

            for teacher, raters in (processed_results or {}).items():
                if not isinstance(raters, dict) or "Student" not in raters:
                    continue
                for item in (raters.get("Student") or []):
                    subj_code = ""
                    result_dict = None
                    fname = ""

                    if isinstance(item, (tuple, list)) and len(item) >= 2:
                        fname, result_dict = item[0], item[1]
                    elif isinstance(item, dict):
                        result_dict = item
                    else:
                        continue

                    subj_code = norm_code(
                        (result_dict or {}).get("subject_code")
                        or (result_dict or {}).get("subject")
                    )

                    if not subj_code and isinstance(fname, str):
                        m = re.search(r"\b([A-Za-z]{2,}\s?-?\s?\d{2,3}[A-Za-z]?)\b", fname)
                        if m:
                            subj_code = norm_code(
                                m.group(1).replace(" ", "").replace("-", "")
                            )

                    if not subj_code:
                        continue

                    key = (teacher or "", subj_code)
                    index[key] = index.get(key, 0) + 1

        except Exception:
            pass

        return index

    def _compute_completed_by_subject_totals(self):
        index = {}
        try:
            import os, pickle, re

            db_path = db.get_default_db_path()
            base_dir = os.path.dirname(db_path)
            pkl_path = os.path.join(base_dir, getattr(db, "PKL_FILENAME", "results.pkl"))
            if not os.path.exists(pkl_path):
                return index

            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            processed_results = (
                data["results"] if isinstance(data, dict) and "results" in data else data
            )

            def norm(s):
                return (s or "").strip().upper()

            for _teacher, raters in (processed_results or {}).items():
                if not isinstance(raters, dict) or "Student" not in raters:
                    continue
                for item in raters.get("Student") or []:
                    result = None
                    fname = ""
                    if isinstance(item, (tuple, list)) and len(item) >= 2:
                        fname, result = item[0], item[1]
                    elif isinstance(item, dict):
                        result = item
                    else:
                        continue

                    subj_code = norm(
                        (result or {}).get("subject_code")
                        or (result or {}).get("subject")
                    )
                    if not subj_code and isinstance(fname, str):
                        m = re.search(r"\b([A-Za-z]{2,}\s?-?\s?\d{2,3}[A-Za-z]?)\b", fname)
                        if m:
                            subj_code = norm(
                                m.group(1).replace(" ", "").replace("-", "")
                            )

                    if not subj_code:
                        continue

                    ay = (result or {}).get("academic_year") or None
                    sem = (result or {}).get("semester") or None
                    key = (subj_code, (ay or None), (sem or None))
                    index[key] = index.get(key, 0) + 1

            return index
        except Exception:
            return index
