from customtkinter import *
from CTkTable import *
from tkinter import filedialog, messagebox
import pandas as pd
import os
from tksheet import Sheet   # make sure you have tksheet installed
import pickle


class ResultsPage:
    def __init__(self, master, processed_results):
        self.master = master
        self.processed_results = processed_results
        self.tab_buttons = []
        
        self.load_results()
        print("Loaded results:", self.processed_results)
        self._build_ui()
        

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.content_frame = CTkFrame(self.master, fg_color="#F8F9FA")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        layout = CTkFrame(self.content_frame, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=10, pady=10)
        layout.grid_rowconfigure(0, weight=1)

        # Build teacher tabs (each tab gets its own table)
        self._build_tabs(layout)

    
    def _build_tabs(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

        # If no results, show a message
        if not self.processed_results:
            CTkLabel(parent, text="No results available").pack(pady=20)
            return

        # Create a tabview (like tabs at the top)
        tabview = CTkTabview(parent, width=800, height=500)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Loop over teacher names
        for teacher_name, _ in self.processed_results.items():
            # Create a tab for each teacher
            tab = tabview.add(teacher_name)

            # Build a results table for this teacher
            self._build_table(tab, teacher_name)
        
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