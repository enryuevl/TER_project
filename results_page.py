from customtkinter import *
from tkinter import filedialog, messagebox
import pandas as pd
import os
from tksheet import Sheet   # make sure you have tksheet installed


class ResultsPage:
    def __init__(self, master, processed_results):
        self.master = master
        self.processed_results = processed_results
        self.tab_buttons = []

        self._build_ui()

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        if not self.processed_results:
            CTkLabel(
                self.master,
                text="No results available. Please scan or process documents first.",
                font=('Montserrat', 16),
                text_color="black"
            ).pack(pady=20)
            return

        self.content_frame = CTkFrame(master=self.master, fg_color="#F8F9FA")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        tabs_frame = CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=10)
        tabs_frame.pack(fill="x", pady=(0, 5))

        self.tab_buttons_container = CTkFrame(tabs_frame, fg_color="transparent")
        self.tab_buttons_container.pack(fill="x", padx=10, pady=5)

        self.sheet_container = CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=10)
        self.sheet_container.pack(fill="both", expand=True)

        # Create teacher tabs
        for i, teacher in enumerate(self.processed_results.keys()):
            btn = CTkButton(
                self.tab_buttons_container,
                text=teacher,
                command=lambda name=teacher: self.show_teacher_results(name),
                fg_color="transparent" if i > 0 else "#691612",
                text_color="#475569" if i > 0 else "#FFFFFF",
                hover_color="#F1F5F9",
                width=150,
                height=35,
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons.append(btn)

        # Show first teacher by default
        first_teacher = next(iter(self.processed_results.keys()))
        self.show_teacher_results(first_teacher)

    # ---------------- Logic ---------------- #
    def show_teacher_results(self, teacher_name):
        for widget in self.sheet_container.winfo_children():
            widget.destroy()

        # Highlight the selected tab
        for btn in self.tab_buttons:
            if btn.cget("text") == teacher_name:
                btn.configure(fg_color="#691612", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#475569")

        teacher_data = self.processed_results.get(teacher_name, [])

        if not teacher_data:
            CTkLabel(
                self.sheet_container,
                text=f"No results available for {teacher_name}",
                font=('Montserrat', 14),
                text_color="#64748B"
            ).pack(pady=20)
            return

        # Build table headers
        headers = ["Section/Row"]
        for idx, (filename, _) in enumerate(teacher_data):
            headers.append(f"Doc {idx + 1}")

        sheet_data = [headers]

        # Collect all row keys dynamically
        all_rows = {}
        for _, results in teacher_data:
            for section, rows in results.items():
                for row_num in rows.keys():   # dynamically detect rows
                    row_key = f"{section} Row {row_num}"
                    if row_key not in all_rows:
                        all_rows[row_key] = []

        # Fill row data
        for row_key in sorted(all_rows.keys()):
            row_data = [row_key]
            for _, results in teacher_data:
                section = row_key.split(" Row ")[0]
                row_num = int(row_key.split(" Row ")[1])
                score = results.get(section, {}).get(row_num, "")
                row_data.append(score if score != "" else 0)
            sheet_data.append(row_data)

        # Add totals
        total_row = ["Total"]
        for _, results in teacher_data:
            total = sum(sum(rows.values()) for rows in results.values())
            total_row.append(total)
        sheet_data.append(total_row)

        # Display table
        table = Sheet(
            self.sheet_container,
            data=sheet_data[1:],   # skip header row
            headers=sheet_data[0],
            width=800,
            height=400
        )

        table.enable_bindings((
            "single_select", "row_select", "column_width_resize",
            "arrowkeys", "right_click_popup_menu", "rc_select", "copy"
        ))

        table.header_font(("Montserrat", 12, "bold"))
        table.font(("Montserrat", 12, "normal"))

        # Export button
        export_frame = CTkFrame(self.sheet_container, fg_color="transparent")
        export_frame.pack(fill="x", pady=5, padx=10)

        CTkButton(
            export_frame,
            text="Export Results",
            command=lambda: self.export_teacher_results(sheet_data, teacher_name),
            fg_color="#691612",
            hover_color="#550d0a",
            text_color="#FFFFFF",
            font=("Arial", 14),
            width=150,
            height=35,
            corner_radius=8
        ).pack(side="right", padx=10)

        table.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    def export_teacher_results(self, sheet_data, teacher_name):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")],
            initialfile=f"{teacher_name}_results"
        )
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    pd.DataFrame(sheet_data[1:], columns=sheet_data[0]).to_csv(file_path, index=False)
                else:
                    pd.DataFrame(sheet_data[1:], columns=sheet_data[0]).to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Results exported to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
