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
        top_nav = CTkFrame(home_frame, fg_color="#FFFFFF", height=70, corner_radius=10)
        top_nav.pack(fill="x", padx=10, pady=(0, 20))

        CTkLabel(
            top_nav, text="Dashboard", font=("Poppins", 24, "bold"), text_color="#691612"
        ).pack(side="left", padx=25, pady=10)

        right_nav = CTkFrame(top_nav, fg_color="transparent")
        right_nav.pack(side="right", padx=20, pady=10)

        CTkLabel(right_nav, text="🔍", font=("Arial", 16)).pack(side="left", padx=(0, 5))
        search_entry = CTkEntry(
            right_nav, placeholder_text="Search...", width=220, height=38,
            border_width=0, fg_color="#F1F3F5", corner_radius=8
        )
        search_entry.pack(side="left", padx=5)

        CTkButton(
            right_nav, text="🔔", width=40, height=38, fg_color="#F1F3F5",
            text_color="#333", hover_color="#E9ECEF", corner_radius=8
        ).pack(side="left", padx=10)

        CTkButton(
            right_nav, text="👤", width=40, height=38, fg_color="#F1F3F5",
            text_color="#333", hover_color="#E9ECEF", corner_radius=8
        ).pack(side="left", padx=5)

        # Content container
        content_frame = CTkFrame(home_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10)

        # Stats cards
        self._build_stats(content_frame)
        self._build_charts(content_frame)
        self._build_table(content_frame)

        # Footer
        footer = CTkFrame(home_frame, fg_color="transparent", height=40)
        footer.pack(fill="x", pady=(20, 0))

        CTkLabel(
            footer,
            text="Pro Tip: Use filters to narrow down evaluation results by department or date range.",
            font=("Poppins", 12), text_color="#6C757D"
        ).pack(side="left", padx=15)

        CTkLabel(
            footer, text="v1.2.0", font=("Poppins", 12), text_color="#ADB5BD"
        ).pack(side="right", padx=15)

    def _build_stats(self, parent):
        stats_frame = CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 25))

        cards = [
            {"title": "Total Forms", "value": "847", "change": "+12%", "icon": "forms_icon.png", "color": "#4361EE"},
            {"title": "Teachers Evaluated", "value": "42", "change": "+7%", "icon": "teachers_icon.png", "color": "#BF3131"},
            {"title": "Average Score", "value": "8.7", "change": "+3%", "icon": "score_icon.png", "color": "#2EC4B6"},
            {"title": "Pending Reviews", "value": "12", "change": "-5%", "icon": "score_icon.png", "color": "#691612"},
        ]

        for card in cards:
            frame = CTkFrame(stats_frame, fg_color="#FFFFFF", corner_radius=14, width=250, height=130)
            frame.pack(side="left", padx=10, pady=10, fill="y")
            frame.pack_propagate(False)

            wrapper = CTkFrame(frame, fg_color="transparent")
            wrapper.pack(fill="both", expand=True, padx=20, pady=15)

            top_section = CTkFrame(wrapper, fg_color="transparent")
            top_section.pack(fill="x")

            CTkLabel(top_section, text=card["title"], font=("Poppins", 15), text_color="#6C757D").pack(side="left")

            try:
                icon = CTkImage(dark_image=Image.open(card["icon"]),
                                light_image=Image.open(card["icon"]), size=(24, 24))
                CTkLabel(top_section, image=icon, text="").pack(side="right")
            except:
                pass

            CTkLabel(wrapper, text=card["value"], font=("Poppins", 30, "bold"), text_color="#212529").pack(anchor="w", pady=(10, 5))

            change_color = "#22C55E" if "+" in card["change"] else "#EF4444"
            change_arrow = "↑" if "+" in card["change"] else "↓"
            CTkLabel(wrapper, text=f"{change_arrow} {card['change']} this week",
                     font=("Poppins", 13), text_color=change_color).pack(anchor="w")

            CTkFrame(frame, height=5, fg_color=card["color"], corner_radius=3).pack(side="bottom", fill="x")

    def _build_charts(self, parent):
        charts_row = CTkFrame(parent, fg_color="transparent")
        charts_row.pack(fill="x", pady=(0, 20))

        activity_chart = CTkFrame(charts_row, fg_color="#FFFFFF", corner_radius=14, width=700, height=350)
        activity_chart.pack(side="left", padx=10, fill="both", expand=True)
        activity_chart.pack_propagate(False)

        chart_header = CTkFrame(activity_chart, fg_color="transparent")
        chart_header.pack(fill="x", padx=20, pady=(20, 10))

        CTkLabel(chart_header, text="Evaluation Activity", font=("Poppins", 18, "bold"), text_color="#212529").pack(side="left")

        filter_frame = CTkFrame(chart_header, fg_color="transparent")
        filter_frame.pack(side="right")
        period_menu = CTkOptionMenu(filter_frame, values=["Weekly", "Monthly", "Yearly"],
                                    fg_color="#F1F3F5", button_color="#E9ECEF", button_hover_color="#DDE2E6",
                                    text_color="#495057", dropdown_fg_color="#FFFFFF", width=120)
        period_menu.pack(side="right")
        period_menu.set("Monthly")

        chart_area = CTkFrame(activity_chart, fg_color="transparent")
        chart_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        CTkLabel(chart_area, text="Area Chart Will Render Here", font=("Arial", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")

        right_stats = CTkFrame(charts_row, fg_color="transparent", width=300)
        right_stats.pack(side="right", padx=10, fill="both")

        performers_card = CTkFrame(right_stats, fg_color="#FFFFFF", corner_radius=14, height=170)
        performers_card.pack(fill="x", pady=(0, 10))
        performers_card.pack_propagate(False)

        CTkLabel(performers_card, text="Top Performers", font=("Poppins", 16, "bold"), text_color="#212529").pack(anchor="w", padx=20, pady=(15, 10))
        for teacher in ["Patricia Acula", "Paul Cafe", "Jheammy Buenaflor"]:
            row = CTkFrame(performers_card, fg_color="transparent", height=35)
            row.pack(fill="x", padx=20, pady=2)
            CTkLabel(row, text=teacher, font=("Poppins", 14), text_color="#495057").pack(side="left")
            CTkLabel(row, text="9.8", font=("Poppins", 14, "bold"), text_color="#691612").pack(side="right")

        dist_card = CTkFrame(right_stats, fg_color="#FFFFFF", corner_radius=14, height=170)
        dist_card.pack(fill="x")
        dist_card.pack_propagate(False)
        CTkLabel(dist_card, text="Score Distribution", font=("Poppins", 16, "bold"), text_color="#212529").pack(anchor="w", padx=20, pady=(15, 10))
        CTkLabel(dist_card, text="Distribution Chart", font=("Arial", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")

    def _build_table(self, parent):
        table_section = CTkFrame(parent, fg_color="#FFFFFF", corner_radius=14)
        table_section.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        table_header = CTkFrame(table_section, fg_color="transparent")
        table_header.pack(fill="x", padx=20, pady=(20, 15))

        CTkLabel(table_header, text="Recent Evaluations", font=("Poppins", 18, "bold"), text_color="#212529").pack(side="left")
        CTkButton(table_header, text="View All", fg_color="#691612", hover_color="#8B1D18", corner_radius=6, height=32, width=100).pack(side="right")

        columns_frame = CTkFrame(table_section, fg_color="#F8F9FA", height=40)
        columns_frame.pack(fill="x", padx=20, pady=(0, 10))

        columns = ["Teacher", "Subject", "Date", "Score", "Status"]
        column_widths = [0.25, 0.25, 0.2, 0.15, 0.15]

        for i, col in enumerate(columns):
            col_frame = CTkFrame(columns_frame, fg_color="transparent")
            col_frame.place(relx=sum(column_widths[:i]), rely=0, relwidth=column_widths[i], relheight=1)
            CTkLabel(col_frame, text=col, font=("Poppins", 14, "bold"), text_color="#495057").place(relx=0.02, rely=0.5, anchor="w")

        CTkLabel(table_section, text="Your evaluation data table will be displayed here",
                 font=("Poppins", 14), text_color="#6C757D").pack(pady=40)
