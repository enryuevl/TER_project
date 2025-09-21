from customtkinter import *
from CTkTable import *
import pickle
import os


class ResultsPage:
    def __init__(self, master, processed_results):
        self.master = master
        self.processed_results = processed_results
        self.tab_buttons = []

        # Load saved results
        self.load_results()
        print("Loaded results:", self.processed_results)

        # Build UI
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

        # Build teacher tabs
        self._build_tabs(layout)

    def _build_tabs(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

        if not self.processed_results:
            CTkLabel(parent, text="No results available").pack(pady=20)
            return

        tabview = CTkTabview(parent, width=800, height=500)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        for teacher_name, _ in self.processed_results.items():
            tab = tabview.add(teacher_name)
            self._build_table(tab, teacher_name)

    def _build_table(self, parent, teacher_name):
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
                for row_num in rows.keys():
                    all_rows.add(f"{section} R{row_num}")
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

        # ---------- Totals ----------
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
            header_color="#691612",
            hover_color="#BF3131",
            colors=["#FFFFFF", "#F8F9FA"],
            color_phase="horizontal",
            corner_radius=8,
            justify="center"
        )
        table.pack(expand=True, fill="both", padx=10, pady=10)

        return table

    # ---------------- Logic ---------------- #
    def load_results(self, path="results.pkl"):
        """Load processed_results dict from pickle file."""
        if not os.path.exists(path):
            print("⚠️ No saved results found.")
            return {}

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            # only grab the results (ignore last_processed_times)
            self.processed_results = data.get("results", {})
            print(f"✅ Results loaded from {os.path.abspath(path)}")
            return self.processed_results
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return {}
