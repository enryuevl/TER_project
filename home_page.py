from customtkinter import *
from PIL import Image

class HomePage:
    def __init__(self, master):
        """Initialize the Home Page (Dashboard) inside a given frame."""
        self.master = master
        self._build_ui()

    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        # Home Frame
        home_frame = CTkFrame(master=self.master, fg_color="#F8F9FA")
        home_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Top Navigation Bar
        top_nav = CTkFrame(home_frame, fg_color="#BF3131", height=70, corner_radius=10)
        top_nav.pack(fill="x", padx=10, pady=(0, 20))
        CTkLabel(top_nav, text="Dashboard", font=("Poppins", 24, "bold"), text_color="#FFFFFF").pack(side="left", padx=25, pady=10)

        # Content container
        content_frame = CTkFrame(home_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10)

        # Dashboard Sections
        self._build_stats(content_frame)       # KPIs row
        self._build_reports(content_frame)     # Students per Faculty/Subject
        self._build_archive(content_frame)     # Archive (bigger)
        self._build_table(content_frame)       # Recent Evaluations

    # ---------------- STATS ROW ----------------
    def _build_stats(self, parent):
        stats_frame = CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))

        cards = [
            {"title": "Total Forms", "value": 847, "change": "+12% this week", "color": "#22C55E"},
            {"title": "Teachers Evaluated", "value": 42, "change": "+7% this week", "color": "#22C55E"},
            {"title": "Average Score", "value": 8.7, "change": "+3% this week", "color": "#22C55E"},
            {"title": "Pending Reviews", "value": 12, "change": "-5% this week", "color": "#EF4444"},
        ]

        for card in cards:
            frame = CTkFrame(stats_frame, fg_color="#FFFFFF", corner_radius=14, width=200, height=120)
            frame.pack(side="left", padx=10, expand=True, fill="both")
            frame.pack_propagate(False)

            CTkLabel(frame, text=card["title"], font=("Poppins", 14, "bold"), text_color="#691612").pack(pady=(10, 5))
            CTkLabel(frame, text=str(card["value"]), font=("Poppins", 28, "bold"), text_color="#212529").pack()
            CTkLabel(frame, text=card["change"], font=("Poppins", 12), text_color=card["color"]).pack(pady=(5, 0))

    # ---------------- REPORTS SECTION ----------------
    def _build_reports(self, parent):
        """Reports section: Number of Students per Faculty/Subject"""
        reports_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=300)
        reports_frame.pack(fill="x", padx=10, pady=(0, 20))
        reports_frame.pack_propagate(False)

        # Header
        header = CTkFrame(reports_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header, text="Students per Faculty / Subject", font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        # Filters
        filter_frame = CTkFrame(reports_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        dept_menu = CTkOptionMenu(filter_frame,
                                  values=["All Departments", "BSIT", "BSIS", "BSOA"],
                                  fg_color="#F1F3F5", button_color="#E9ECEF",
                                  button_hover_color="#DDE2E6", text_color="#495057",
                                  dropdown_fg_color="#FFFFFF", width=150)
        dept_menu.pack(side="left", padx=(0, 10))
        dept_menu.set("All Departments")

        sem_menu = CTkOptionMenu(filter_frame,
                                 values=["1st Semester", "2nd Semester"],
                                 fg_color="#F1F3F5", button_color="#E9ECEF",
                                 button_hover_color="#DDE2E6", text_color="#495057",
                                 dropdown_fg_color="#FFFFFF", width=150)
        sem_menu.pack(side="left", padx=(0, 10))
        sem_menu.set("1st Semester")

        CTkButton(filter_frame, text="Generate Report", fg_color="#691612", hover_color="#8B1D18",
                  corner_radius=6, width=150).pack(side="right")

        # Chart Placeholder
        chart_area = CTkFrame(reports_frame, fg_color="transparent")
        chart_area.pack(fill="both", expand=True, padx=20, pady=10)
        CTkLabel(chart_area, text="Bar Chart of Students/Faculty will render here",
                 font=("Arial", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- ARCHIVE SECTION (BIGGER) ----------------
    def _build_archive(self, parent):
        """Archive section: Old Teaching Efficiency Ratings"""
        archive_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=400)  # Made taller
        archive_frame.pack(fill="x", padx=10, pady=(0, 20))
        archive_frame.pack_propagate(False)

        # Header
        header_frame = CTkFrame(archive_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header_frame, text="Archive - Teaching Efficiency Ratings",
                 font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        # Filters
        filter_frame = CTkFrame(archive_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        year_menu = CTkOptionMenu(filter_frame,
                                  values=["2025", "2024", "2023", "2022"],
                                  fg_color="#F1F3F5", button_color="#E9ECEF",
                                  button_hover_color="#DDE2E6", text_color="#495057",
                                  dropdown_fg_color="#FFFFFF", width=100)
        year_menu.pack(side="left", padx=(0, 10))
        year_menu.set("2025")

        dept_menu = CTkOptionMenu(filter_frame,
                                  values=["All Departments", "BSIT", "BSIS", "BSOA"],
                                  fg_color="#F1F3F5", button_color="#E9ECEF",
                                  button_hover_color="#DDE2E6", text_color="#495057",
                                  dropdown_fg_color="#FFFFFF", width=150)
        dept_menu.pack(side="left", padx=(0, 10))
        dept_menu.set("All Departments")

        CTkButton(filter_frame, text="Export", fg_color="#691612", hover_color="#8B1D18",
                  corner_radius=6, width=100).pack(side="right", padx=(10, 0))
        CTkButton(filter_frame, text="View Details", fg_color="#BF3131", hover_color="#8B1D18",
                  corner_radius=6, width=120).pack(side="right")

        # Archive Table Placeholder
        table_area = CTkFrame(archive_frame, fg_color="#F8F9FA")
        table_area.pack(fill="both", expand=True, padx=20, pady=10)
        CTkLabel(table_area, text="Archive of TER Records will be displayed here",
                 font=("Arial", 14), text_color="#6C757D").place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- RECENT EVALUATIONS ----------------
    def _build_table(self, parent):
        table_frame = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14, height=300)
        table_frame.pack(fill="x", padx=10, pady=(0, 20))
        table_frame.pack_propagate(False)

        header = CTkFrame(table_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        CTkLabel(header, text="Recent Evaluation Results", font=("Poppins", 18, "bold"), text_color="#691612").pack(side="left")

        CTkButton(header, text="View All", fg_color="#691612", hover_color="#8B1D18",
                  corner_radius=6, width=100).pack(side="right")

        table_area = CTkFrame(table_frame, fg_color="#F8F9FA")
        table_area.pack(fill="both", expand=True, padx=20, pady=10)
        CTkLabel(table_area, text="Table of evaluation results will be displayed here",
                 font=("Arial", 14), text_color="#6C757D").place(relx=0.5, rely=0.5, anchor="center")
