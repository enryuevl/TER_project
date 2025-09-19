from customtkinter import *
from CTkTable import *
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
def show_teacher_results(self, teacher_name):
    # Clear previous content in sheet_container
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

    # Header frame for title, search, and export
    header_frame = CTkFrame(self.sheet_container, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(10, 15))

    CTkLabel(
        header_frame,
        text=f"{teacher_name}'s Evaluation Results",
        font=("Arial", 20, "bold"),
        text_color="#691612"
    ).pack(side="left")

    # Search frame
    search_frame = CTkFrame(header_frame, fg_color="transparent")
    search_frame.pack(side="right")

    CTkLabel(
        search_frame,
        text="Search:",
        font=("Arial", 14),
        text_color="#333333"
    ).pack(side="left", padx=(0, 10))

    search_entry = CTkEntry(
        search_frame,
        fg_color="#F8F9FA",
        border_color="#E9ECEF",
        text_color="#333333",
        corner_radius=5,
        width=200,
        height=32,
        placeholder_text="Search sections or scores..."
    )
    search_entry.pack(side="left", padx=(0, 10))

    # Export button
    def export_table():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")],
            initialfile=f"{teacher_name}_evaluation_results"
        )
        if file_path:
            df = pd.DataFrame(sheet_data)
            try:
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    export_btn = CTkButton(
        search_frame,
        text="Export CSV",
        command=export_table,
        fg_color="#691612",
        hover_color="#AC5353",
        text_color="#FFFFFF",
        font=("Arial", 12, "bold"),
        height=32,
        corner_radius=6
    )
    export_btn.pack(side="left")

    # Table container
    table_container = CTkFrame(self.sheet_container, fg_color="#FFFFFF", corner_radius=10)
    table_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Build table headers
    headers = ["Section/Row"]
    for idx, (filename, _) in enumerate(teacher_data):
        headers.append(f"Doc {idx + 1}")

    sheet_data = [headers]

    # Collect all row keys dynamically
    all_rows = {}
    for _, results in teacher_data:
        for section, rows in results.items():
            for row_num in rows.keys():
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

    # Add totals row
    total_row = ["Total"]
    for _, results in teacher_data:
        total = sum(sum(rows.values()) for rows in results.values())
        total_row.append(total)
    sheet_data.append(total_row)

    # Create CTkTable
    table = CTkTable(
        master=table_container,
        values=sheet_data,
        colors=["#F8F9FA", "#FFFFFF"],  # Alternating row colors
        header_color="#F8F9FA",  # Header background
        text_color="#333333",  # Body text
        hover_color="#BF3131",  # Selection background
        font=("Arial", 12),
        header_font=("Arial", 12, "bold"),
        corner_radius=8,
        border_width=1,
        border_color="#E9ECEF"  # Gridlines
    )

    # Style totals row
    for col in range(len(headers)):
        table.edit_cell(
            row=len(sheet_data) - 1,
            column=col,
            value=sheet_data[-1][col],
            fg_color="#F8F9FA",  # Light background for totals
            text_color="#691612"  # Bold text
        )

    # Conditional formatting
    def apply_conditional():
        for row_idx in range(1, len(sheet_data) - 1):  # Exclude header and total
            for col_idx in range(1, len(headers)):  # Skip section column
                value = sheet_data[row_idx][col_idx]
                if isinstance(value, (int, float)):
                    fg_color = "#333333"
                    bg_color = "#FFFFFF" if row_idx % 2 == 0 else "#F8F9FA"
                    if value < 50:
                        bg_color = "#EF4444"
                        fg_color = "#FFFFFF"
                    elif value > 90:
                        bg_color = "#22C55E"
                        fg_color = "#FFFFFF"
                    table.edit_cell(
                        row=row_idx,
                        column=col_idx,
                        value=value,
                        fg_color=fg_color,
                        bg_color=bg_color
                    )

    apply_conditional()

    # Right-align numerical columns
    for col in range(1, len(headers)):
        for row in range(len(sheet_data)):
            table.edit_cell(
                row=row,
                column=col,
                justify="right"  # Right-align numerical columns
            )

    # Search functionality
    def search_table(event):
        search_term = search_entry.get().lower()
        if not search_term:
            table.update_values(sheet_data)
            apply_conditional()
            return
        filtered_data = [sheet_data[0]]  # Keep headers
        filtered_data.extend([row for row in sheet_data[1:] if search_term in str(row[0]).lower()])
        table.update_values(filtered_data)
        apply_conditional()

    search_entry.bind("<KeyRelease>", search_table)

    # Pack the table
    table.pack(expand=True, fill="both", padx=10, pady=10)

    return table