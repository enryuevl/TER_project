import os, pickle
from customtkinter import *
from tkinter import messagebox
import db
from summary_helpers import SummaryFormController


# --- Rating chips with custom palette (1–5) ---
class RatingChips(CTkFrame):
    ACTIVE_BG = "#AC5353"
    ACTIVE_HOVER = "#BF3131"
    ACTIVE_TEXT = "#FFFFFF"
    INACTIVE_BG = "#F1F3F5"
    INACTIVE_HOVER = "#E9ECEF"
    INACTIVE_TEXT = "#333333"

    def __init__(self, master, values=("1","2","3","4","5"), variable=None, **kwargs):
        super().__init__(master, fg_color="#FFFFFF", **kwargs)
        self.values = list(values)
        self.variable = variable if variable is not None else StringVar(value="0")
        self.buttons = []

        for i, val in enumerate(self.values):
            b = CTkButton(
                self, text=val,
                width=36, height=28, corner_radius=8,
                command=lambda v=val: self.set(v)
            )
            padx = (0, 6) if i < len(self.values)-1 else (0, 0)
            b.pack(side="left", padx=padx, pady=0)
            self.buttons.append(b)

        self._apply_styles()

        def _watch(*_):
            self._apply_styles()
        try:
            self.variable.trace_add("write", _watch)
        except Exception:
            pass

    def get(self): return self.variable.get()
    def set(self, value):
        self.variable.set(str(value))
        self._apply_styles()

    def _apply_styles(self):
        current = str(self.variable.get())
        for btn in self.buttons:
            is_active = (btn.cget("text") == current)
            if is_active:
                btn.configure(
                    fg_color=self.ACTIVE_BG,
                    hover_color=self.ACTIVE_HOVER,
                    text_color=self.ACTIVE_TEXT
                )
            else:
                btn.configure(
                    fg_color=self.INACTIVE_BG,
                    hover_color=self.INACTIVE_HOVER,
                    text_color=self.INACTIVE_TEXT
                )

# --- Custom exception for dean overwrites ---
class OverwriteDeanEvaluationError(Exception):
    pass


