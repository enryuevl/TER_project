from customtkinter import *
from CTkTable import *
from tkinter import filedialog, messagebox
import pandas as pd
import os
from tksheet import Sheet   # make sure you have tksheet installed
import pickle
from tkinter import filedialog
import openpyxl
import win32com.client as win32
from datetime import datetime
from openpyxl import load_workbook
from openpyxl import Workbook


class ResultsPage:
    def __init__(self, master, processed_results):
        self.master = master
        self.processed_results = processed_results
        self.current_teacher = None
        self.tab_buttons = []
        
        self.load_results()
        print(self.processed_results)
        self._build_ui()
        

# ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.content_frame = CTkFrame(self.master, fg_color="#F3F4F6")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        layout = CTkFrame(self.content_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=10, pady=10)
        layout.grid_rowconfigure(0, weight=1)
        layout.grid_rowconfigure(1, weight=3)
        layout.grid_rowconfigure(2, weight=1)
        
            
        # --- Table frame (create FIRST so it exists) ---
        self.table_frame = CTkFrame(layout, fg_color="transparent")
        self.table_frame.grid(row=1, column=0,sticky="nsew", padx=10, pady=10)

        # --- Teacher buttons ---
        self._build_tabs(layout)

        # --- Controls ---
        self.controls_frame = CTkFrame(layout, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self._build_controls(self.controls_frame)

# ---------------- Table Building ---------------- #
    def _build_tabs(self, parent):
        tab_frame = CTkFrame(parent, fg_color="transparent")
        tab_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.tab_buttons = []
        first_teacher = None

        for teacher_name in self.processed_results.keys():
            if first_teacher is None:
                first_teacher = teacher_name

            btn = CTkButton(
                tab_frame,
                text=teacher_name,
                command=lambda t=teacher_name: self._on_teacher_selected(parent, t),
                fg_color="#DC2626",
                hover_color="#B91C1C",
                text_color="#FFFFFF",
                font=("Roboto", 14, "bold"),
                corner_radius=5
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons.append(btn)

        if first_teacher:
            self._on_teacher_selected(parent, first_teacher)


    def _build_table(self, parent, teacher_name, rater_type=None):
        # Clear previous table
        for widget in parent.winfo_children():
            widget.destroy()

        # Get data for teacher + rater
        teacher_data = self.processed_results.get(teacher_name, {})
        if isinstance(teacher_data, list):  # fallback for old format
            teacher_data = {"Unknown": teacher_data}

        if not rater_type:
            rater_type = list(teacher_data.keys())[0]  # default to first rater

        rater_data = teacher_data.get(rater_type, [])
        if not rater_data:
            CTkLabel(parent, text=f"No results for {rater_type}",
                    font=("Roboto", 16), text_color="#374151").pack(pady=20)
            return

        # ---------- Build headers ----------
        headers = ["Section/Row"]
        for idx, (filename, result, *_) in enumerate(rater_data):
            headers.append(f"Doc {idx+1}")

        table_data = [headers]

        # ---------- Collect all section-row keys ----------
        all_rows = set()
        for _, result, *_ in rater_data:
            for section, rows in result.items():
                for rownum in rows.keys():
                    all_rows.add(f"{section} R{rownum}")
        all_rows = sorted(all_rows)

        # ---------- Fill rows ----------
        for row_key in all_rows:
            row_data = [row_key]
            for _, result, *_ in rater_data:
                section, rownum = row_key.split(" R")
                rownum = int(rownum)
                score = result.get(section, {}).get(rownum, "")
                row_data.append(score if score != "" else 0)
            table_data.append(row_data)

        # ---------- Add totals ----------
        totals = ["Total"]
        for _, result, *_ in rater_data:
            total_score = sum(sum(rows.values()) for rows in result.values())
            totals.append(total_score)
        table_data.append(totals)

        # ---------- Create CTkTable ----------
        table = CTkTable(
            parent,
            row=len(table_data),
            column=len(table_data[0]),
            values=table_data,
            header_color="#DC2626",
            hover_color="#FECACA",
            colors=["#FFFFFF", "#F9FAFB"],
            color_phase="horizontal",
            corner_radius=10,
            font=("Roboto", 12),
            text_color="#1F2937",
            justify="center"
        )
        table.pack(expand=True, fill="both", padx=10, pady=10)

        return table

# ---------------- Controls ---------------- #
    def _build_controls(self, parent):
        control_frame = CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)


        # New Summary View Button
        summary_btn = CTkButton(
            control_frame,
            text="View Summary",
            command=self.show_summary_window,
            fg_color="#DC2626",  # Red primary color
            hover_color="#B91C1C",  # Darker red on hover
            text_color="#FFFFFF",
            font=("Roboto", 14),
            corner_radius=5
        )
        summary_btn.pack(side="left", padx=5)
        
        CTkLabel(
            control_frame, text="Select Rater Type",
            font=('Montserrat', 16, 'bold'),
            text_color="#334155"
        ).pack(pady=10, padx=15, anchor="w")

        self.rater_var = StringVar(value="Student")

        self.rater_dropdown = CTkOptionMenu(
            control_frame,
            variable=self.rater_var,
            values=["Student", "Peer", "Self", "Dean"],
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14),
            width=250, height=35,
            command=lambda choice: self._on_rater_selected(choice)  # <— added callback
        )
        self.rater_dropdown.pack(padx=15, pady=10)

