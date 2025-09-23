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

        self.content_frame = CTkFrame(self.master, fg_color="#F8F9FA")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        layout = CTkFrame(self.content_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        # Build teacher tabs (pack inside layout)
        self._build_tabs(layout)

        # Bottom controls (also pack inside layout)
        bottom_controls = CTkFrame(layout, fg_color="transparent")
        bottom_controls.pack(fill="x", pady=10)
        self._build_controls(bottom_controls)

    def _build_tabs(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

        # If no results, show a message
        if not self.processed_results:
            CTkLabel(parent, text="No results available").pack(pady=20)
            return

        # Create a tabview (like tabs at the top)
        self.tabview = CTkTabview(parent, width=800, height=500)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Loop over teacher names
        for teacher_name, _ in self.processed_results.items():
            tab = self.tabview.add(teacher_name)
            self._build_table(tab, teacher_name)

        # Set the first teacher as current
        if self.processed_results:
            self.current_teacher = self.tabview.get()

        # Bind tab change to update current_teacher
        def on_tab_change():
            # Get currently selected tab name
            self.current_teacher = self.tabview.get()

        self.tabview.configure(command=on_tab_change)

    def _build_table(self, parent, teacher_name):
        # Clear tab before building table
        for widget in parent.winfo_children():
            widget.destroy()

        teacher_data = self.processed_results.get(teacher_name, [])
        if not teacher_data:
            CTkLabel(parent, text="No results available").pack(pady=20)
            return

        # ---------- Headers ----------
        headers = ["Section/Row"]
        for idx, (filename, result, *_) in enumerate(teacher_data):
            headers.append(f"Doc {idx+1}")


        table_data = [headers]

        # ---------- Collect all section-row keys ----------
        all_rows = set()
        for _, result, *_ in teacher_data:
            for section, rows in result.items():
                for rownum in rows.keys():
                    all_rows.add(f"{section} R{rownum}")

        all_rows = sorted(all_rows)

        # ---------- Fill table ----------
        for row_key in all_rows:
            row_data = [row_key]
            for _, result, *_ in teacher_data:
                section, rownum = row_key.split(" R")
                rownum = int(rownum)
                score = result.get(section, {}).get(rownum, "")
                row_data.append(score if score != "" else 0)
            table_data.append(row_data)

        # ---------- Add totals ----------
        totals = ["Total"]
        for _, result, *_ in teacher_data:
            total_score = sum(sum(rows.values()) for rows in result.values())
            totals.append(total_score)
        table_data.append(totals)

        # ---------- Create CTkTable ----------
        table = CTkTable(
        parent,
        row=len(table_data),
        column=len(table_data[0]),
        values=table_data,
        header_color="#691612",       # dark crimson header
        hover_color="#BF3131",        # red hover
        colors=["#FFFFFF", "#F8F9FA"],  # alternating row colors
        color_phase="horizontal",     # alternate across rows
        corner_radius=8,
        justify="center"              # center text in cells
        )
        table.pack(expand=True, fill="both", padx=10, pady=10)


        return table
    
    def _build_controls(self, parent):
        control_frame = CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)

        load_btn = CTkButton(control_frame, text="print average", command=self.show_average_window)
        load_btn.pack(side="left", padx=5)
    
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

    