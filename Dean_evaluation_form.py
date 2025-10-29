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


# --- Main Panel ---
class DeanEvaluationForm:
    def __init__(self, master, processed_results, results_file=None):
        if results_file is None:
            results_file = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "results.pkl")

        self.results_file = str(results_file)
        self.master = master
        self.processed_results = processed_results
        self.rating_vars = {}
        self.teacher_name_to_id = {}

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
                rows = conn.execute("SELECT id, full_name FROM faculty ORDER BY full_name").fetchall()
                if rows:
                    self.teacher_name_to_id = {full_name: fid for fid, full_name in rows}
                    teacher_list = list(self.teacher_name_to_id.keys())
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

        placeholder = "No teachers found"
        self.teacher_var = StringVar(value=teacher_list[0] if teacher_list else placeholder)
        teacher_dropdown = CTkOptionMenu(
            left, variable=self.teacher_var,
            values=teacher_list if teacher_list else [placeholder],
            width=280, state=("normal" if teacher_list else "disabled"),
        )
        self._theme_dropdown(teacher_dropdown)
        teacher_dropdown.pack(padx=16, pady=(0, 12), anchor="w")

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
                  command=self.save_dean_rating).pack(fill="x", pady=4)
        CTkButton(btns_primary, text="Save & Open Summary", fg_color="#BF3131",
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
        teacher = (self.teacher_var.get() or "").strip()
        if not teacher or teacher == "No teachers found":
            messagebox.showwarning("No Teacher", "Please select a teacher.")
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
        if "Dean" in self.processed_results[teacher] and self.processed_results[teacher]["Dean"]:
            overwrite = messagebox.askyesno("Overwrite Dean Rating",
                f"A Dean evaluation already exists for {teacher}.\nDo you want to overwrite it?")
            if not overwrite: return

        self.processed_results[teacher]["Dean"] = [("dean_input", sectioned_results)]
        self._save_results()

        messagebox.showinfo("Saved", f"Dean evaluation for {teacher} saved successfully.")
        if hasattr(self, "status_label"):
            self.status_label.configure(text="Saved")

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
        teacher = (self.teacher_var.get() or "").strip()
        if not teacher or teacher == "No teachers found":
            messagebox.showwarning("No Teacher", "Please select a teacher first.")
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