# ---------------- Summary Window ---------------- #
    def show_summary_window(self):
        if not self.current_teacher:
            messagebox.showwarning("No Teacher", "Please select a teacher first.")
            return

        # Open popup first so entry_widgets exist
        self._open_summary_popup()

        # rater types → entry key → weight %
        mapping = {
            "Student": ("student_rater", 25),
            "Peer": ("peer_rater", 15),
            "Dean": ("dean_rater", 15)
        }

        for rater_key, (entry_key, weight) in mapping.items():
            averages = self.calculate_row_averages(self.current_teacher, rater_key)
            grand_total = sum(averages.values()) if averages else 0

            # Rating
            self.set_value(entry_key, f"{grand_total:.2f}", field="rating")

            # Equivalent = Rating ÷ 10
            rating_equiv = grand_total / 10 if grand_total else 0
            self.set_value(entry_key, f"{rating_equiv:.2f}", field="equivalent")

            # Point Score = Equivalent × Weight%
            point_score = rating_equiv * (weight / 100)
            self.set_value(entry_key, f"{point_score:.2f}", field="point")

    def update_overall_point_score(self):
        """Sum all point scores and update the Overall Point Score entry."""
        total = 0.0
        for key, widgets in self.entry_widgets.items():
            if isinstance(widgets, dict) and "point" in widgets:
                val = widgets["point"].get().strip()
                try:
                    total += float(val)
                except ValueError:
                    pass  # skip empty/invalid entries

        # Update the Overall Point Score entry
        if "overall_point" in self.entry_widgets:
            e = self.entry_widgets["overall_point"]
            e.delete(0, "end")
            e.insert(0, f"{total:.2f}")

        # Compute Equivalent Numerical Rating
        eq_num = self.compute_equivalent_numerical(total)
        if "eq_numerical" in self.entry_widgets:
            e = self.entry_widgets["eq_numerical"]
            e.delete(0, "end")
            e.insert(0, str(eq_num))
        
        eq_adj = self.compute_adjective_rating(eq_num)
        if "eq_adjective" in self.entry_widgets:
            e = self.entry_widgets["eq_adjective"]
            e.delete(0, "end")
            e.insert(0, eq_adj)

    def _build_dataframe(self, teacher_name):
        """
        Build a Pandas DataFrame from the calculated section totals.
        """
        data = self._calculate_section_totals(teacher_name)
        if not data:
            return None

        return pd.DataFrame(data, columns=["Row", "Average Score", "Section Total"])
    
    # ---------------- Summary Popup ---------------- #
    
    def _open_summary_popup(self):
        # Get screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        # Calculate position to center the window
        x = (screen_width - 1280) // 2
        y = (screen_height - 720) // 2

        win = CTkToplevel(self.master)
        win.title(f"Teaching Efficiency Rating - {self.current_teacher}")
        win.geometry(f"1280x720+{x}+{y}")
        win.configure(fg_color="#F3F4F6")  # Light background

        win.transient(self.master)
        win.grab_set()
        win.focus_force()
        win.lift()

        # Scrollable frame
        scroll_frame = CTkScrollableFrame(
            win, fg_color="#FFFFFF",
            label_font=("Roboto", 14, "bold"),
            label_text_color="#DC2626"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # storage for all entry references
        self.entry_widgets = {}

        # Helper for consistent rows
        def add_row(parent, row_idx, label, percent="", key=None):
            """Full row: Rating, Equivalent, Point Score (used in Performance)."""
            CTkLabel(parent, text=label, font=("Roboto", 12),
                    text_color="#1F2937", anchor="w").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

            rating_entry = CTkEntry(parent, width=120, font=("Roboto", 12))
            rating_entry.grid(row=row_idx, column=1, padx=5, pady=2)

            eq_entry = CTkEntry(parent, width=150, font=("Roboto", 12))
            eq_entry.grid(row=row_idx, column=2, padx=5, pady=2)

            CTkLabel(parent, text=percent, font=("Roboto", 12),
                    text_color="#1F2937", anchor="center").grid(row=row_idx, column=3, padx=5, pady=2)

            point_entry = CTkEntry(parent, width=120, font=("Roboto", 12))
            point_entry.grid(row=row_idx, column=4, padx=5, pady=2)

            if key:
                self.entry_widgets[key] = {
                    "rating": rating_entry,
                    "equivalent": eq_entry,
                    "point": point_entry,
                }

        def add_behavior_row(parent, row_idx, label, percent="", key=None):
            """Behavior row: Equivalent only (Dean fills manually)."""
            CTkLabel(parent, text=label, font=("Roboto", 12),
                    text_color="#1F2937", anchor="w").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

            eq_entry = CTkEntry(parent, width=150, font=("Roboto", 12))
            eq_entry.grid(row=row_idx, column=2, padx=5, pady=2)

            CTkLabel(parent, text=percent, font=("Roboto", 12),
                    text_color="#1F2937", anchor="center").grid(row=row_idx, column=3, padx=5, pady=2)

            point_entry = CTkEntry(parent, width=120, font=("Roboto", 12))
            point_entry.grid(row=row_idx, column=4, padx=5, pady=2)

            if key:
                self.entry_widgets[key] = {
                    "equivalent": eq_entry,
                    "point": point_entry,
                    "weight": float(percent.strip('%')) if percent else 0.0,
                }

                # 🔑 bind so updating equivalent auto-updates point
                def update_point(event=None, entry_key=key):
                    val = eq_entry.get().strip()
                    try:
                        num = float(val)
                        weight = self.entry_widgets[entry_key]["weight"] / 100
                        point = num * weight
                        point_entry.delete(0, "end")
                        point_entry.insert(0, f"{point:.2f}")
                    except ValueError:
                        point_entry.delete(0, "end")
                    
                    self.update_overall_point_score()

                eq_entry.bind("<KeyRelease>", update_point)



        #  Header
        CTkLabel(scroll_frame, text="TEACHING EFFICIENCY RATING (TER) SCALE FORM",
                font=("Roboto", 16, "bold"), text_color="#FFFFFF",
                fg_color="#DC2626", corner_radius=6).pack(fill="x", pady=5)

        # === Instructor Info ===
        info_frame = CTkFrame(scroll_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=5)
        for lbl in ["Instructor:", "College:", "Rating Period:", "Department:"]:
            CTkLabel(info_frame, text=lbl, font=("Roboto", 12),
                    text_color="#1F2937").pack(side="left", padx=5)
            e = CTkEntry(info_frame, width=150, font=("Roboto", 12))
            e.pack(side="left", padx=10)
            # store by label text
            self.entry_widgets[lbl.strip(":").lower()] = e

        # === Performance Section ===
        perf_frame = CTkFrame(scroll_frame, fg_color="transparent")
        perf_frame.pack(fill="x", pady=10)

        CTkLabel(perf_frame, text="I. PERFORMANCE (70%)",
                font=("Roboto", 14, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))

        headers = ["", "RATING", "RATING EQUIVALENT", "RATING %", "POINT SCORE"]
        for i, h in enumerate(headers):
            CTkLabel(perf_frame, text=h, font=("Roboto", 12, "bold"),
                    text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

        # Rows
        CTkLabel(perf_frame, text="1. Instruction (55%)",
                font=("Roboto", 12, "bold"), text_color="#DC2626")\
            .grid(row=2, column=0, sticky="w", pady=(0, 3))

        add_row(perf_frame, 3, "a) Student as Rater", "25%", key="student_rater")
        add_row(perf_frame, 4, "b) Peer as Rater", "15%", key="peer_rater")
        add_row(perf_frame, 5, "c) Dean as Rater", "15%", key="dean_rater")

        add_behavior_row(perf_frame, 6, "2. Research", "5%", key="research")
        add_behavior_row(perf_frame, 7, "3. Extension", "5%", key="extension")
        add_behavior_row(perf_frame, 8, "4. Production", "5%", key="production")

        # === Behavior Section ===
        behav_frame = CTkFrame(scroll_frame, fg_color="transparent")
        behav_frame.pack(fill="x", pady=10)

        CTkLabel(behav_frame, text="II. BEHAVIOR (30%)",
                font=("Roboto", 14, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))

        for i, h in enumerate(headers):
            CTkLabel(behav_frame, text=h, font=("Roboto", 12, "bold"),
                    text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

        add_behavior_row(behav_frame, 2, "1. Courtesy", "7.5%", key="courtesy")
        add_behavior_row(behav_frame, 3, "2. Human Relations", "7.5%", key="human_relations")
        add_behavior_row(behav_frame, 4, "3. Punctuality and Attendance", "7.5%", key="punctuality")
        add_behavior_row(behav_frame, 5, "4. Initiative", "7.5%", key="initiative")
        add_behavior_row(behav_frame, 6, "5. Leadership (Supervisors only)", "5%", key="leadership")
        add_behavior_row(behav_frame, 7, "6. Stress Tolerance (Supervisors only)", "5%", key="stress_tolerance")

        
        

        # === Plus Factor ===
        plus_frame = CTkFrame(scroll_frame, fg_color="transparent")
        plus_frame.pack(fill="x", pady=10)
        CTkLabel(plus_frame, text="PLUS FACTOR (not to exceed one (1) credit point)",
                font=("Roboto", 12, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))
        e_plus = CTkEntry(plus_frame, width=120, font=("Roboto", 12))
        e_plus.grid(row=0, column=1, padx=5, pady=2)
        self.entry_widgets["plus_factor"] = e_plus

        # === Summary Ratings ===
        summary_frame = CTkFrame(scroll_frame, fg_color="transparent")
        summary_frame.pack(fill="x", pady=10)

        labels = [
            ("Overall Point Score", "overall_point"),
            ("Equivalent Numerical Rating", "eq_numerical"),
            ("Equivalent Adjective Rating", "eq_adjective"),
        ]
        for idx, (text, key) in enumerate(labels):
            CTkLabel(summary_frame, text=text, font=("Roboto", 12, "bold"),
                    text_color="#1F2937").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
            e = CTkEntry(summary_frame, width=120, font=("Roboto", 12))
            e.grid(row=idx, column=1, padx=5, pady=2)
            self.entry_widgets[key] = e

        # === Comments Section ===
        comments_frame = CTkFrame(scroll_frame, fg_color="transparent")
        comments_frame.pack(fill="x", pady=10)

        CTkLabel(comments_frame, text="EMPLOYEE'S COMMENTS/REMARKS",
                font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        self.entry_widgets["employee_comments"] = CTkTextbox(
            comments_frame, height=50, width=900, font=("Roboto", 12))
        self.entry_widgets["employee_comments"].pack(pady=5)

        CTkLabel(comments_frame, text="RATER'S COMMENTS/REMARKS",
                font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        self.entry_widgets["rater_comments"] = CTkTextbox(
            comments_frame, height=50, width=900, font=("Roboto", 12))
        self.entry_widgets["rater_comments"].pack(pady=5)
        
                # === Save Button ===
        save_frame = CTkFrame(scroll_frame, fg_color="transparent")
        save_frame.pack(fill="x", pady=20)

        save_btn = CTkButton(
            save_frame,
            text="💾 Save Summary",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="#FFFFFF",
            font=("Roboto", 14, "bold"),
            corner_radius=8,
            command=lambda: self.export_full_summary()
        )
        save_btn.pack(pady=10)
        
        # --- Auto-fill Instructor and Department ---
        if "instructor" in self.entry_widgets:
            self.entry_widgets["instructor"].delete(0, "end")
            self.entry_widgets["instructor"].insert(0, self.current_teacher)

        # fetch department from DB
        dept = self.get_department_for_teacher(self.current_teacher)
        if dept and "department" in self.entry_widgets:
            self.entry_widgets["department"].delete(0, "end")
            self.entry_widgets["department"].insert(0, dept)

    def get_department_for_teacher(self, teacher_name: str) -> str:
        """Lookup department name for a teacher in the database using full_name."""
        import db

        try:
            conn = db.connect()
            cur = conn.cursor()

            query = """
            SELECT d.name
            FROM faculty f
            JOIN departments d ON f.department_id = d.id
            WHERE f.full_name = ?
            """
            cur.execute(query, (teacher_name,))
            row = cur.fetchone()
            conn.close()

            return row[0] if row else ""
        except Exception as e:
            print(f"❌ DB lookup failed: {e}")
            return ""

    

    # ---------------- Data Persistence ---------------- #
    def load_results(self, path="results.pkl"):
        """Load processed_results dict from a pickle file (teacher → rater → docs)."""
        if not os.path.exists(path):
            print("⚠️ No saved results found.")
            self.processed_results = {}
            return {}

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            # Make sure we only extract the nested results
            if isinstance(data, dict) and "results" in data:
                self.processed_results = data["results"]
            else:
                # legacy format fallback: wrap flat structure into "Unknown" rater
                self.processed_results = {}
                for teacher, docs in data.items():
                    self.processed_results[teacher] = {"Unknown": docs}
        
            return self.processed_results
        
        
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            self.processed_results = {}
            return {}


    # ---------------- Calculations ---------------- #
    def compute_equivalent_numerical(self, overall_score: float) -> int:
        """Convert overall point score to numerical rating using Excel-like rules."""
        if overall_score >= 9.3:
            return 10
        elif overall_score >= 7.5:
            return 8
        elif overall_score >= 5:
            return 6
        elif overall_score >= 3:
            return 4
        else:
            return 2

    def compute_adjective_rating(self, eq_num: int) -> str:
        """Convert numerical rating into adjective equivalent."""
        mapping = {
            10: "Outstanding (O)",
            8: "Very Satisfactory (VS)",
            6: "Satisfactory (S)",
            4: "Fair (F)",
            2: "Unsatisfactory (US)"
        }
        return mapping.get(eq_num, "")

    def calculate_row_averages(self, teacher_name, rater_type=None):
        """Compute averages for a teacher and selected rater type."""
        teacher_data = self.processed_results.get(teacher_name, {})

        # Handle old flat list format
        if isinstance(teacher_data, list):
            teacher_data = {"Unknown": teacher_data}

        # pick selected rater or default
        if not rater_type:
            if hasattr(self, "rater_var"):
                rater_type = self.rater_var.get()
            else:
                rater_type = next(iter(teacher_data.keys()), None)

        if not rater_type or rater_type not in teacher_data:
            return {}

        row_scores = {}

        # Collect all rows for all documents under this rater
        for _, result, *_ in teacher_data[rater_type]:
            for section, rows in result.items():
                for rownum, score in rows.items():
                    row_key = f"{section} R{rownum}"
                    row_scores.setdefault(row_key, []).append(score)

        # Compute averages
        averages = {}
        for row_key, scores in row_scores.items():
            if scores:
                averages[row_key] = sum(scores) / len(scores)

        return averages  # dict of row_key -> average score
 
    def _calculate_section_totals(self, teacher_name):
        averages = self.calculate_row_averages(teacher_name)
        if not averages:
            return None

        # Group averages by section
        section_rows = {}
        for row_key, avg in averages.items():
            section = " ".join(row_key.split()[:2])  # e.g. "Section 1"
            section_rows.setdefault(section, []).append((row_key, avg))

        # Build structured data (list of tuples)
        data = []
        section_totals = []
        for section, rows in section_rows.items():
            section_total = sum(avg for _, avg in rows)
            section_totals.append(section_total)

            for i, (row_key, avg) in enumerate(rows):
                if i == 0:
                    data.append((row_key, round(avg, 2), round(section_total, 2)))
                else:
                    data.append((row_key, round(avg, 2), ""))

        # Add grand total row
        grand_total = sum(section_totals)
        data.append(("Grand Total", "", round(grand_total, 2)))
        print(data)
        return data
    
    # ---------------- Callbacks ---------------- #
    def _on_teacher_selected(self, parent, teacher_name):
        self.current_teacher = teacher_name

        # Clear only the table frame
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self._build_table(self.table_frame, teacher_name)

    def _on_rater_selected(self, rater_type):
        if not hasattr(self, "current_teacher") or not self.current_teacher:
            return  # no teacher selected yet

        # Rebuild the table for the selected teacher & rater
        self._build_table(self.table_frame, self.current_teacher, rater_type)

    def set_value(self, key, value, field=None):
        """
        Set a value into an entry or textbox inside entry_widgets.

        key   : the key you stored in self.entry_widgets (e.g. "student_rater", "eq_numerical")
        value : the string to insert
        field : optional, if the widget is a row dict ("rating", "equivalent", "point")
        """
        if key not in self.entry_widgets:
            print(f"⚠️ No entry found for key: {key}")
            return

        widget = self.entry_widgets[key]

        # Row dicts (rating/equivalent/point)
        if isinstance(widget, dict):
            if field not in widget:
                print(f"⚠️ No field '{field}' in key '{key}'")
                return
            widget = widget[field]

        # Textboxes use line/char indices
        if hasattr(widget, "insert") and hasattr(widget, "delete"):
            # clear then insert
            if "Textbox" in widget.__class__.__name__:
                widget.delete("1.0", "end")
                widget.insert("1.0", value)
            else:
                widget.delete(0, "end")
                widget.insert(0, value)


    # ---------------- summary helpers ---------------- #
    def _write_manual_results(self, ws):
        mapping = {
            "instructor": "D9",
            "college": "D10",
            "rating period": "J9",
            "department": "J10",

            "research":      {"equivalent": "F19", "point": "L19"},
            "extension":     {"equivalent": "F20", "point": "L20"},
            "productivity":  {"equivalent": "F21", "point": "L21"},

            "courtesy":         {"equivalent": "H25", "point": "L25"},
            "human_relations":  {"equivalent": "H26", "point": "L26"},
            "punctuality":      {"equivalent": "H27", "point": "L27"},
            "initiative":       {"equivalent": "H28", "point": "L28"},
            "leadership":       {"equivalent": "H29", "point": "L29"},
            "stress_tolerance": {"equivalent": "H30", "point": "L30"},

            
        }

        for key, widget in self.entry_widgets.items():
            if key not in mapping:
                continue

            target = mapping[key]
            if isinstance(widget, dict):
                for sub_key, entry in widget.items():
                    if sub_key in target:
                        ws[target[sub_key]] = entry.get().strip()
            elif hasattr(widget, "get"):
                if widget.__class__.__name__ == "CTkTextbox":
                    ws[target] = widget.get("1.0", "end").strip()
                else:
                    ws[target] = widget.get().strip()
                    
    def _write_student_scores(self, ws):
        student_docs = self.processed_results.get(self.current_teacher, {}).get("Student", [])
        if not student_docs:
            print(f"⚠️ No Student results for {self.current_teacher}")
            return

        row_maps = {
            "Section 1": {1: 12, 2: 13, 3: 14, 4: 15, 5: 16},
            "Section 2": {1: 18, 2: 19, 3: 20, 4: 21, 5: 22},
            "Section 3": {1: 24, 2: 25, 3: 26, 4: 27, 5: 28},
            "Section 4": {1: 30, 2: 31, 3: 32, 4: 33, 5: 34},
        }

        start_col = 6  # column F

        for doc_idx, (_, result) in enumerate(student_docs):
            col = start_col + doc_idx
            for section, row_map in row_maps.items():
                for rownum, score in result.get(section, {}).items():
                    excel_row = row_map.get(rownum)
                    if excel_row:
                        ws.cell(row=excel_row, column=col, value=score)

    def _write_peer_scores(self, ws):
        peer_docs = self.processed_results.get(self.current_teacher, {}).get("Peer", [])
        if not peer_docs:
            print(f"⚠️ No Peer results for {self.current_teacher}")
            return

        # Row mappings for each Section (Peer rater)
        row_maps = {
            "Section 1": {1: 12, 2: 13, 3: 14, 4: 15, 5: 16},
            "Section 2": {1: 18, 2: 19, 3: 20, 4: 21, 5: 22},
            "Section 3": {1: 24, 2: 25, 3: 26, 4: 27, 5: 28},
            "Section 4": {1: 30, 2: 31, 3: 32, 4: 33, 5: 34},
        }

        # Starting column index (MG = 345 in Excel)
        start_col = 345

        for doc_idx, (_, result) in enumerate(peer_docs):
            col = start_col + doc_idx  # shift one column per document (MG, MH, MI … MU)
            for section, row_map in row_maps.items():
                for rownum, score in result.get(section, {}).items():
                    excel_row = row_map.get(rownum)
                    if excel_row:
                        ws.cell(row=excel_row, column=col, value=score)

    def _write_self_scores(self, ws):
        self_docs = self.processed_results.get(self.current_teacher, {}).get("Self", [])
        if not self_docs:
            print(f"⚠️ No Self results for {self.current_teacher}")
            return

        # We only accept 1 self evaluation → take the first one
        _, result = self_docs[0]

        # Row mappings for each Section (Self rater)
        row_maps = {
            "Section 1": {1: 46, 2: 47, 3: 48, 4: 49, 5: 50},
            "Section 2": {1: 52, 2: 53, 3: 54, 4: 55, 5: 56},
            "Section 3": {1: 58, 2: 59, 3: 60, 4: 61, 5: 62},
            "Section 4": {1: 64, 2: 65, 3: 66, 4: 67, 5: 68},
        }

        # Fixed column index for column C = 3
        col = 3

        for section, row_map in row_maps.items():
            for rownum, score in result.get(section, {}).items():
                excel_row = row_map.get(rownum)
                if excel_row:
                    ws.cell(row=excel_row, column=col, value=score)

    def _write_dean_scores(self, ws):
        self_docs = self.processed_results.get(self.current_teacher, {}).get("Dean", [])
        if not self_docs:
            print(f"⚠️ No Self results for {self.current_teacher}")
            return

        # We only accept 1 self evaluation → take the first one
        _, result = self_docs[0]

        # Row mappings for each Section (Self rater)
        row_maps = {
            "Section 1": {1: 46, 2: 47, 3: 48, 4: 49, 5: 50},
            "Section 2": {1: 52, 2: 53, 3: 54, 4: 55, 5: 56},
            "Section 3": {1: 58, 2: 59, 3: 60, 4: 61, 5: 62},
            "Section 4": {1: 64, 2: 65, 3: 66, 4: 67, 5: 68},
        }

        # Fixed column index for column O = 15
        col = 15

        for section, row_map in row_maps.items():
            for rownum, score in result.get(section, {}).items():
                excel_row = row_map.get(rownum)
                if excel_row:
                    ws.cell(row=excel_row, column=col, value=score)
    
    def export_full_summary(self, template_path="template.xlsx"):
        
        try:
            wb = load_workbook(template_path)
            ws_ti = wb["TI"]
            ws_ter = wb["TER"]

            # Fill Student scores into TI sheet
            self._write_student_scores(ws_ti)

            # Fill manual/dean inputs into TER sheet
            self._write_manual_results(ws_ter)
            
            # Fill Peer scores into TER sheet
            self._write_peer_scores(ws_ter)
            
            # Fill Self scores into TER sheet
            self._write_self_scores(ws_ter)
            
            
            
            

            # Save as new file
            base_folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Summaries")
            os.makedirs(base_folder, exist_ok=True)

            safe_teacher = self.current_teacher.replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"Summary_{safe_teacher}_{timestamp}.xlsx"
            save_path = os.path.join(base_folder, new_filename)

            wb.save(save_path)
            messagebox.showinfo("Saved", f"✅ Summary saved to {save_path}")

        except Exception as e:
            messagebox.showerror("Save Error", str(e))




    