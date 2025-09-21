from customtkinter import *
from PIL import Image, ImageTk
from customtkinter import CTkImage
import json
import pickle
import os
from tkinter import messagebox, filedialog
import main_code
import pandas as pd
import cv2, numpy as np, os, threading
from scanner import WIAScanner
import db
import pythoncom


class ScanPage:
    def __init__(self, master, processed_results):
        """Initialize the Scan Page inside a given frame."""
        self.master = master
        self.processed_results = processed_results
        self.last_processed_times = {}
        self.annotated_cache = {}  # Cache for annotated images
        self.load_results()

        # Tkinter variables
        self.teacher_var = StringVar()
        self.subject_var = StringVar()
        self.block_var = StringVar()

        # ID mappings
        self.teacher_name_to_id = {}
        self.subject_code_to_id = {}
        self.block_label_to_id = {}

        # Build UI
        self._build_ui()

        # Load teacher list from DB
        self.load_teachers()


    # ---------------- UI BUILDERS ---------------- #
    def _build_ui(self):
        """Create the layout and widgets."""
        for widget in self.master.winfo_children():
            widget.destroy()

        self.content_frame = CTkFrame(self.master, fg_color="#F8F9FA")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        main_layout = CTkFrame(self.content_frame, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=10)
        main_layout.grid_columnconfigure(0, weight=1)
        main_layout.grid_columnconfigure(1, weight=3)

        # Left column
        left_column = CTkFrame(main_layout, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="nsew", padx=10)

        self._build_scanner_controls(left_column)
        self._build_teacher_dropdown(left_column)
        self._build_results_panel(left_column)

        # Right column (Preview)
        right_column = CTkFrame(main_layout, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=10)
        self._build_preview_panel(right_column)


    def _build_scanner_controls(self, parent):
        scanner_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        scanner_frame.pack(fill="x", pady=10)

        CTkLabel(scanner_frame, text="Document Scanner",
                 font=('Montserrat', 18, 'bold'),
                 text_color="#334155").pack(pady=(15, 10), padx=15, anchor="w")

        button_frame = CTkFrame(scanner_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10, padx=15)

        buttons = [
            {"text": "Scan", "command": self.start_scan, "fg_color": "#691612"},
            {"text": "Check Existing", "command": self.scan_existing, "fg_color": "#BF3131"},
            {"text": "Clear Documents", "command": self.clear_scan, "fg_color": "#AC5353"}
        ]

        for cfg in buttons:
            CTkButton(button_frame,
                      text=cfg["text"],
                      command=cfg["command"],
                      fg_color=cfg["fg_color"],
                      hover_color="#550d0a",
                      text_color="#FFFFFF",
                      font=('Montserrat', 14),
                      height=40,
                      corner_radius=8).pack(fill="x", pady=5)

        # Scanner status
        self.status_label = CTkLabel(scanner_frame,
                                     text="Scanner disconnected",
                                     font=('Montserrat', 14),
                                     text_color="#64748B")
        self.status_label.pack(pady=5, padx=15, anchor="w")


    def _build_teacher_dropdown(self, parent):
        teacher_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        teacher_frame.pack(fill="x", pady=10)

        CTkLabel(teacher_frame, text="Select Teacher",
                 font=('Montserrat', 16, 'bold'),
                 text_color="#334155").pack(pady=(10, 5), padx=15, anchor="w")

        self.teacher_dropdown = CTkOptionMenu(
            teacher_frame, variable=self.teacher_var, values=["Loading..."],
            command=self.on_teacher_change,
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14), width=250, height=35
        )
        self.teacher_dropdown.pack(padx=15, pady=(10, 5))

        CTkLabel(teacher_frame, text="Select Subject",
                 font=('Montserrat', 14, 'bold'),
                 text_color="#334155").pack(pady=(5, 0), padx=15, anchor="w")

        self.subject_dropdown = CTkOptionMenu(
            teacher_frame, variable=self.subject_var, values=["No subjects"],
            command=self.on_subject_change,
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14), width=250, height=35, state="disabled"
        )
        self.subject_dropdown.pack(padx=15, pady=5)

        CTkLabel(teacher_frame, text="Select Block",
                 font=('Montserrat', 14, 'bold'),
                 text_color="#334155").pack(pady=(5, 0), padx=15, anchor="w")

        self.block_dropdown = CTkOptionMenu(
            teacher_frame, variable=self.block_var, values=["No blocks"],
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14), width=250, height=35, state="disabled"
        )
        self.block_dropdown.pack(padx=15, pady=(5, 10))


    def _build_results_panel(self, parent):
        results_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        results_frame.pack(fill="x", pady=10)

        CTkLabel(results_frame, text="Evaluation Results",
                 font=('Montserrat', 18, 'bold'),
                 text_color="#334155").pack(pady=(15, 10), padx=15, anchor="w")

        self.progress_bar = CTkProgressBar(results_frame, width=250, height=10,
                                           corner_radius=5, progress_color="#BF3131")
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)

        self.scan_info_label = CTkLabel(results_frame, text="No scan loaded",
                                        font=('Montserrat', 12), text_color="#64748B")
        self.scan_info_label.pack(anchor="w", padx=15, pady=5)

        # Action buttons
        action_frame = CTkFrame(results_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=10, padx=15)

        self.process_button = CTkButton(action_frame, text="Process Evaluation",
                                        command=self.process_scan,
                                        fg_color="#94A3B8", state="disabled")
        self.process_button.pack(fill="x", pady=5)

        self.save_button = CTkButton(action_frame, text="Save Results",
                                     command=self.save_result,
                                     fg_color="#94A3B8", state="disabled")
        self.save_button.pack(fill="x", pady=5)


    def _build_preview_panel(self, parent):
        preview_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        preview_frame.pack(fill="both", expand=True)

        CTkLabel(preview_frame, text="Document Preview",
                 font=('Montserrat', 18, 'bold'), text_color="#334155").pack(pady=(15, 0))

        self.document_listbox = CTkOptionMenu(
            preview_frame, values=["No documents loaded"],
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14), width=250, height=35
        )
        self.document_listbox.pack(padx=20, pady=10, fill="x")

        self.img_label = CTkLabel(preview_frame, text="No image loaded",
                                  font=('Montserrat', 14),
                                  fg_color="#555555", width=400, height=500)
        self.img_label.pack(padx=10, pady=20, fill="both", expand=True)


    # ---------------- DB HANDLERS ---------------- #
    def load_teachers(self):
        try:
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT f.id, f.name FROM teaching_assignments ta "
                    "JOIN faculty f ON ta.faculty_id = f.id ORDER BY f.name"
                ).fetchall()
            if rows:
                self.teacher_name_to_id = {name: fid for fid, name in rows}
                names = list(self.teacher_name_to_id.keys())
                self.teacher_dropdown.configure(values=names)
                self.teacher_dropdown.set(names[0])
                self.on_teacher_change(names[0])
            else:
                self.teacher_dropdown.configure(values=["No assigned teachers"])
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    def on_teacher_change(self, teacher_name):
        """Load subjects when teacher changes."""
        fid = self.teacher_name_to_id.get(teacher_name)
        if not fid: return

        try:
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT s.id, s.code, s.name FROM teaching_assignments ta "
                    "JOIN subjects s ON ta.subject_id = s.id "
                    "WHERE ta.faculty_id = ? ORDER BY s.code", (fid,)
                ).fetchall()
            if rows:
                self.subject_code_to_id = {code: sid for sid, code, name in rows}
                values = [f"{code} - {name}" for sid, code, name in rows]
                self.subject_dropdown.configure(values=values, state="normal")
                self.subject_dropdown.set(values[0])
                self.on_subject_change(values[0])
            else:
                self.subject_dropdown.configure(values=["No subjects"], state="disabled")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    def on_subject_change(self, subject_label):
        if not subject_label or " - " not in subject_label: return
        code = subject_label.split(" - ")[0]
        sid = self.subject_code_to_id.get(code)
        fid = self.teacher_name_to_id.get(self.teacher_var.get())

        try:
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT b.id, b.year_level, b.section FROM teaching_assignments ta "
                    "JOIN blocks b ON ta.block_id = b.id "
                    "WHERE ta.faculty_id = ? AND ta.subject_id = ? "
                    "ORDER BY b.year_level, b.section", (fid, sid)
                ).fetchall()
            if rows:
                self.block_label_to_id = {f"Year {y} - Section {s}": bid for bid, y, s in rows}
                values = list(self.block_label_to_id.keys())
                self.block_dropdown.configure(values=values, state="normal")
                self.block_dropdown.set(values[0])
            else:
                self.block_dropdown.configure(values=["No blocks"], state="disabled")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    # ---------------- SCANNER ACTIONS ---------------- #
    def start_scan(self):
        def worker():
            try:
                # Initialize COM for this thread
                pythoncom.CoInitialize()

                teacher = self.teacher_var.get()
                scanner = WIAScanner(teacher_name=teacher) 
                info = scanner.initialize()
                self.status_label.configure(text=f"Scanner detected: {info['name']}")
                pages = scanner.scan_batch()

                if pages > 0:
                    results = self.process_work_folder(teacher)
                    if results:
                        self.processed_results.update(results)   # temporary hold new
                        self.save_results()  # merges with pickle + updates memory
                        self.update_preview(results.get(teacher, []))
                    self.status_label.configure(text="Processing complete!")
                else:
                    self.status_label.configure(text="No documents found.")

            except Exception as e:
                messagebox.showerror("Scan Error", str(e))

            finally:
                # Always uninitialize COM when done
                pythoncom.CoUninitialize()

        threading.Thread(target=worker, daemon=True).start()


    def scan_existing(self):
        teacher = self.teacher_var.get()
        results = self.process_work_folder(teacher)
        self.save_results_to_json()
        if results:
            self.processed_results.update(results)
            
            
            self.update_preview(results.get(teacher, []))
            

            



    def clear_scan(self):
        self.img_label.configure(image=None, text="No image loaded")
        self.document_listbox.configure(values=["No documents loaded"])
        self.processed_results.clear()


    # ---------------- PROCESS & SAVE ---------------- #
    def process_scan(self):
        if not self.processed_results:
            messagebox.showwarning("Warning", "No scan found.")
            return
        self.progress_bar.set(1.0)
        messagebox.showinfo("Done", "Evaluation processed successfully!")


    def save_result(self):
        if not self.processed_results:
            messagebox.showwarning("Warning", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")])
        if not path: return
        try:
            rows = []
            for teacher, docs in self.processed_results.items():
                for file, result in docs:
                    row = {"Teacher": teacher, "File": file}
                    for sec, sec_data in result.items():
                        for rownum, score in sec_data.items():
                            row[f"{sec} Row {rownum}"] = score
                    rows.append(row)
            df = pd.DataFrame(rows)
            if path.endswith(".csv"): df.to_csv(path, index=False)
            else: df.to_excel(path, index=False)
            messagebox.showinfo("Saved", f"Results saved to {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))


    def process_work_folder(self, teacher):
        folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Scan", teacher)
        new_results = []

        # Get last time just for this teacher
        last_time = self.last_processed_times.get(teacher, 0)

        for file in os.scandir(folder):
            if not file.name.lower().endswith(".bmp"):
                continue

            if file.stat().st_mtime <= last_time:
                continue  # skip already processed

            filepath = os.path.join(folder, file.name)
            img = cv2.imread(filepath)

            # process sections now returns (scores, annotated_img)
            result_dict, annotated_img = main_code.process_sections(img)

            # store only filename + results in pickle-ready structure
            new_results.append((file.name, result_dict))

            # cache annotated image just for this session
            self.annotated_cache[file.name] = annotated_img

            # update tracker for this teacher only
            self.last_processed_times[teacher] = max(last_time, file.stat().st_mtime)

        return {teacher: new_results}



    def save_results(self, path="results.pkl"):
        try:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    old_data = pickle.load(f)
                old_results = old_data.get("results", {})
                old_times = old_data.get("last_processed_times", {})
            else:
                old_results, old_times = {}, {}

            # Merge teacher results
            for teacher, docs in self.processed_results.items():
                if teacher not in old_results:
                    old_results[teacher] = []
                existing_files = {fname for fname, *_ in old_results[teacher]}
                for fname, result in docs:
                    if fname not in existing_files:
                        old_results[teacher].append((fname, result))

            # Merge per-teacher last processed times
            old_times.update(self.last_processed_times)

            data = {
                "results": old_results,
                "last_processed_times": old_times
            }
            with open(path, "wb") as f:
                pickle.dump(data, f)

            self.processed_results = old_results
            self.last_processed_times = old_times
            print(f"✅ Results saved with per-teacher tracking to {os.path.abspath(path)}")

        except Exception as e:
            print(f"❌ Error saving results: {e}")
            
    def load_results(self, path="results.pkl"):
        if not os.path.exists(path):
            print("⚠️ No saved results found.")
            return

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            self.processed_results = data.get("results", {})
            self.last_processed_times = data.get("last_processed_times", {})

            print(f"✅ Results loaded from {os.path.abspath(path)}")
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            self.processed_results = {}
            self.last_processed_times = {}




            
    #---------------- PREVIEW HANDLERS ---------------- #
    def update_preview(self, teacher_results):
        if not teacher_results:
            self.document_listbox.configure(values=["No documents loaded"])
            self.img_label.configure(image=None, text="No image loaded")
            return
        values = [f for f, *_ in teacher_results]
        self.document_listbox.configure(values=values)
        self.document_listbox.set(values[0])
        self.display_image(values[0], self.teacher_var.get())


    def display_image(self, filename, teacher):
        if filename in self.annotated_cache:
            # ✅ use session-only annotated version
            rgb_img = cv2.cvtColor(self.annotated_cache[filename], cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img).resize((400, 500), Image.Resampling.LANCZOS)
        else:
            # fallback to raw file
            folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Scan", teacher)
            path = os.path.join(folder, filename)
            pil_img = Image.open(path).resize((400, 500), Image.Resampling.LANCZOS)

        img_tk = CTkImage(light_image=pil_img, dark_image=pil_img, size=(400, 500))
        self.img_label.configure(image=img_tk, text="")
        self.img_label.image = img_tk

