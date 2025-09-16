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

        # Header frame for title, search, and export (like database viewer)
        header_frame = CTkFrame(self.sheet_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 15))

        CTkLabel(
            header_frame,
            text=f"{teacher_name}'s Evaluation Results",
            font=("Arial", 20, "bold"),
            text_color="#691612"  # Theme primary
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
            fg_color="#F8F9FA",  # Theme light bg
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
            fg_color="#691612",  # Theme primary
            hover_color="#AC5353",  # Theme secondary
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
                for row_num in rows.keys():  # Dynamically detect rows
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

        # Create styled Sheet
        sheet = Sheet(
            table_container,  # Parent is the new CTkFrame
            data=sheet_data[1:],  # Skip header for data
            headers=sheet_data[0],
            width=800,
            height=400,
            # Theme-based colors
            header_bg="#F8F9FA",  # Light bg like Treeview headings
            header_fg="#691612",  # Primary text color
            table_bg="#FFFFFF",   # White cells
            table_fg="#333333",   # Body text
            selected_row_bg="#BF3131",  # Selection bg like Treeview
            selected_row_fg="#FFFFFF",  # Selection text
            grid_color="#E9ECEF",  # Subtle gridlines
            align="w",  # Left align by default
            show_row_index=False,  # Hide row index
            font=("Arial", 12),  # Theme body font
            header_font=("Arial", 12, "bold"),  # Theme header font
            row_height=30,  # Match Treeview row height
            alternating_colors=("#F8F9FA", "#FFFFFF")  # Subtle alternating like cards
        )

        # Enable bindings (interactivity)
        sheet.enable_bindings((
            "single_select", "row_select", "column_width_resize",
            "arrowkeys", "right_click_popup_menu", "rc_select", "copy",
            "edit_cell", "undo"  # Support editing
        ))

        # Right-align numerical columns (Docs and Total)
        for col in range(1, len(headers)):
            sheet.align_columns(columns=[col], align="e")  # Right align

        # Style totals row (last row)
        sheet.highlight_rows(rows=[len(sheet_data) - 2], bg="#F8F9FA", fg="#691612")  # Light bg, bold text

        # Conditional formatting (scoring)
        def apply_conditional():
            for row_idx in range(len(sheet_data) - 1):  # Exclude total
                for col_idx in range(1, len(headers)):  # Skip section column
                    value = sheet_data[row_idx + 1][col_idx]  # +1 for data offset
                    if isinstance(value, (int, float)):
                        if value < 50:
                            sheet.highlight_cells(row=row_idx, column=col_idx, bg="#EF4444", fg="#FFFFFF")  # Red for low
                        elif value > 90:
                            sheet.highlight_cells(row=row_idx, column=col_idx, bg="#22C55E", fg="#FFFFFF")  # Green for high

        apply_conditional()
        sheet.redraw()  # Refresh after styling

        # Search functionality
        def search_table(event):
            search_term = search_entry.get().lower()
            if not search_term:
                sheet.set_sheet_data(sheet_data[1:])  # Reset to full data
                apply_conditional()
                sheet.redraw()
                return
            filtered_data = [row for row in sheet_data[1:] if search_term in str(row[0]).lower()]
            sheet.set_sheet_data(filtered_data)
            apply_conditional()
            sheet.redraw()

        search_entry.bind("<KeyRelease>", search_table)

        # Pack the sheet
        sheet.pack(expand=True, fill="both", padx=10, pady=10)

        return sheet