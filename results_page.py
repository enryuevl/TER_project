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


class ResultsPage:
    def __init__(self, master, processed_results):
        self.master = master
        self.processed_results = processed_results
        self.current_teacher = None
        self.tab_buttons = []
        
        self.load_results()
        self._build_ui()
        

# ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        # Main content frame with a modern light background
        self.content_frame = CTkFrame(self.master, fg_color="#F3F4F6")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Layout frame for tabs and table
        layout = CTkFrame(self.content_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        # Build teacher tabs
        self._build_tabs(layout)

        # Bottom controls
        bottom_controls = CTkFrame(layout, fg_color="transparent")
        bottom_controls.pack(fill="x", pady=10)
        self._build_controls(bottom_controls)

    def _build_tabs(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

        if not self.processed_results:
            CTkLabel(parent, text="No results available", font=("Roboto", 16), text_color="#374151").pack(pady=20)
            return

        # Tab navigation frame
        tab_frame = CTkFrame(parent, fg_color="transparent")
        tab_frame.pack(fill="x", padx=10, pady=5)

        self.tab_buttons = []
        for teacher_name in self.processed_results.keys():
            btn = CTkButton(
                tab_frame,
                text=teacher_name,
                command=lambda t=teacher_name: self._build_table(parent, t),
                fg_color="#DC2626",  # Red primary color
                hover_color="#B91C1C",  # Darker red on hover
                text_color="#FFFFFF",
                font=("Roboto", 14, "bold"),
                corner_radius=5
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons.append(btn)

        # Display the first teacher's table by default
        if self.processed_results:
            first_teacher = list(self.processed_results.keys())[0]
            self._build_table(parent, first_teacher)

    def _build_table(self, parent, teacher_name):
        # Clear previous table content but keep tab frame
        for widget in parent.winfo_children():
            if widget != parent.winfo_children()[0]:  # Preserve tab_frame
                widget.destroy()

        teacher_data = self.processed_results.get(teacher_name, [])
        if not teacher_data:
            CTkLabel(parent, text="No results available", font=("Roboto", 16), text_color="#374151").pack(pady=20)
            return

        # Headers
        headers = ["Section/Row"]
        for idx, (filename, result, *_) in enumerate(teacher_data):
            headers.append(f"Doc {idx+1}")

        table_data = [headers]

        # Collect all section-row keys
        all_rows = set()
        for _, result, *_ in teacher_data:
            for section, rows in result.items():
                for rownum in rows.keys():
                    all_rows.add(f"{section} R{rownum}")

        all_rows = sorted(all_rows)

        # Fill table
        for row_key in all_rows:
            row_data = [row_key]
            for _, result, *_ in teacher_data:
                section, rownum = row_key.split(" R")
                rownum = int(rownum)
                score = result.get(section, {}).get(rownum, "")
                row_data.append(score if score != "" else 0)
            table_data.append(row_data)

        # Add totals
        totals = ["Total"]
        for _, result, *_ in teacher_data:
            total_score = sum(sum(rows.values()) for rows in result.values())
            totals.append(total_score)
        table_data.append(totals)

        # Create CTkTable with modern styling
        table = CTkTable(
            parent,
            row=len(table_data),
            column=len(table_data[0]),
            values=table_data,
            header_color="#DC2626",  # Red primary color for header
            hover_color="#FECACA",  # Light red hover
            colors=["#FFFFFF", "#F9FAFB"],  # Clean white and light gray rows
            color_phase="horizontal",
            corner_radius=10,
            font=("Roboto", 12),
            text_color="#1F2937",  # Dark gray text for contrast
            justify="center"
        )
        table.pack(expand=True, fill="both", padx=10, pady=10)

        return table

    def _build_controls(self, parent):
        control_frame = CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)

        load_btn = CTkButton(
            control_frame,
            text="Load Results",
            command=self.load_results,
            fg_color="#DC2626",  # Red primary color
            hover_color="#B91C1C",  # Darker red on hover
            text_color="#FFFFFF",
            font=("Roboto", 14),
            corner_radius=5
        )
        load_btn.pack(side="left", padx=5)

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
        
    def show_summary_window(self):
        #buray ni andrei (temporary at pag na select teacher nawawala buttons)
        #if not self.current_teacher:
            #messagebox.showwarning("No Teacher", "Please select a teacher first.")
            #return

        # Open new window with custom UI
        self._open_summary_popup()
        
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
        scroll_frame = CTkScrollableFrame(win, fg_color="#FFFFFF", label_font=("Roboto", 14, "bold"), label_text_color="#DC2626")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

         # Helper for consistent rows
        def add_row(parent, row_idx, label, percent=""):
            CTkLabel(parent, text=label, font=("Roboto", 12), text_color="#1F2937", anchor="w").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
            CTkEntry(parent, width=120, font=("Roboto", 12)).grid(row=row_idx, column=1, padx=5, pady=2)  # Rating
            CTkEntry(parent, width=150, font=("Roboto", 12)).grid(row=row_idx, column=2, padx=5, pady=2)  # Equivalent
            CTkLabel(parent, text=percent, font=("Roboto", 12), text_color="#1F2937", anchor="center").grid(row=row_idx, column=3, padx=5, pady=2)  # %
            CTkEntry(parent, width=120, font=("Roboto", 12)).grid(row=row_idx, column=4, padx=5, pady=2)  # Point

        #  Header 
        CTkLabel(scroll_frame, text="TEACHING EFFICIENCY RATING (TER) SCALE FORM",
                 font=("Roboto", 16, "bold"), text_color="#FFFFFF",
                 fg_color="#DC2626", corner_radius=6).pack(fill="x", pady=5)

        # === Instructor Info ===
        info_frame = CTkFrame(scroll_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=5)
        for lbl in ["Instructor:", "College:", "Rating Period:", "Department:"]:
            CTkLabel(info_frame, text=lbl, font=("Roboto", 12), text_color="#1F2937").pack(side="left", padx=5)
            CTkEntry(info_frame, width=150, font=("Roboto", 12)).pack(side="left", padx=10)

        # === Performance Section ===
        perf_frame = CTkFrame(scroll_frame, fg_color="transparent")
        perf_frame.pack(fill="x", pady=10)

        # Section title
        CTkLabel(perf_frame, text="I. PERFORMANCE (70%)", font=("Roboto", 14, "bold"),
                 text_color="#DC2626").grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Column headers
        headers = ["", "RATING", "RATING EQUIVALENT", "RATING %", "POINT SCORE"]
        for i, h in enumerate(headers):
            CTkLabel(perf_frame, text=h, font=("Roboto", 12, "bold"), text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

            # Rows
        CTkLabel(perf_frame, text="1. Instruction (55%)", font=("Roboto", 12, "bold"),
                 text_color="#DC2626").grid(row=2, column=0, sticky="w", pady=(0, 3))

        add_row(perf_frame, 3, "a) Student as Rater", "20%")
        add_row(perf_frame, 4, "b) Peer as Rater", "10%")
        add_row(perf_frame, 5, "c) Dean as Rater", "15%")
        add_row(perf_frame, 6, "d) Self as Rater", "10%")

        # Research
        CTkLabel(perf_frame, text="2. Research", font=("Roboto", 12, "bold"),
                 text_color="#DC2626").grid(row=7, column=0, sticky="w", pady=(5, 3))
        add_row(perf_frame, 8, "", "5%")

        # Extension Service
        CTkLabel(perf_frame, text="3. Extension Service", font=("Roboto", 12, "bold"),
                 text_color="#DC2626").grid(row=9, column=0, sticky="w", pady=(5, 3))
        add_row(perf_frame, 10, "", "5%")

        # Productivity
        CTkLabel(perf_frame, text="4. Productivity", font=("Roboto", 12, "bold"),
                 text_color="#DC2626").grid(row=11, column=0, sticky="w", pady=(5, 3))
        add_row(perf_frame, 12, "", "5%")

        # === Behavior Section ===
        behav_frame = CTkFrame(scroll_frame, fg_color="transparent")
        behav_frame.pack(fill="x", pady=10)

        CTkLabel(behav_frame, text="II. BEHAVIOR (30%)", font=("Roboto", 14, "bold"),
                 text_color="#DC2626").grid(row=0, column=0, sticky="w", pady=(0, 5))

        for i, h in enumerate(headers):
            CTkLabel(behav_frame, text=h, font=("Roboto", 12, "bold"), text_color="#1F2937").grid(row=1, column=i, padx=5, pady=2)

        add_row(behav_frame, 2, "1. Courtesy", "7.5%")
        add_row(behav_frame, 3, "2. Human Relations", "7.5%")
        add_row(behav_frame, 4, "3. Punctuality and Attendance", "7.5%")
        add_row(behav_frame, 5, "4. Initiative", "7.5%")
        add_row(behav_frame, 6, "5. Leadership (Supervisors only)", "5%")
        add_row(behav_frame, 7, "6. Stress Tolerance (Supervisors only)", "5%")

        # === Plus Factor ===
        plus_frame = CTkFrame(scroll_frame, fg_color="transparent")
        plus_frame.pack(fill="x", pady=10)

        CTkLabel(plus_frame, text="PLUS FACTOR (not to exceed one (1) credit point)",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").grid(row=0, column=0, sticky="w", pady=(0, 5))

        # === Summary Ratings ===
        summary_frame = CTkFrame(scroll_frame, fg_color="transparent")
        summary_frame.pack(fill="x", pady=10)

        CTkLabel(summary_frame, text="Overall Point Score", font=("Roboto", 12, "bold"), text_color="#1F2937").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        CTkEntry(summary_frame, width=120, font=("Roboto", 12)).grid(row=0, column=1, padx=5, pady=2)

        CTkLabel(summary_frame, text="Equivalent Numerical Rating", font=("Roboto", 12, "bold"), text_color="#1F2937").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        CTkEntry(summary_frame, width=120, font=("Roboto", 12)).grid(row=1, column=1, padx=5, pady=2)

        CTkLabel(summary_frame, text="Equivalent Adjective Rating", font=("Roboto", 12, "bold"), text_color="#1F2937").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        CTkEntry(summary_frame, width=120, font=("Roboto", 12)).grid(row=2, column=1, padx=5, pady=2)

        # === Descriptive Equivalent Table ===
        desc_frame = CTkFrame(scroll_frame, fg_color="transparent")
        desc_frame.pack(fill="x", pady=10)

        CTkLabel(desc_frame, text="Descriptive Equivalent of Numerical Ratings:",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")

        desc_list = [
            "93.8 & Above - Outstanding (O)",
            "75.5 - 92.0 - Very Satisfactory (VS)",
            "50.0 - 74.4 - Satisfactory (S)",
            "3.0 - 4.9 - Unsatisfactory (US)",
            "2.0 - 2.9 - Poor (P)"
        ]
        for text in desc_list:
            CTkLabel(desc_frame, text=text, font=("Roboto", 12), text_color="#1F2937").pack(anchor="w", padx=20)


        # === Comments Section ===
        comments_frame = CTkFrame(scroll_frame, fg_color="transparent")
        comments_frame.pack(fill="x", pady=10)

        CTkLabel(comments_frame, text="EMPLOYEE'S COMMENTS/REMARKS",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        CTkTextbox(comments_frame, height=50, width=900, font=("Roboto", 12)).pack(pady=5)

        CTkLabel(comments_frame, text="RATER'S COMMENTS/REMARKS",
                 font=("Roboto", 12, "bold"), text_color="#DC2626").pack(anchor="w")
        CTkTextbox(comments_frame, height=50, width=900, font=("Roboto", 12)).pack(pady=5)
        
        
    def show_average_window(self):
        print(self.current_teacher)
        if not self.current_teacher:
            messagebox.showwarning("No Teacher", "Please select a teacher first.")
            return

        # --- Get processed averages ---
        df = self._prepare_average_dataframe(self.current_teacher)
        if df is None or df.empty:
            messagebox.showinfo("No Data", "No scores available for this teacher.")
            return

        # --- Build UI window ---
        self._open_average_popup(df)

    def _open_average_popup(self, df):
        """Open a popup window and show averages DataFrame in a tksheet table."""
        win = CTkToplevel(self.master)
        win.title(f"Averages - {self.current_teacher}")
        win.geometry("600x400")

        win.transient(self.master)
        win.grab_set()
        win.focus_force()
        win.lift()

        # Add tksheet table
        sheet = Sheet(win, data=df.values.tolist(), headers=df.columns.tolist())
        sheet.pack(fill="both", expand=True, padx=10, pady=10)

        sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "row_height_resize",
            "arrowkeys",
            "copy",
        ))

        # Buttons
        CTkButton(win, text="Close", command=win.destroy).pack(pady=5)
        CTkButton(win, text="open summary", command=lambda: self.open_excel_in_sheet()).pack(pady=5)
    
    # ---------------- Logic ---------------- #
    def load_results(self, path="results.pkl"):
        """Load processed_results dict from a pickle file."""
        if not os.path.exists(path):
            print("⚠️ No saved results found.")
            return {}

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            # If saved with wrapper
            if "results" in data:
                self.processed_results = data["results"]
            else:
                self.processed_results = data

        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return {}
    
    def calculate_row_averages(self, teacher_name):
        teacher_data = self.processed_results.get(teacher_name, [])
        if not teacher_data:
            return {}

        row_scores = {}

        # Collect all rows for all documents
        for _, result, *_ in teacher_data:
            for section, rows in result.items():
                for rownum, score in rows.items():
                    row_key = f"{section} R{rownum}"
                    row_scores.setdefault(row_key, []).append(score)

        # Compute averages
        averages = {}
        for row_key, scores in row_scores.items():
            if scores:
                averages[row_key] = sum(scores) / len(scores)

        return averages # return dict of row_key -> average score

    def print_row_averages(self):
        if not self.current_teacher:
            print("⚠️ No teacher selected")
            return
        
        averages = self.calculate_row_averages(self.current_teacher)
        print(f"\n📊 Row Averages for {self.current_teacher}:")
        for row_key, avg in averages.items():
            print(f"  {row_key}: {avg:.2f}")
    
    def _prepare_average_dataframe(self, teacher_name):
        """Compute averages per row, section totals, and grand total, return as DataFrame."""
        averages = self.calculate_row_averages(teacher_name)
        if not averages:
            return None

        # Group averages by section
        section_rows = {}
        for row_key, avg in averages.items():
            section = " ".join(row_key.split()[:2])  # "Section 1"
            section_rows.setdefault(section, []).append((row_key, avg))

        # Build structured data
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

        return pd.DataFrame(data, columns=["Row", "Average Score", "Section Total"])
    

    