# --- Main Panel ---
class DeanEvaluationForm:
    def __init__(self, master, processed_results, results_file=None, ctx=None):
        if results_file is None:
            results_file = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "results.pkl")

        self.results_file = str(results_file)
        self.master = master
        self.processed_results = processed_results
        self.rating_vars = {}
        self.teacher_name_to_id = {}
        self.peer_name_to_id = {}
        self.ctx = ctx

        if results_file == "results.pkl" or not os.path.isabs(results_file):
            base_dir = os.path.dirname(db.get_default_db_path())
            self.results_file = os.path.join(base_dir, "results.pkl")
        else:
            self.results_file = results_file

        self._load_results()
        self.summary = SummaryFormController(self.processed_results, db_module=db)
        self._build_ui()

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for w in self.master.winfo_children(): w.destroy()

        container = CTkFrame(self.master, fg_color="#F3F4F6")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title_bar = CTkFrame(container, fg_color="#BF3131", height=60, corner_radius=10)
        title_bar.pack(fill="x", padx=0, pady=(0, 12))
        CTkLabel(title_bar, text="Dean Evaluation Panel",
                 font=("Poppins", 20, "bold"), text_color="#FFFFFF").pack(side="left", padx=16, pady=12)

        body = CTkFrame(container, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0, minsize=320)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Left panel
        left = CTkFrame(body, fg_color="#FFFFFF", corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        left.grid_rowconfigure(99, weight=1)

        CTkLabel(left, text="Select Faculty", font=("Roboto", 14, "bold"),
                 text_color="#691612").pack(anchor="w", padx=16, pady=(16, 6))

        teacher_list = []
        try:
            with db.connect() as conn:
                teacher_query = [
                    "SELECT id, full_name",
                    "FROM faculty",
                    "WHERE is_active = 1"
                ]
                params = []
                dept_id = getattr(self.ctx, "department_id", None)
                if dept_id is not None:
                    teacher_query.append("AND department_id = ?")
                    params.append(dept_id)
                teacher_query.append("ORDER BY full_name")
                query = " ".join(teacher_query)
                rows = conn.execute(query, params).fetchall()
                if rows:
                    self.teacher_name_to_id = {full_name: fid for fid, full_name in rows}
                    teacher_list = list(self.teacher_name_to_id.keys())
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

        placeholder = "No teachers found"
        placeholder_peer = "No peers found"
        self.teacher_var = StringVar(value=placeholder)
        self.peer_var = StringVar(value=placeholder_peer)
        
        teacher_dropdown = CTkOptionMenu(
            left, variable=self.teacher_var,
            values=[placeholder] + teacher_list if teacher_list else [placeholder],
            width=280, state=("normal" if teacher_list else "disabled"),
        )
        self._theme_dropdown(teacher_dropdown)
        teacher_dropdown.pack(padx=16, pady=(0, 6), anchor="w")

        # Peer dropdown for evaluating deans from other departments
        CTkLabel(left, text="Select Peer (Dean)", font=("Roboto", 14, "bold"),
                 text_color="#691612").pack(anchor="w", padx=16, pady=(12, 6))

        peer_list = []
        self.peer_name_to_id = {}
        try:
            with db.connect() as conn:
                dept_id = getattr(self.ctx, "department_id", None)
                if dept_id is not None:
                    # Get deans from other departments
                    peer_query = """
                        SELECT f.id, f.full_name
                        FROM faculty f
                        JOIN departments d ON d.dean_id = f.id
                        WHERE f.is_active = 1
                          AND d.id != ?
                        ORDER BY f.full_name
                    """
                    rows = conn.execute(peer_query, (dept_id,)).fetchall()
                    if rows:
                        self.peer_name_to_id = {full_name: fid for fid, full_name in rows}
                        peer_list = list(self.peer_name_to_id.keys())
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

        peer_dropdown = CTkOptionMenu(
            left, variable=self.peer_var,
            values=[placeholder_peer] + peer_list if peer_list else [placeholder_peer],
            width=280, state=("normal" if peer_list else "disabled"),
        )
        self._theme_dropdown(peer_dropdown)
        peer_dropdown.pack(padx=16, pady=(0, 12), anchor="w")

        # Auto-clear logic: when one dropdown is selected, clear the other
        def on_teacher_change(*args):
            if self.teacher_var.get() != placeholder:
                self.peer_var.set(placeholder_peer)
        
        def on_peer_change(*args):
            if self.peer_var.get() != placeholder_peer:
                self.teacher_var.set(placeholder)
        
        self.teacher_var.trace_add("write", on_teacher_change)
        self.peer_var.trace_add("write", on_peer_change)

        meta = CTkFrame(left, fg_color="#F8F9FA")
        meta.pack(fill="x", padx=16, pady=(0, 12))
        CTkLabel(meta, text="Current Period", font=("Roboto", 12, "bold"),
                 text_color="#374151").pack(anchor="w", pady=(8, 2))
        CTkLabel(meta, text=self._current_period_label(), font=("Roboto", 12),
                 text_color="#6B7280").pack(anchor="w", pady=(0, 8))

        CTkLabel(left, text="Actions", font=("Roboto", 14, "bold"),
                 text_color="#691612").pack(anchor="w", padx=16, pady=(4, 6))
        btns_primary = CTkFrame(left, fg_color="transparent")
        btns_primary.pack(fill="x", padx=16, pady=(0, 8))
        CTkButton(btns_primary, text="Save Evaluation", fg_color="#691612",
                  hover_color="#8B1D18", text_color="#FFFFFF",
                  command=self._save_evaluation).pack(fill="x", pady=4)
        CTkButton(btns_primary, text="View Summary", fg_color="#AC5353",
                  hover_color="#8B1D18", text_color="#FFFFFF",
                  command=self._open_summary_for_current).pack(fill="x", pady=4)
    

        CTkLabel(left, text="Utilities", font=("Roboto", 14, "bold"),
                 text_color="#691612").pack(anchor="w", padx=16, pady=(8, 6))
        utils_box = CTkFrame(left, fg_color="transparent")
        utils_box.pack(fill="x", padx=16, pady=(0, 8))

        self.autosave_var = BooleanVar(value=False)
        CTkSwitch(utils_box, text="Autosave on change", variable=self.autosave_var,
                  progress_color="#BF3131", fg_color="#E5E7EB",
                  button_color="#691612").pack(anchor="w", pady=4)
        CTkButton(utils_box, text="Clear Responses", fg_color="#AC5353",
                  hover_color="#8B1D18", text_color="#FFFFFF",
                  command=self._clear_responses).pack(fill="x", pady=4)

        sticky = CTkFrame(left, fg_color="#F8F9FA", corner_radius=10)
        sticky.pack(fill="x", padx=16, pady=(8, 16))
        self.status_label = CTkLabel(sticky, text="Ready",
                                     font=("Roboto", 12), text_color="#374151")
        self.status_label.pack(side="left", padx=12, pady=8)

        # Right panel
        right = CTkFrame(body, fg_color="#FFFFFF", corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=0)

        header = CTkFrame(right, fg_color="#FFFFFF")
        header.pack(fill="x", padx=16, pady=(16, 8))
        CTkLabel(header, text="Evaluation", font=("Roboto", 16, "bold"),
                 text_color="#691612").pack(side="left")

        scroll = CTkScrollableFrame(right, fg_color="#FFFFFF")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._build_evaluation_grid(scroll)

    # ---------- helpers ----------
    def _theme_dropdown(self, menu: CTkOptionMenu):
        try:
            menu.configure(
                fg_color="#BF3131", button_color="#691612",
                button_hover_color="#8B1D18", text_color="#FFFFFF",
                dropdown_fg_color="#FFFFFF", dropdown_text_color="#1F2937",
                dropdown_hover_color="#F3F4F6",
            )
        except Exception: pass

    def _current_period_label(self):
        import datetime as _dt
        now = _dt.datetime.now()
        y = now.year
        month = now.month
        sem = "1st" if 8 <= month <= 12 else ("2nd" if 1 <= month <= 6 else "Summer")
        ay = f"{y}-{y+1}" if sem == "1st" else f"{y-1}-{y}"
        return f"{ay} • {sem}"

    def _infer_ay_and_sem_from_today(self):
        import datetime as _dt
        now = _dt.datetime.now()
        y, m = now.year, now.month
        if 8 <= m <= 12:
            return f"{y}-{y+1}", "1st"
        elif 1 <= m <= 6:
            return f"{y-1}-{y}", "2nd"
        else:
            return f"{y-1}-{y}", "Summer"

    
    # ---------- grid builder ----------
    def _build_evaluation_grid(self, parent):
        legend = CTkFrame(parent, fg_color="#FFFFFF")
        legend.pack(fill="x", padx=6, pady=(6, 0))
        CTkLabel(legend, text="Rate 1 (lowest) … 5 (highest)",
                 font=("Roboto", 11), text_color="#6B7280").pack(side="left", padx=6, pady=4)

        categories = {
            "A. Commitment": [
                "Demonstrates sensitivity to students' ability to learn",
                "Integrates objectives with students",
                "Availability beyond official time",
                "Preparedness and punctuality",
                "Accurate student records",
            ],
            "B. Knowledge of Subject": [
                "Mastery without relying on textbook",
                "Shares state of the art/practice",
                "Integrates subject to practical cases",
                "Relevance to prior lessons/issues",
                "Up-to-date knowledge of trends",
            ],
            "C. Teaching for Independent Learning": [
                "Creates strategies for interactive learning",
                "Enhances self-esteem / recognizes potential",
                "Allows own rules/objectives",
                "Encourages independent decisions",
                "Encourages innovation and going beyond",
            ],
            "D. Management of Learning": [
                "Creates varied contribution opportunities",
                "Acts as facilitator/resource",
                "Implements varied learning conditions",
                "Structures interactive class",
                "Uses instructional materials effectively",
            ],
        }

        wrap = CTkFrame(parent, fg_color="#FFFFFF")
        wrap.pack(fill="both", expand=True, padx=6, pady=6)

        for cat, questions in categories.items():
            card = CTkFrame(wrap, fg_color="#FFFFFF", corner_radius=10)
            card.pack(fill="x", padx=0, pady=(0, 10))

            header = CTkFrame(card, fg_color="#FFFFFF", corner_radius=10)
            header.pack(fill="x", padx=0, pady=0)
            CTkLabel(header, text=cat, font=("Roboto", 14, "bold"),
                     text_color="#691612").pack(side="left", padx=10, pady=8)

            grid = CTkFrame(card, fg_color="#FFFFFF")
            grid.pack(fill="x", padx=10, pady=8)
            grid.grid_columnconfigure(0, weight=1)
            grid.grid_columnconfigure(1, weight=0)

            for i, q in enumerate(questions, start=1):
                key = f"{cat}_{i}"
                lbl = CTkLabel(grid, text=f"{i}. {q}", font=("Roboto", 12),
                               text_color="#111827", anchor="w")
                lbl.grid(row=i, column=0, sticky="w", padx=(8, 8), pady=3)
                try: lbl._label.configure(wraplength=650)
                except Exception: pass

                var = self.rating_vars.get(key)
                if var is None:
                    var = StringVar(value="0")
                    self.rating_vars[key] = var
                else:
                    try:
                        var = StringVar(value=str(int(var.get())))
                        self.rating_vars[key] = var
                    except Exception:
                        var = StringVar(value="0")
                        self.rating_vars[key] = var

                chips = RatingChips(grid, values=("1","2","3","4","5"), variable=var)
                chips.grid(row=i, column=1, sticky="e", padx=(8, 8), pady=3)

                def _mk_cb(_k=key):
                    def _cb(*_):
                        if hasattr(self, "autosave_var") and self.autosave_var.get():
                            if hasattr(self, "status_label"):
                                self.status_label.configure(text="Autosaving…")
                            self.save_dean_rating()
                            if hasattr(self, "status_label"):
                                self.status_label.configure(text="Saved")
                    return _cb
                self.rating_vars[key].trace_add("write", _mk_cb())

        comments = CTkFrame(parent, fg_color="#FFFFFF")
        comments.pack(fill="x", padx=6, pady=(4, 6))
        CTkLabel(comments, text="Dean's Comments",
                 font=("Roboto", 13, "bold"), text_color="#691612").pack(anchor="w", padx=6, pady=(6, 2))
        self.comments_box = CTkTextbox(comments, height=80, font=("Roboto", 12))
        self.comments_box.pack(fill="x", padx=6, pady=(0, 8))

    # ---------- Save / Load ----------
    def save_dean_rating(self):
        # Determine mode based on which dropdown has a selection
        teacher_selected = (self.teacher_var.get() or "").strip()
        peer_selected = (self.peer_var.get() or "").strip()
        placeholder = "No teachers found"
        placeholder_peer = "No peers found"
        
        if peer_selected and peer_selected != placeholder_peer:
            # Peer evaluation: peer dropdown is selected
            teacher = peer_selected
            rater_type = "Peer"
        elif teacher_selected and teacher_selected != placeholder:
            # Dean evaluation: faculty dropdown is selected
            teacher = teacher_selected
            rater_type = "Dean"
        else:
            messagebox.showwarning("No Selection", "Please select either a faculty member or a peer (dean) to evaluate.")
            return

        section_map = {
            "A. Commitment": "Section 1",
            "B. Knowledge of Subject": "Section 2",
            "C. Teaching for Independent Learning": "Section 3",
            "D. Management of Learning": "Section 4",
        }

        sectioned_results = {s: {} for s in section_map.values()}
        for q_key, var in self.rating_vars.items():
            cat, idx = q_key.rsplit("_", 1)
            section = section_map.get(cat)
            if section:
                try:
                    sectioned_results[section][int(idx)] = int(var.get())
                except Exception:
                    sectioned_results[section][int(idx)] = 0

        self.processed_results.setdefault(teacher, {})
        
        # For Peer evaluations, append to list (multiple peers can evaluate)
        # For Dean evaluations, keep single entry (overwrite check)
        if rater_type == "Peer":
            if "Peer" not in self.processed_results[teacher]:
                self.processed_results[teacher]["Peer"] = []
            # Check if this peer already evaluated
            existing_peer = any(
                name == f"peer_dean_{self.ctx.department_id}" 
                for name, _, *_ in self.processed_results[teacher]["Peer"]
            )
            if existing_peer:
                # Update existing peer evaluation
                for i, (name, _, *_) in enumerate(self.processed_results[teacher]["Peer"]):
                    if name == f"peer_dean_{self.ctx.department_id}":
                        self.processed_results[teacher]["Peer"][i] = (f"peer_dean_{self.ctx.department_id}", sectioned_results)
                        break
            else:
                # Add new peer evaluation
                self.processed_results[teacher]["Peer"].append((f"peer_dean_{self.ctx.department_id}", sectioned_results))
            overwrote = existing_peer
        else:
            # Dean evaluation: single entry
            overwrote = bool(self.processed_results[teacher].get("Dean"))
            self.processed_results[teacher]["Dean"] = [("dean_input", sectioned_results)]

        self._save_results()
        # write/update the Excel summary using the shared path
        try:
            self._export_summary_excel(teacher)
        except Exception as _ex:
            print(f"⚠️ {rater_type} export failed: {_ex}")

        if not overwrote:
            eval_type = "Peer evaluation" if rater_type == "Peer" else "Dean evaluation"
            messagebox.showinfo("Saved", f"{eval_type} for {teacher} saved successfully.")
            if hasattr(self, "status_label"):
                self.status_label.configure(text="Saved")
            return

        # Raise when overwriting an existing Dean evaluation
        if rater_type == "Dean":
            raise OverwriteDeanEvaluationError(f"Overwriting existing Dean evaluation for: {teacher}")
        else:
            # For peer, just show info that it was updated
            messagebox.showinfo("Updated", f"Peer evaluation for {teacher} has been updated.")
            if hasattr(self, "status_label"):
                self.status_label.configure(text="Updated")


    def _save_results(self):
        try:
            with open(self.results_file, "wb") as f:
                pickle.dump({"results": self.processed_results}, f)
            print(f"💾 Dean results saved to {os.path.abspath(self.results_file)}")
        except Exception as e:
            print(f"❌ Error saving results.pkl: {e}")

    def _load_results(self):
        if not os.path.exists(self.results_file): return
        try:
            with open(self.results_file, "rb") as f:
                data = pickle.load(f)
            self.processed_results.update(data.get("results", {}))
            print(f"📂 Loaded existing results from {self.results_file}")
        except Exception as e:
            print(f"❌ Error loading results.pkl: {e}")

    # ---------- Utilities ----------
    def _open_summary_for_current(self):
        # Determine which dropdown has a selection
        teacher_selected = (self.teacher_var.get() or "").strip()
        peer_selected = (self.peer_var.get() or "").strip()
        placeholder = "No teachers found"
        placeholder_peer = "No peers found"
        
        if peer_selected and peer_selected != placeholder_peer:
            teacher = peer_selected
        elif teacher_selected and teacher_selected != placeholder:
            teacher = teacher_selected
        else:
            messagebox.showwarning("No Selection", "Please select either a faculty member or a peer (dean) first.")
            return
        
        self.summary.processed_results = self.processed_results
        self.summary.show(self.master, teacher)

    def _clear_responses(self):
        for var in self.rating_vars.values():
            try: var.set("0")
            except Exception: pass
        if hasattr(self, "comments_box"):
            try: self.comments_box.delete("1.0", "end")
            except Exception: pass
        if hasattr(self, "status_label"):
            self.status_label.configure(text="Cleared")

    def _save_evaluation(self):
        """Save the evaluation without opening the summary."""
        try:
            self.save_dean_rating()
        except OverwriteDeanEvaluationError as e:
            # The save already happened, just inform the user it was overwritten
            messagebox.showwarning("Overwritten", f"The evaluation has been overwritten.\n\n{str(e)}")
            if hasattr(self, "status_label"):
                self.status_label.configure(text="Overwritten")

    def _export_summary_excel(self, teacher: str):
        if not teacher or teacher == "No teachers found":
            return

        # 1) Make sure the controller knows the teacher (export_full_summary uses this)
        self.summary.processed_results = self.processed_results
        try:
            # SummaryFormController expects a current_teacher attr
            self.summary.current_teacher = teacher
        except Exception:
            pass

       
        ay, sem = self._infer_ay_and_sem_from_today()
        try:
            if getattr(self.summary, "semester_var", None):
               self.summary.semester_var.set(sem)
            if getattr(self.summary, "academic_year_var", None):
               self.summary.academic_year_var.set(ay)
        except Exception:
            pass

        
        template_path = "template.xlsx"
        save_path = None
        if hasattr(self.summary, "export_full_summary"):
            save_path = self.summary.export_full_summary(template_path)  # returns the file it saved

        # 3) Move/rename to your unified naming/location so ScanPage & Dean match
        try:
            from utils import get_summary_export_path
            ay, sem = self._infer_ay_and_sem_from_today()
            target_path = get_summary_export_path(teacher, ay, sem)

            if save_path and os.path.exists(save_path):
                # ensure target dir exists
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                import shutil
                # replace/overwrite to keep single source of truth
                try:
                    os.replace(save_path, target_path)
                except Exception:
                    shutil.copyfile(save_path, target_path)
            else:
                # If helper didn’t produce a file, fall back to simple writer
                include_raters = ("Student", "Peer", "Self", "Dean")
                self._fallback_write_excel(target_path, teacher, include_raters)
        except Exception as e:
            print(f"⚠️ Dean export normalization failed: {e}")
