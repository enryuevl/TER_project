from customtkinter import *
from PIL import Image
import db, utils
from customtkinter import *
from PIL import Image
import os
from pathlib import Path
import db
import humanize  
import subprocess
import sys
import pickle

class HomePage:
    def __init__(self, master):
        self.master = master
        self._build_ui()

    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        # Home Frame
        home_frame = CTkFrame(master=self.master, fg_color="#F8F9FA")
        home_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Top Navigation Bar
        top_nav = CTkFrame(home_frame, fg_color="#BF3131", height=70, corner_radius=10)
        top_nav.pack(fill="x", padx=10, pady=(0, 20))
        CTkLabel(top_nav, text="Dashboard", font=("Poppins", 24, "bold"), text_color="#FFFFFF").pack(side="left", padx=25, pady=10)

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
        # container for the line (filters + cards)
        stats_frame = CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))

        # left: filters
        left = CTkFrame(stats_frame, fg_color="transparent")
        left.pack(side="left", padx=10, fill="x")

        # Department dropdown
        self.dept_var = StringVar()
        dept_names = []
        self._dept_name_to_id = {}

        try:
            with db.connect() as conn:
                rows = conn.execute("SELECT id, name FROM departments ORDER BY name").fetchall()
                dept_names = [r[1] for r in rows]
                self._dept_name_to_id = {r[1]: r[0] for r in rows}
        except Exception as e:
            dept_names = ["No Departments"]
            self._dept_name_to_id = {}

        CTkLabel(left, text="Department", font=("Poppins", 12, "bold"),
                text_color="#691612").pack(anchor="w")
        self.dept_menu = CTkOptionMenu(
            left,
            variable=self.dept_var,
            values=dept_names if dept_names else ["No Departments"],
            fg_color="#F1F3F5", button_color="#E9ECEF",
            button_hover_color="#DDE2E6", text_color="#495057",
            dropdown_fg_color="#FFFFFF", width=220
        )
        self.dept_menu.pack(pady=(2, 0), anchor="w")

        # right: stat cards
        cards_frame = CTkFrame(stats_frame, fg_color="transparent")
        cards_frame.pack(side="left", padx=10, fill="x", expand=True)

        # two KPI cards + (optional) average score you had before
        self.card_uncompleted = CTkFrame(cards_frame, fg_color="#FFFFFF", corner_radius=14, width=220, height=120)
        self.card_uncompleted.pack(side="left", padx=10, expand=True, fill="both")
        self.card_uncompleted.pack_propagate(False)

        self.card_completed = CTkFrame(cards_frame, fg_color="#FFFFFF", corner_radius=14, width=220, height=120)
        self.card_completed.pack(side="left", padx=10, expand=True, fill="both")
        self.card_completed.pack_propagate(False)

        # (Optional: keep a third KPI placeholder)
        self.card_avg = CTkFrame(cards_frame, fg_color="#FFFFFF", corner_radius=14, width=220, height=120)
        self.card_avg.pack(side="left", padx=10, expand=True, fill="both")
        self.card_avg.pack_propagate(False)

        # labels inside cards
        CTkLabel(self.card_uncompleted, text="Uncompleted evaluations",
                font=("Poppins", 14, "bold"), text_color="#691612").pack(pady=(10, 5))
        self.lbl_uncompleted = CTkLabel(self.card_uncompleted, text="0",
                                        font=("Poppins", 28, "bold"), text_color="#212529")
        self.lbl_uncompleted.pack()

        CTkLabel(self.card_completed, text="Completed evaluations",
                font=("Poppins", 14, "bold"), text_color="#691612").pack(pady=(10, 5))
        self.lbl_completed = CTkLabel(self.card_completed, text="0",
                                    font=("Poppins", 28, "bold"), text_color="#212529")
        self.lbl_completed.pack()

    

        # initialize selection and compute
        if dept_names:
            self.dept_var.set(dept_names[0])
        else:
            self.dept_var.set("No Departments")

        # recompute when department changes
        def on_dept_change(choice):
            self._refresh_counts()

        self.dept_menu.configure(command=on_dept_change)
        self._refresh_counts()

    def _refresh_counts(self):
        dept_name = self.dept_var.get()
        dept_id = self._dept_name_to_id.get(dept_name)
        total_expected = 0
        completed = 0

        # A) Get total expected (sum of expected_students) for this department
        try:
            if dept_id is not None:
                with db.connect() as conn:
                    # sum expected_students of all assignments belonging to this department
                    # (through the teacher’s department)
                    row = conn.execute("""
                        SELECT COALESCE(SUM(ta.expected_students), 0)
                        FROM teaching_assignments ta
                        JOIN faculty f ON f.id = ta.teacher_id
                        WHERE f.department_id = ?
                    """, (dept_id,)).fetchone()
                    total_expected = int(row[0] or 0)
        except Exception as e:
            total_expected = 0

        # B) Count completed = number of Student scans saved for teachers in this department
        try:
            # results.pkl lives next to the DB (same folder)
            db_path = db.get_default_db_path()
            base_dir = os.path.dirname(db_path)
            pkl_path = os.path.join(base_dir, db.PKL_FILENAME if hasattr(db, "PKL_FILENAME") else "results.pkl")

            if os.path.exists(pkl_path):
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                processed_results = data["results"] if isinstance(data, dict) and "results" in data else data

                # Build a set of teacher names in this department to filter processed_results
                teacher_names = set()
                with db.connect() as conn:
                    rows = conn.execute("""
                        SELECT full_name FROM faculty WHERE department_id = ?
                    """, (dept_id,)).fetchall()
                    teacher_names = {r[0] for r in rows}

                # Walk the results dict structure:
                # { teacher_name: { rater_type: [(file, result_dict), ...], ... }, ... }
                for tname, raters in (processed_results or {}).items():
                    if tname not in teacher_names:
                        continue
                    # only count Student scans as completed evaluations
                    if isinstance(raters, dict) and "Student" in raters and isinstance(raters["Student"], list):
                        completed += len(raters["Student"])
        except Exception as e:
            completed = 0

        uncompleted = max(total_expected - completed, 0)

        # Update the labels
        self.lbl_uncompleted.configure(text=str(uncompleted))
        self.lbl_completed.configure(text=str(completed))
        

    
    # ---------------- REPORTS SECTION ----------------
    def _build_reports(self, parent):
        """Reports section: Number of Students per Faculty/Subject"""
        reports_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=300)
        reports_frame.pack(fill="x", padx=10, pady=(0, 20))
        reports_frame.pack_propagate(False)

        # Header
        header = CTkFrame(reports_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header, text="Students per Faculty / Subject", font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        # Filters
        filter_frame = CTkFrame(reports_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        dept_menu = CTkOptionMenu(filter_frame,
                                  values=["All Departments"],
                                  fg_color="#F1F3F5", button_color="#E9ECEF",
                                  button_hover_color="#DDE2E6", text_color="#495057",
                                  dropdown_fg_color="#FFFFFF", width=150)
        dept_menu.pack(side="left", padx=(0, 10))
        dept_menu.set("All Departments")

        sem_menu = CTkOptionMenu(filter_frame,
                                 values=["1st Semester", "2nd Semester"],
                                 fg_color="#F1F3F5", button_color="#E9ECEF",
                                 button_hover_color="#DDE2E6", text_color="#495057",
                                 dropdown_fg_color="#FFFFFF", width=150)
        sem_menu.pack(side="left", padx=(0, 10))
        sem_menu.set("1st Semester")

        CTkButton(filter_frame, text="Generate Report", fg_color="#691612", hover_color="#8B1D18",
                  corner_radius=6, width=150).pack(side="right")

        # Chart Placeholder
        chart_area = CTkFrame(reports_frame, fg_color="transparent")
        chart_area.pack(fill="both", expand=True, padx=20, pady=10)
        CTkLabel(chart_area, text="Bar Chart of Students/Faculty will render here",
                 font=("Poppins", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- ARCHIVE SECTION (BIGGER) ----------------
    def _build_archive(self, parent):
        """Archive section: Old Teaching Efficiency Ratings"""
        archive_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=400)
        archive_frame.pack(fill="x", padx=10, pady=(0, 20))
        archive_frame.pack_propagate(False)

        # Header
        header_frame = CTkFrame(archive_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header_frame, text="Archive - Teaching Efficiency Ratings",
                font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        # Resolve MyWork/Archived root
        try:
            base_dir = Path(os.path.dirname(db.get_default_db_path()))
        except Exception:
            base_dir = Path(os.path.expanduser("~")) / "Documents" / "MyWork"
        archived_root = base_dir / "Archived"

        # Table container
        table_area = CTkFrame(archive_frame, fg_color="#F8F9FA")
        table_area.pack(fill="both", expand=True, padx=20, pady=10)

        # Build a lightweight list of recent ZIPs
        rows = []
        if archived_root.exists():
            for p in archived_root.rglob("*.zip"):
                # Expect path .../Archived/<Dept>/<AY>/<file>.zip
                dept = p.parent.parent.name if p.parent.parent != archived_root else "(Unknown Dept)"
                ay = p.parent.name
                size = p.stat().st_size
                rows.append((p, dept, ay, p.name, size))

            # newest first
            rows.sort(key=lambda r: r[0].stat().st_mtime, reverse=True)
            rows = rows[:50]  # show top 50
        else:
            archived_root.mkdir(parents=True, exist_ok=True)

        # Header row
        header = CTkFrame(table_area, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        for i, h in enumerate(["Department", "Academic Year", "Archive File", "Size", "Open Folder"]):
            CTkLabel(header, text=h, font=("Poppins", 12, "bold"), text_color="#495057").grid(row=0, column=i, padx=6, sticky="w")

        # Scrollable list
        list_frame = CTkScrollableFrame(table_area, fg_color="#FFFFFF", corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def open_folder(path: Path):
            try:
                if sys.platform.startswith("win"):
                    os.startfile(path.parent)  # open in Explorer
                elif sys.platform == "darwin":
                    subprocess.run(["open", path.parent])
                else:
                    subprocess.run(["xdg-open", path.parent])
            except Exception:
                pass

        if not rows:
            CTkLabel(list_frame, text="No archived files yet. Use the 'Archive this Semester' button in Results.",
                    font=("Arial", 14), text_color="#6C757D").pack(pady=16)
        else:
            for r, (zip_path, dept, ay, fname, size) in enumerate(rows, start=1):
                row = CTkFrame(list_frame, fg_color="#F8F9FA" if r % 2 == 0 else "#FFFFFF")
                row.pack(fill="x", padx=6, pady=3)

                CTkLabel(row, text=dept,  font=("Poppins", 12)).grid(row=0, column=0, padx=6, sticky="w")
                CTkLabel(row, text=ay,    font=("Poppins", 12)).grid(row=0, column=1, padx=6, sticky="w")
                CTkLabel(row, text=fname, font=("Poppins", 12)).grid(row=0, column=2, padx=6, sticky="w")

                try:
                    size_text = humanize.naturalsize(size, binary=True)
                except Exception:
                    size_text = f"{size/1024:.1f} KB"
                CTkLabel(row, text=size_text, font=("Poppins", 12)).grid(row=0, column=3, padx=6, sticky="w")

                CTkButton(row, text="Open", width=80, fg_color="#691612", hover_color="#8B1D18",
                        command=lambda p=zip_path: open_folder(p)).grid(row=0, column=4, padx=6, pady=4)


    # ---------------- RECENT EVALUATIONS ----------------
    def _build_table(self, parent):
        table_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=300)
        table_frame.pack(fill="x", padx=10, pady=(0, 20))
        table_frame.pack_propagate(False)

        header = CTkFrame(table_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header, text="Recent Evaluation Results", font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        CTkButton(header, text="View All", fg_color="#691612", hover_color="#8B1D18",
                  corner_radius=6, width=100).pack(side="right")

        table_area = CTkFrame(table_frame, fg_color="#F8F9FA")
        table_area.pack(fill="both", expand=True, padx=20, pady=10)
        CTkLabel(table_area, text="Table of evaluation results will be displayed here",
                 font=("Poppins", 14), text_color="#6C757D").place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- ACTIVITY SIDEBAR ----------------
    def _build_activity_sidebar(self, parent):
        # Header
        header = CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        CTkLabel(header, text="Activity Logs", font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        # Current department scope
        u = utils.get_current_user()
        dept_id = u.get("department_id")

        # Small filter row (read-only display of scope)
        scope = CTkFrame(parent, fg_color="#F8F9FA", corner_radius=10)
        scope.pack(fill="x", padx=16, pady=(0, 8))
        CTkLabel(scope, text=f"Department ID: {dept_id if dept_id is not None else '—'}",
                font=("Poppins", 12), text_color="#6C757D").pack(side="left", padx=10, pady=8)

        # Scrollable list
        list_frame = CTkScrollableFrame(parent, fg_color="#FFFFFF", corner_radius=12)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        # Fetch department-scoped logs (latest first)
        rows = []
        if dept_id is not None:
            rows = db.fetch_activity_logs(limit=50, where="department_id = ?", params=(dept_id,))
        else:
            # If no department set, show nothing (or you can fall back to all by removing this else)
            rows = []

        if not rows:
            CTkLabel(list_frame, text="No activity for this department yet.",
                    font=("Poppins", 13), text_color="#6B7280").pack(anchor="w", padx=10, pady=8)
            return

        # Render slim entries
        for (ts, action, who, role, teacher, rater, fname, details_json) in rows:
            row = CTkFrame(list_frame, fg_color="#F8F9FA", corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)

            # First line: timestamp + action
            CTkLabel(row, text=f"{ts} · {action}",
                    font=("Poppins", 12, "bold"), text_color="#212529").pack(anchor="w", padx=10, pady=(8, 2))

            # Second line: who (role) → teacher [rater]
            who_txt = who or "—"
            role_txt = role or "—"
            teacher_txt = teacher or "—"
            rater_txt = f"[{rater}]" if rater else ""
            CTkLabel(row, text=f"{who_txt} ({role_txt}) → {teacher_txt} {rater_txt}",
                    font=("Poppins", 12), text_color="#495057").pack(anchor="w", padx=10, pady=(0, 8))
