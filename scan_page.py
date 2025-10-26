from customtkinter import *
from PIL import Image, ImageTk
from customtkinter import CTkImage
import pickle
import os
from tkinter import messagebox, filedialog
import main_code
import pandas as pd
import cv2, numpy as np, os, threading
from scanner import WIAScanner
import db
import pythoncom
from utils import set_sidebar_state
import utils
import datetime

class ScanPage:
    def __init__(self, master, processed_results):
        """Initialize the Scan Page inside a given frame."""
        self.master = master
        self.processed_results = processed_results
        self.last_processed_times = {}
        self.annotated_cache = {}  # Cache for annotated images
        self.current_scan_dir = None
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

        # --- Teacher selection ---
        CTkLabel(
            teacher_frame, text="Select Teacher",
            font=('Montserrat', 16, 'bold'),
            text_color="#334155"
        ).pack(pady=(10, 5), padx=15, anchor="w")

        self.teacher_dropdown = CTkOptionMenu(
            teacher_frame, variable=self.teacher_var, values=["Loading..."],
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14),
            width=250, height=35
        )
        self.teacher_dropdown.pack(padx=15, pady=(10, 5))

        # --- Rater type selection ---
        CTkLabel(
            teacher_frame, text="Select Rater Type",
            font=('Montserrat', 16, 'bold'),
            text_color="#334155"
        ).pack(pady=(10, 5), padx=15, anchor="w")

        self.rater_var = StringVar(value="Student")  # default option
        self.rater_dropdown = CTkOptionMenu(
            teacher_frame, variable=self.rater_var,
            values=["Student", "Peer", "Self"],
            fg_color="#BF3131", button_color="#691612",
            text_color="#FFFFFF", font=('Montserrat', 14),
            width=250, height=35
        )
        self.rater_dropdown.pack(padx=15, pady=(10, 5))
        self.teacher_dropdown.configure(command=lambda _: self._refresh_teacher_progress())



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
                                     command=self.save_csv,
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

        # ⬇️ Restore the preview label (this is what was missing)
        self.img_label = CTkLabel(
            preview_frame, text="No image loaded",
            font=('Montserrat', 14), fg_color="#555555",
            width=400, height=500
        )
        self.img_label.pack(padx=10, pady=20, fill="both", expand=True)

        # When user picks a file, update the preview
        self.document_listbox.configure(
            command=lambda choice: self.display_image(
                choice, self.teacher_var.get(), base_dir=self.current_scan_dir
            )
        )



    # ---------------- DB HANDLERS ---------------- #
    def load_teachers(self):
        try:
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT id, full_name FROM faculty ORDER BY full_name"
                ).fetchall()

            if rows:
                # Map teacher full_name → faculty_id
                self.teacher_name_to_id = {full_name: fid for fid, full_name in rows}
                names = list(self.teacher_name_to_id.keys())

                self.teacher_dropdown.configure(values=names)
                self.teacher_dropdown.set(names[0])
            else:
                self.teacher_dropdown.configure(values=["No teachers found"])

        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    #
    def _infer_ay_and_sem_from_today(self):
        now = datetime.datetime.now()
        y, m = now.year, now.month
        if 8 <= m <= 12:
            return f"{y}-{y+1}", "1st"
        elif 1 <= m <= 6:
            return f"{y-1}-{y}", "2nd"
        else:
            return f"{y-1}-{y}", "Summer"

    def _get_teacher_department(self, teacher_full_name: str) -> str | None:
        try:
            with db.connect() as conn:
                row = conn.execute("""
                    SELECT d.name
                    FROM faculty f
                    JOIN departments d ON d.id = f.department_id
                    WHERE f.full_name = ?
                """, (teacher_full_name,)).fetchone()
            return row[0] if row else None
        except Exception:
            return None

    def _build_scan_dir(self, teacher_full_name: str) -> str:
        dept = self._get_teacher_department(teacher_full_name) or "UnknownDept"
        ay, sem = self._infer_ay_and_sem_from_today()
        folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Scan", dept, ay, sem, teacher_full_name)
        os.makedirs(folder, exist_ok=True)
        return folder



    # ---------------- SCANNER ACTIONS ---------------- #
    def start_scan(self):
        def worker():
            try:
                pythoncom.CoInitialize()
                teacher = self.teacher_var.get()
                scan_dir = self._build_scan_dir(teacher)
                self.current_scan_dir = scan_dir
                start_idx = self._next_scan_index(scan_dir)

                # session log: scan_started
                user = utils.get_current_user()
                db.log_activity(
                    action="scan_started",
                    actor_name=user.get("name"),
                    actor_role=user.get("role"),
                    department_id=user.get("department_id"),
                    teacher_name=teacher,
                    rater_type=self.rater_var.get() if hasattr(self, "rater_var") else None
                )

                scanner = WIAScanner(teacher_name=teacher, output_dir=scan_dir)
                info = scanner.initialize()
                self.status_label.configure(text=f"Scanner detected: {info['name']}")

                pages = scanner.scan_batch()

                if pages > 0:
                    results, qc_errors = self.process_work_folder(teacher, base_dir=scan_dir)

                    # Show one message if there were any rejected pages
                    if qc_errors:
                        lines = [f"• {fname} → {reason}" for fname, reason in qc_errors]
                        messagebox.showerror(
                            "Incomplete / Blank Pages Detected",
                            "The following documents have missing keys and were discarded:\n\n"
                            + "\n".join(lines)
                            + "\n\nPlease rescan those page(s)."
                        )

                    if results:
                        # merge into in-memory results + persist
                        self.processed_results.update(results)
                        self.save_results()
                        self._refresh_teacher_progress()


                        # preview only for current rater (if any clean files)
                        rater = self.rater_var.get() if hasattr(self, "rater_var") else "Unknown"
                        teacher_files = results.get(teacher, {}).get(rater, [])
                        if teacher_files:
                            self.update_preview(teacher_files)

                    # session log: scan_completed
                    db.log_activity(
                        action="scan_completed",
                        actor_name=user.get("name"),
                        actor_role=user.get("role"),
                        department_id=user.get("department_id"),
                        teacher_name=teacher,
                        rater_type=self.rater_var.get() if hasattr(self, "rater_var") else None,
                        details={"pages_scanned": int(pages)}
                    )

                    # status label
                    if not results and not qc_errors:
                        self.status_label.configure(text="No new documents found.")
                        self.set_controls_state("normal")
                        set_sidebar_state("normal")
                    else:
                        self.status_label.configure(text="Processing complete!")
                        self.set_controls_state("normal")
                        set_sidebar_state("normal")
                else:
                    self.status_label.configure(text="No documents found.")
                    self.set_controls_state("normal")
                    set_sidebar_state("normal")

            except Exception as e:
                messagebox.showerror("Scan Error", str(e))
            finally:
                pythoncom.CoUninitialize()
                self.set_controls_state("normal")
                if hasattr(self, "wait_popup") and self.wait_popup.winfo_exists():
                    self.wait_popup.destroy()




        # ✅ disable controls and show popup
        self.set_controls_state("disabled")
        set_sidebar_state("disabled")
        self.wait_popup = CTkToplevel(self.master)
        self.wait_popup.title("Please Wait")

        # desired popup size
        popup_w, popup_h = 300, 120

        # get screen size
        screen_w = self.wait_popup.winfo_screenwidth()
        screen_h = self.wait_popup.winfo_screenheight()

        # calculate x, y for centering
        x = (screen_w // 2) - (popup_w // 2)
        y = (screen_h // 2) - (popup_h // 2)

        # set geometry with position
        self.wait_popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        # optional: disable resizing
        self.wait_popup.resizable(False, False)

        self.wait_popup.grab_set()
        CTkLabel(
            self.wait_popup,
            text="Scanning in progress...\nPlease wait.",
            font=("Roboto", 14),
            text_color="#374151"
        ).pack(expand=True, pady=30)

        threading.Thread(target=worker, daemon=True).start()


    def scan_existing(self):
        teacher = self.teacher_var.get()
        scan_dir = self._build_scan_dir(teacher)
        self.current_scan_dir = scan_dir
        results, qc_errors = self.process_work_folder(teacher, base_dir=scan_dir)
        if qc_errors:
            lines = [f"• {fname} → {reason}" for fname, reason in qc_errors]
            messagebox.showerror("Incomplete / Blank Pages Detected", "\n".join(lines))
        if results:
            self.processed_results.update(results)
            rater = self.rater_var.get() if hasattr(self, "rater_var") else "Unknown"
            self.update_preview(results.get(teacher, {}).get(rater, []))

    def clear_scan(self):
        self.img_label.configure(image=None, text="No image loaded")
        self.document_listbox.configure(values=["No documents loaded"])
        self.processed_results.clear()

    # ---------------- PROCESSING---------------- #
    def _qc_check_page(self, result_dict):
        """
        Returns (is_ok, page_blank, missing_map, total_detected)
        - is_ok = True only if all 4 sections have complete rows (1..5)
        - page_blank = True if nothing detected
        - missing_map = {section: [missing rows]}
        """
        expected = {"Section 1": 5, "Section 2": 5, "Section 3": 5, "Section 4": 5}
        missing_map = {}
        total_detected = 0

        for sec, n in expected.items():
            got = set(result_dict.get(sec, {}).keys())
            total_detected += len(got)
            missing = sorted(set(range(1, n + 1)) - got)
            missing_map[sec] = missing

        page_blank = (total_detected == 0)
        # A page is OK only if no section has missing rows
        is_ok = (not page_blank) and all(len(m) == 0 for m in missing_map.values())
        return is_ok, page_blank, missing_map, total_detected

    def process_scan(self):
        if not self.processed_results:
            messagebox.showwarning("Warning", "No scan found.")
            return
        self._refresh_teacher_progress()
        messagebox.showinfo("Done", "Evaluation processed successfully!")

    def process_work_folder(self, teacher, base_dir=None):
        folder = base_dir or self._build_scan_dir(teacher)
        # key by absolute folder path so AY/Sem/Dept are naturally separated
        key = os.path.abspath(folder)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        new_results = []
        qc_errors = []
        last_time = self.last_processed_times.get(key, 0)


        # --- use dropdown rater type ---
        rater = self.rater_var.get() if hasattr(self, "rater_var") else "Unknown"

        for file in os.scandir(folder):
            if not file.name.lower().endswith(".bmp"):
                continue
            if file.stat().st_mtime <= last_time:
                continue

            filepath = os.path.join(folder, file.name)
            img = cv2.imread(filepath)

            result_dict, annotated_img = main_code.process_sections(img)

            # ---- QC check for blanks/incomplete ----
            is_ok, page_blank, missing_map, total_detected = self._qc_check_page(result_dict)

            if not is_ok:
                # Build a readable reason
                if page_blank:
                    reason = "no marks detected"
                else:
                    summary = "; ".join(f"{sec} missing {','.join(map(str, miss))}"
                                        for sec, miss in missing_map.items() if miss)
                    reason = f"incomplete ({summary})"

                qc_errors.append((file.name, reason))

                # Delete the bad image so it won't linger
                try:
                    os.remove(filepath)
                except Exception:
                    pass

                # DO NOT add to new_results nor update last_processed_times for this file
                continue

            # ---- Keep only clean pages ----
            new_results.append((file.name, result_dict))
            self.annotated_cache[os.path.join(folder, file.name)] = annotated_img
            self.last_processed_times[key] = max(last_time, file.stat().st_mtime)

        # ✅ Special rule: only one "Self" entry per teacher
        if rater == "Self":
            if len(new_results) > 1:
                # Keep only the first scanned result
                kept = new_results[0:1]
                # Append to QC errors for visibility
                for extra in new_results[1:]:
                    qc_errors.append((extra[0], "Self evaluation allows only one page (discarded)"))
                    # Also delete extra images if they still exist (should exist because passed QC)
                    extra_path = os.path.join(folder, extra[0])
                    try:
                        os.remove(extra_path)
                    except Exception:
                        pass
                new_results = kept

            existing = self.processed_results.get(teacher, {}).get("Self", [])
            if existing:
                overwrite = messagebox.askyesno(
                    "Overwrite Self Evaluation",
                    f"A self-evaluation already exists for {teacher}.\nDo you want to overwrite it?"
                )
                if overwrite:
                    # overwrite with new (clean) results
                    return ({teacher: {"Self": new_results}} if new_results else {}), qc_errors
                else:
                    return ({}, qc_errors)

        # Normal case: return clean results only
        return ({teacher: {rater: new_results}} if new_results else {}), qc_errors



    # ---------------- RESULT HANDLERS ---------------- #

    def save_results(self, path=None):
        try:
            # 🔹 default path = same folder as database
            if path is None:
                db_path = db.get_default_db_path()
                base_dir = os.path.dirname(db_path)
                path = os.path.join(base_dir, "results.pkl")

            if os.path.exists(path):
                with open(path, "rb") as f:
                    old_data = pickle.load(f)
                old_results = old_data.get("results", {})
                old_times = old_data.get("last_processed_times", {})
            else:
                old_results, old_times = {}, {}

            # --- merge new results ---
            for teacher, rater_dict in self.processed_results.items():
                # 🔑 Normalize flat list → wrap as "Unknown"
                if isinstance(rater_dict, list):
                    rater_dict = {"Unknown": rater_dict}

                if teacher not in old_results:
                    old_results[teacher] = {}

                for rater, docs in rater_dict.items():
                    if rater not in old_results[teacher]:
                        old_results[teacher][rater] = []

                    existing_files = {fname for fname, *_ in old_results[teacher][rater]}
                    for fname, result in docs:
                        if fname not in existing_files:
                            old_results[teacher][rater].append((fname, result))

            # merge last processed times
            old_times.update(self.last_processed_times)

            data = {
                "results": old_results,
                "last_processed_times": old_times
            }
            with open(path, "wb") as f:
                pickle.dump(data, f)

            self.processed_results = old_results
            self.last_processed_times = old_times

            print(f"✅ Results saved to {os.path.abspath(path)}")

        except Exception as e:
            print(f"❌ Error saving results: {e}")

    def save_csv(self):
        if not self.processed_results:
            messagebox.showwarning("Warning", "Nothing to save.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")]
        )
        if not path:
            return

        try:
            rows = []
            for teacher, rater_dict in self.processed_results.items():
                # normalize old flat format -> wrap as Unknown
                if isinstance(rater_dict, list):
                    rater_dict = {"Unknown": rater_dict}

                for rater, docs in rater_dict.items():
                    for file, result in docs:
                        row = {"Teacher": teacher, "Rater": rater, "File": file}
                        for sec, sec_data in result.items():
                            for rownum, score in sec_data.items():
                                row[f"{sec} Row {rownum}"] = score
                        rows.append(row)

            df = pd.DataFrame(rows)
            if path.endswith(".csv"):
                df.to_csv(path, index=False)
            else:
                df.to_excel(path, index=False)

            messagebox.showinfo("Saved", f"Results saved to {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _next_scan_index(self, folder: str) -> int:
        """Return next integer N so the next file can be named ..._{N:03d}.bmp."""
        import re
        max_n = 0
        if not os.path.exists(folder):
            return 1
        for entry in os.scandir(folder):
            if not entry.name.lower().endswith(".bmp"):
                continue
            # grab the last number before .bmp (works with page_12.bmp or Teacher_012.bmp)
            m = re.search(r'(\d+)(?=\.bmp$)', entry.name, flags=re.IGNORECASE)
            if m:
                max_n = max(max_n, int(m.group(1)))
        return max_n + 1

     
    def load_results(self, path=None):
        # 🔹 default path = same folder as database
        if path is None:
            db_path = db.get_default_db_path()
            base_dir = os.path.dirname(db_path)
            path = os.path.join(base_dir, "results.pkl")

        if not os.path.exists(path):
            print("⚠️ No saved results found.")
            self.processed_results = {}
            self.last_processed_times = {}
            return

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            self.processed_results = data.get("results", {})
            self.last_processed_times = data.get("last_processed_times", {})

            # 🔑 Normalize: wrap flat lists into {"Unknown": [...]}
            for teacher, val in list(self.processed_results.items()):
                if isinstance(val, list):
                    self.processed_results[teacher] = {"Unknown": val}

            print(f"✅ Results loaded from {os.path.abspath(path)}")
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            self.processed_results = {}
            self.last_processed_times = {}

   
    #---------------- PREVIEW HANDLERS ---------------- #
    def update_preview(self, teacher_results):
        if not teacher_results:
            self.document_listbox.configure(values=["No documents loaded"])
            self.document_listbox.set("No documents loaded")
            self.img_label.configure(image=None, text="No image loaded")
            return

        values = [fname for fname, *_ in teacher_results]
        self.document_listbox.configure(values=values)
        self.document_listbox.set(values[0])

        # ensure command is bound after repopulating
        self.document_listbox.configure(
            command=lambda choice: self.display_image(
                choice, self.teacher_var.get(), base_dir=self.current_scan_dir
            )
        )

        # load the first image immediately
        self.display_image(values[0], self.teacher_var.get(), base_dir=self.current_scan_dir)



    def display_image(self, filename, teacher, base_dir=None):
        try:
            folder = base_dir or self.current_scan_dir or self._build_scan_dir(teacher)
            full_path = os.path.join(folder, filename)

            if full_path in self.annotated_cache:
                rgb_img = cv2.cvtColor(self.annotated_cache[full_path], cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img).resize((400, 500), Image.Resampling.LANCZOS)
            else:
                pil_img = Image.open(full_path).resize((400, 500), Image.Resampling.LANCZOS)

            img_tk = CTkImage(light_image=pil_img, dark_image=pil_img, size=(400, 500))
            self.img_label.configure(image=img_tk, text="")
            self.img_label.image = img_tk  # prevent GC
        except Exception as e:
            self.img_label.configure(image=None, text="Error loading image")
            messagebox.showerror("Image Error", str(e))


    # ---------------- OTHERS ---------------- #
  
    def set_controls_state(self, state="normal"):
        """Enable or disable all buttons/menus in the scan page."""
        widgets = [
            self.process_button,
            self.save_button,
            self.teacher_dropdown,
            self.document_listbox,
            # add more if needed
        ]
        for w in widgets:
            try:
                w.configure(state=state)
            except Exception:
                pass
            
    def _get_expected_total_for_teacher(self, teacher_full_name: str) -> int:
        """Sum of expected_students across ALL teaching_assignments for the teacher."""
        try:
            with db.connect() as conn:
                row = conn.execute("""
                    SELECT COALESCE(SUM(ta.expected_students), 0)
                    FROM teaching_assignments ta
                    JOIN faculty f ON f.id = ta.teacher_id
                    WHERE f.full_name = ?
                """, (teacher_full_name,)).fetchone()
            return int(row[0] or 0)
        except Exception:
            return 0

    def _get_completed_student_scans_current_period(self, teacher_full_name: str) -> int:
        """
        Count Student scans for this teacher that are saved and belong to the CURRENT AY/Sem folder.
        We ensure the file exists under the current scan dir to scope to the period.
        """
        # where results.pkl is stored
        db_path = db.get_default_db_path()
        base_dir = os.path.dirname(db_path)
        pkl_path = os.path.join(base_dir, "results.pkl")

        if not os.path.exists(pkl_path):
            return 0

        try:
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            results = data.get("results", {})
        except Exception:
            return 0

        teacher_bucket = results.get(teacher_full_name, {})
        student_list = teacher_bucket.get("Student", [])
        if isinstance(teacher_bucket, list):
            # normalize legacy structure (shouldn’t happen here, but safe)
            student_list = []

        # Only count files that live in THIS period's folder to avoid cross-term inflation
        current_dir = self._build_scan_dir(teacher_full_name)
        count = 0
        for fname, _payload in student_list:
            if os.path.exists(os.path.join(current_dir, fname)):
                count += 1
        return count

    def _refresh_teacher_progress(self):
        """Recompute and update the progress bar + label for the selected teacher."""
        teacher = self.teacher_var.get()
        if not teacher or teacher in ("Loading...", "No teachers found"):
            self.progress_bar.set(0)
            self.scan_info_label.configure(text="No teacher selected")
            return

        total = self._get_expected_total_for_teacher(teacher)
        completed = self._get_completed_student_scans_current_period(teacher)
        remaining = max(total - completed, 0)

        progress = (completed / total) if total > 0 else 0.0
        self.progress_bar.set(progress)
        # e.g., “12 / 30 completed • 18 remaining”
        self.scan_info_label.configure(
            text=f"{completed} / {total} completed • {remaining} remaining"
        )
