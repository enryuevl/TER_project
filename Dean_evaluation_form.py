import os, pickle
from customtkinter import *
from tkinter import messagebox
import db


class DeanEvaluationForm:
    def __init__(self, master, processed_results, results_file="results.pkl"):
        """
        Dean Evaluation Form UI
        - master: parent frame (main_frame from main.py)
        - processed_results: shared results dictionary for all evaluations
        - results_file: path to pickle file for persistence
        """
        self.master = master
        self.processed_results = processed_results
        self.results_file = results_file
        self.rating_vars = {}
        self.teacher_name_to_id = {}

        # load from pickle (merge into processed_results)
        self._load_results()

        self._build_ui()

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        container = CTkFrame(self.master, fg_color="#F3F4F6")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        CTkLabel(container, text="Dean Evaluation Form",
                 font=("Roboto", 20, "bold"), text_color="#DC2626").pack(pady=10)

        # ---- Faculty Dropdown ----
        CTkLabel(container, text="Select Faculty:", font=("Roboto", 14)).pack(pady=5, anchor="w")

        teacher_list = []
        try:
            with db.connect() as conn:
                rows = conn.execute("SELECT id, full_name FROM faculty ORDER BY full_name").fetchall()
                if rows:
                    self.teacher_name_to_id = {full_name: fid for fid, full_name in rows}
                    teacher_list = list(self.teacher_name_to_id.keys())
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

        self.teacher_var = StringVar(value=teacher_list[0] if teacher_list else "")
        self.teacher_dropdown = CTkOptionMenu(
            container,
            variable=self.teacher_var,
            values=teacher_list if teacher_list else ["No teachers found"],
            width=250,
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=("Roboto", 14)
        )
        self.teacher_dropdown.pack(pady=5)

        # ---- Scrollable Content ----
        scroll = CTkScrollableFrame(container, fg_color="#FFFFFF")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        categories = {
            "A. Commitment": [
                "Demonstrates sensitivity to students' ability to learn",
                "Integrates objectives with students",
                "Availability beyond official time",
                "Preparedness and punctuality",
                "Accurate student records"
            ],
            "B. Knowledge of Subject": [
                "Mastery without relying on textbook",
                "Shares state of the art/practice",
                "Integrates subject to practical cases",
                "Relevance to prior lessons/issues",
                "Up-to-date knowledge of trends"
            ],
            "C. Teaching for Independent Learning": [
                "Creates strategies for interactive learning",
                "Enhances self-esteem / recognizes potential",
                "Allows own rules/objectives",
                "Encourages independent decisions",
                "Encourages innovation and going beyond"
            ],
            "D. Management of Learning": [
                "Creates varied contribution opportunities",
                "Acts as facilitator/resource",
                "Implements varied learning conditions",
                "Structures interactive class",
                "Uses instructional materials effectively"
            ]
        }

        # Column headers
        CTkLabel(scroll, text="Question", font=("Roboto", 12, "bold"))\
            .grid(row=0, column=0, sticky="w", padx=(10, 30), pady=5)
        for col, score in enumerate(range(5, 0, -1), start=1):
            CTkLabel(scroll, text=str(score), font=("Roboto", 12, "bold"))\
                .grid(row=0, column=col, padx=0, pady=5, sticky="n")

        row_index = 1
        for cat, questions in categories.items():
            CTkLabel(scroll, text=cat,
                     font=("Roboto", 14, "bold"), text_color="#DC2626")\
                .grid(row=row_index, column=0, columnspan=6,
                      sticky="w", pady=(15, 5), padx=5)
            row_index += 1

            for i, q in enumerate(questions, start=1):
                q_key = f"{cat}_{i}"
                CTkLabel(scroll, text=f"{i}. {q}", font=("Roboto", 12), anchor="w")\
                    .grid(row=row_index, column=0, sticky="w", padx=10, pady=3)

                self.rating_vars[q_key] = IntVar(value=0)
                for col, score in enumerate(range(5, 0, -1), start=1):
                    CTkRadioButton(scroll, text="", variable=self.rating_vars[q_key], value=score,
                                   radiobutton_width=18, radiobutton_height=18,
                                   fg_color="#691612")\
                        .grid(row=row_index, column=col, padx=25, pady=3, sticky="n")
                row_index += 1

        # Comments
        CTkLabel(scroll, text="Dean's Comments:", font=("Roboto", 14, "bold"), text_color="#DC2626")\
            .grid(row=row_index, column=0, columnspan=6, sticky="w", pady=(15, 5))
        row_index += 1
        self.comments_box = CTkTextbox(scroll, width=600, height=80, font=("Roboto", 12))
        self.comments_box.grid(row=row_index, column=0, columnspan=6, padx=10, pady=5, sticky="w")

        # Save button
        CTkButton(container, text="Save Evaluation", fg_color="#DC2626",
                  hover_color="#B91C1C", text_color="#FFFFFF",
                  font=("Roboto", 14, "bold"), corner_radius=8,
                  command=self.save_dean_rating).pack(pady=10)

        scroll.grid_columnconfigure(0, weight=5)
        for col in range(1, 6):
            scroll.grid_columnconfigure(col, weight=1, uniform="scale")


        # summary of ratings per section
        CTkButton(container, text="View Summary",
                fg_color="#AC5353", hover_color="#8B1D18",
                text_color="#FFFFFF", font=("Roboto", 14, "bold"),
                corner_radius=8, command=self.show_summary_window).pack(pady=(0, 10))

        






    # ---------------- SAVE ---------------- #
    def save_dean_rating(self):
        teacher = self.teacher_var.get()
        if not teacher or teacher == "No teachers found":
            messagebox.showwarning("No Teacher", "Please select a teacher.")
            return

        # Map categories to "Section n"
        section_map = {
            "A. Commitment": "Section 1",
            "B. Knowledge of Subject": "Section 2",
            "C. Teaching for Independent Learning": "Section 3",
            "D. Management of Learning": "Section 4",
        }

        # Build structured results
        sectioned_results = {"Section 1": {}, "Section 2": {}, "Section 3": {}, "Section 4": {}}
        for q_key, var in self.rating_vars.items():
            # q_key looks like "A. Commitment_1"
            cat, idx = q_key.rsplit("_", 1)
            section = section_map.get(cat)
            if section:
                sectioned_results[section][int(idx)] = var.get()

        # Ensure teacher entry exists
        self.processed_results.setdefault(teacher, {})

        # Overwrite check
        if "Dean" in self.processed_results[teacher] and self.processed_results[teacher]["Dean"]:
            overwrite = messagebox.askyesno(
                "Overwrite Dean Rating",
                f"A Dean evaluation already exists for {teacher}.\nDo you want to overwrite it?"
            )
            if not overwrite:
                return

        # Save dean rating in normalized format
        self.processed_results[teacher]["Dean"] = [
            ("dean_input", sectioned_results)
        ]

        # Persist into results.pkl
        self._save_results()

        messagebox.showinfo("Saved", f"Dean evaluation for {teacher} saved successfully.")
        print("✅ Dean Evaluation Saved:", teacher, sectioned_results)

    def _save_results(self):
        try:
            with open(self.results_file, "wb") as f:
                pickle.dump({"results": self.processed_results}, f)
            print(f"💾 Dean results saved to {os.path.abspath(self.results_file)}")
        except Exception as e:
            print(f"❌ Error saving results.pkl: {e}")

    def _load_results(self):
        if not os.path.exists(self.results_file):
            return
        try:
            with open(self.results_file, "rb") as f:
                data = pickle.load(f)
            self.processed_results.update(data.get("results", {}))
            print(f"📂 Loaded existing results from {self.results_file}")
        except Exception as e:
            print(f"❌ Error loading results.pkl: {e}")

    
       


    # ---------------- SUMMARY from ---------------- #
    def compute_equivalent_numerical(self, overall_score: float) -> int:
        if overall_score >= 9.3: return 10
        elif overall_score >= 7.5: return 8
        elif overall_score >= 5:   return 6
        elif overall_score >= 3:   return 4
        else:                      return 2

    def compute_adjective_rating(self, eq_num: int) -> str:
        mapping = {
            10: "Outstanding (O)",
            8:  "Very Satisfactory (VS)",
            6:  "Satisfactory (S)",
            4:  "Fair (F)",
            2:  "Unsatisfactory (US)"
        }
        return mapping.get(eq_num, "")

    def calculate_row_averages(self, teacher_name, rater_type=None):
        """Compute averages for a teacher and selected rater type (Student/Peer/Dean)."""
        teacher_data = self.processed_results.get(teacher_name, {})
        if isinstance(teacher_data, list):
            teacher_data = {"Unknown": teacher_data}

        # default to Dean if not specified
        rater_type = rater_type or "Dean"
        if rater_type not in teacher_data:
            return {}

        row_scores = {}
        for _, result, *_ in teacher_data[rater_type]:
            for section, rows in result.items():
                for rownum, score in rows.items():
                    row_key = f"{section} R{rownum}"
                    row_scores.setdefault(row_key, []).append(score)

        averages = {}
        for row_key, scores in row_scores.items():
            if scores:
                averages[row_key] = sum(scores) / len(scores)
        return averages

    def update_overall_point_score(self):
        """Sum all point scores and update the Overall Point Score + equivalents."""
        total = 0.0
        for key, widgets in self.entry_widgets.items():
            if isinstance(widgets, dict) and "point" in widgets:
                try:
                    total += float(widgets["point"].get().strip() or 0)
                except ValueError:
                    pass

        # Plus Factor (optional, up to 1)
        if "plus_factor" in self.entry_widgets:
            try:
                total += float(self.entry_widgets["plus_factor"].get().strip() or 0)
            except ValueError:
                pass

        # Overall
        if "overall_point" in self.entry_widgets:
            e = self.entry_widgets["overall_point"]
            e.delete(0, "end"); e.insert(0, f"{total:.2f}")

        eq_num = self.compute_equivalent_numerical(total)
        if "eq_numerical" in self.entry_widgets:
            e = self.entry_widgets["eq_numerical"]
            e.delete(0, "end"); e.insert(0, str(eq_num))

        eq_adj = self.compute_adjective_rating(eq_num)
        if "eq_adjective" in self.entry_widgets:
            e = self.entry_widgets["eq_adjective"]
            e.delete(0, "end"); e.insert(0, eq_adj)

    def set_value(self, key, value, field=None):
        """Set a value into an entry or textbox inside entry_widgets."""
        if key not in self.entry_widgets:
            return
        widget = self.entry_widgets[key]
        if isinstance(widget, dict):
            if field not in widget: return
            widget = widget[field]
        if hasattr(widget, "insert") and hasattr(widget, "delete"):
            if "Textbox" in widget.__class__.__name__:
                widget.delete("1.0", "end"); widget.insert("1.0", value)
            else:
                widget.delete(0, "end"); widget.insert(0, value)

    def get_department_for_teacher(self, teacher_name: str) -> str:
        """Lookup department name for a teacher in the database using full_name."""
        try:
            conn = db.connect(); cur = conn.cursor()
            cur.execute("""
                SELECT d.name
                FROM faculty f
                JOIN departments d ON f.department_id = d.id
                WHERE f.full_name = ?
            """, (teacher_name,))
            row = cur.fetchone(); conn.close()
            return row[0] if row else ""
        except Exception as e:
            print(f"❌ DB lookup failed: {e}")
            return ""

    # ---------------- SUMMARY UI ---------------- #

    def show_summary_window(self):
        teacher = self.teacher_var.get().strip()
        if not teacher or teacher == "No teachers found":
            messagebox.showwarning("No Teacher", "Please select a teacher first.")
            return

        # 1) Build the popup and UI controls, collect references in self.entry_widgets
        self._open_summary_popup(teacher)

        # 2) Auto-fill Instructor & Department
        if "instructor" in self.entry_widgets:
            self.entry_widgets["instructor"].delete(0, "end")
            self.entry_widgets["instructor"].insert(0, teacher)

        dept = self.get_department_for_teacher(teacher)
        if dept and "department" in self.entry_widgets:
            self.entry_widgets["department"].delete(0, "end")
            self.entry_widgets["department"].insert(0, dept)

        # 3) Fill ratings for Instruction (Student/Peer/Dean) using same weights
        mapping = {
            "Student": ("student_rater", 25),
            "Peer":    ("peer_rater",    15),
            "Dean":    ("dean_rater",    15),
        }
        for rater_key, (entry_key, weight) in mapping.items():
            averages = self.calculate_row_averages(teacher, rater_key)
            grand_total = sum(averages.values()) if averages else 0.0

            # Rating
            self.set_value(entry_key, f"{grand_total:.2f}", field="rating")

            # Equivalent = Rating ÷ 10
            rating_equiv = grand_total / 10 if grand_total else 0.0
            self.set_value(entry_key, f"{rating_equiv:.2f}", field="equivalent")

            # Point Score = Equivalent × Weight%
            point_score = rating_equiv * (weight / 100.0)
            self.set_value(entry_key, f"{point_score:.2f}", field="point")

        # 4) Compute overall (includes any Behavior you type + Plus Factor)
        self.update_overall_point_score()

    def _open_summary_popup(self, teacher_name: str):
        # Centered popup
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        x = (screen_w - 1280) // 2
        y = (screen_h - 720) // 2

        win = CTkToplevel(self.master)
        win.title(f"Teaching Efficiency Rating - {teacher_name}")
        win.geometry(f"1280x720+{x}+{y}")
        win.configure(fg_color="#F3F4F6")
        win.transient(self.master); win.grab_set(); win.focus_force(); win.lift()

        # Scrollable frame
        scroll_frame = CTkScrollableFrame(
            win, fg_color="#FFFFFF",
            label_font=("Roboto", 14, "bold"),
            label_text_color="#DC2626"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # store all entry references
        self.entry_widgets = {}

        # Helpers to add rows
        def add_row(parent, row_idx, label, percent="", key=None):
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
                self.entry_widgets[key] = {"rating": rating_entry, "equivalent": eq_entry, "point": point_entry}

        def add_behavior_row(parent, row_idx, label, percent="", key=None):
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
                    "equivalent": eq_entry, "point": point_entry,
                    "weight": float(percent.strip('%')) if percent else 0.0,
                }

                def update_point(_event=None, entry_key=key):
                    val = eq_entry.get().strip()
                    try:
                        num = float(val)
                        weight = self.entry_widgets[entry_key]["weight"] / 100.0
                        point = num * weight
                        point_entry.delete(0, "end"); point_entry.insert(0, f"{point:.2f}")
                    except ValueError:
                        point_entry.delete(0, "end")
                    self.update_overall_point_score()

                eq_entry.bind("<KeyRelease>", update_point)

        # Header
        CTkLabel(scroll_frame, text="TEACHING EFFICIENCY RATING (TER) SCALE FORM",
                 font=("Roboto", 16, "bold"), text_color="#FFFFFF",
                 fg_color="#DC2626", corner_radius=6).pack(fill="x", pady=5)

        # Instructor Info
        info_frame = CTkFrame(scroll_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=5)
        for lbl in ["Instructor:", "College:", "Rating Period:", "Department:"]:
            CTkLabel(info_frame, text=lbl, font=("Roboto", 12), text_color="#1F2937").pack(side="left", padx=5)
            e = CTkEntry(info_frame, width=150, font=("Roboto", 12))
            e.pack(side="left", padx=10)
            self.entry_widgets[lbl.strip(":").lower()] = e

        # PERFORMANCE 70%
        perf = CTkFrame(scroll_frame, fg_color="transparent")
        perf.pack(fill="x", pady=10)
        CTkLabel(perf, text="I. PERFORMANCE (70%)",
                 font=("Roboto", 14, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))
        headers = ["", "RATING", "RATING EQUIVALENT", "RATING %", "POINT SCORE"]
        for i, h in enumerate(headers):
            CTkLabel(perf, text=h, font=("Roboto", 12, "bold"),
                     text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

        CTkLabel(perf, text="1. Instruction (55%)",
                 font=("Roboto", 12, "bold"), text_color="#DC2626")\
            .grid(row=2, column=0, sticky="w", pady=(0, 3))
        add_row(perf, 3, "a) Student as Rater", "25%", key="student_rater")
        add_row(perf, 4, "b) Peer as Rater",    "15%", key="peer_rater")
        add_row(perf, 5, "c) Dean as Rater",    "15%", key="dean_rater")

        add_behavior_row(perf, 6, "2. Research",   "5%", key="research")
        add_behavior_row(perf, 7, "3. Extension",  "5%", key="extension")
        add_behavior_row(perf, 8, "4. Production", "5%", key="production")

        # BEHAVIOR 30%
        beh = CTkFrame(scroll_frame, fg_color="transparent")
        beh.pack(fill="x", pady=10)
        CTkLabel(beh, text="II. BEHAVIOR (30%)",
                 font=("Roboto", 14, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))
        for i, h in enumerate(headers):
            CTkLabel(beh, text=h, font=("Roboto", 12, "bold"),
                     text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

        add_behavior_row(beh, 2, "1. Courtesy",                          "7.5%", key="courtesy")
        add_behavior_row(beh, 3, "2. Human Relations",                   "7.5%", key="human_relations")
        add_behavior_row(beh, 4, "3. Punctuality and Attendance",        "7.5%", key="punctuality")
        add_behavior_row(beh, 5, "4. Initiative",                        "7.5%", key="initiative")
        add_behavior_row(beh, 6, "5. Leadership (Supervisors only)",     "5%",   key="leadership")
        add_behavior_row(beh, 7, "6. Stress Tolerance (Supervisors only)","5%",   key="stress_tolerance")

        # Plus Factor
        plus = CTkFrame(scroll_frame, fg_color="transparent")
        plus.pack(fill="x", pady=10)
        CTkLabel(plus, text="PLUS FACTOR (not to exceed one (1) credit point)",
                 font=("Roboto", 12, "bold"), text_color="#DC2626")\
            .grid(row=0, column=0, sticky="w", pady=(0, 5))
        e_plus = CTkEntry(plus, width=120, font=("Roboto", 12))
        e_plus.grid(row=0, column=1, padx=5, pady=2)
        self.entry_widgets["plus_factor"] = e_plus
        e_plus.bind("<KeyRelease>", lambda _e: self.update_overall_point_score())

        # Summary Ratings
        summ = CTkFrame(scroll_frame, fg_color="transparent")
        summ.pack(fill="x", pady=10)
        labels = [
            ("Overall Point Score", "overall_point"),
            ("Equivalent Numerical Rating", "eq_numerical"),
            ("Equivalent Adjective Rating", "eq_adjective"),
        ]
        for idx, (text, key) in enumerate(labels):
            CTkLabel(summ, text=text, font=("Roboto", 12, "bold"),
                     text_color="#1F2937").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
            e = CTkEntry(summ, width=120, font=("Roboto", 12))
            e.grid(row=idx, column=1, padx=5, pady=2)
            self.entry_widgets[key] = e

        # Comments
        comments = CTkFrame(scroll_frame, fg_color="transparent")
        comments.pack(fill="x", pady=10)
        CTkLabel(comments, text="EMPLOYEE'S COMMENTS/REMARKS",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        self.entry_widgets["employee_comments"] = CTkTextbox(comments, height=50, width=900, font=("Roboto", 12))
        self.entry_widgets["employee_comments"].pack(pady=5)
        CTkLabel(comments, text="RATER'S COMMENTS/REMARKS",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        self.entry_widgets["rater_comments"] = CTkTextbox(comments, height=50, width=900, font=("Roboto", 12))
        self.entry_widgets["rater_comments"].pack(pady=5)

        # Save/Close Row (Export optional)
        btn_row = CTkFrame(scroll_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)
        CTkButton(btn_row, text="Close", fg_color="#9CA3AF", hover_color="#6B7280",
                  text_color="#FFFFFF", command=win.destroy).pack(side="right")
