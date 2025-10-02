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
