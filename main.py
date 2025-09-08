from customtkinter import *
from CTkTable import CTkTable
from PIL import Image, ImageTk
from tkinter import messagebox, ttk, filedialog
import utils
import main_code
import pandas as pd
import cv2
import numpy as np
from tksheet import Sheet
import db
from scanner import WIAScanner
import threading
import datetime
import os
from accounts_page import acc_page
from scan_page import ScanPage
from results_page import ResultsPage


# Initialize database (creates Documents/MyWork/ter_db.sqlite on first run)
db.initialize_database()

# Initialize global variables
processed_results = {}
user_data = []  # Initialize user_data for render_user_page

app = CTk()
app.title("Automatic Tallying System")
app.after(10, lambda: app.state("zoomed"))
set_appearance_mode("light")

# Sidebar
sidebar_frame = CTkFrame(master=app, fg_color="#691612", width=220, corner_radius=0)
sidebar_frame.pack_propagate(0)
sidebar_frame.pack(fill="y", side="left")

# Logo
try:
    logo_img_data = Image.open("logo.png").convert("RGBA")
    logo_img = CTkImage(light_image=logo_img_data, dark_image=logo_img_data, size=(120, 120))
    logo_label = CTkLabel(master=sidebar_frame, text="", image=logo_img, bg_color="transparent")
    logo_label.pack(pady=(30, 20))
except:
    pass

# Navigation Icons
icons = {
    "Dashboard": "dashboard.png",
    "Scan": "scan.png",
    "Print": "print.png",
    "Results": "results.png",
    "Accounts": "accounts.png",
    "Logout": "logout.png"
}

def load_icon(name):
    try:
        img = Image.open(icons[name])
        return CTkImage(light_image=img, dark_image=img, size=(20, 20))
    except:
        return None

def confirm_logout():
    if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
        app.destroy()

CTkButton(
    master=sidebar_frame,
    image=load_icon("Logout"),
    text="Logout",
    fg_color="#AC5353",
    font=("Arial", 14, "bold"),
    text_color="#FFFFFF",
    hover_color="#BF3131",
    width=160,
    height=45,
    anchor="w",
    compound="left",
    command=confirm_logout
).pack(pady=30, padx=20, side="bottom")

# Modern Topbar
topbar = CTkFrame(master=app, height=60, fg_color="#BF3131", corner_radius=0)
topbar.pack(side="top", fill="x")

# Main content frame
main_frame = CTkFrame(master=app, fg_color="#F5F5F5")  # Lighter background for main content
main_frame.pack(fill="both", expand=True)


# Shadow effect
shadow = CTkFrame(master=app, height=2, fg_color="#B22222")
shadow.pack(side="top", fill="x")

CTkLabel(
    master=topbar,
    text="Camarines Norte State College",
    font=("Arial", 18, "bold"),
    text_color="#FFFFFF"
).place(relx=0.02, rely=0.5, anchor="w")

# Table style
style = ttk.Style()
style.theme_use("default")
style.configure(
    "Treeview",
    background="#FFFFFF",
    foreground="#333333",
    rowheight=25,
    fieldbackground="#FFFFFF",
    font=("Arial", 12)
)
style.configure(
    "Treeview.Heading",
    background="#691612",
    foreground="#FFFFFF",
    font=("Arial", 12, "bold")
)
style.map(
    "Treeview",
    background=[("selected", "#BF3131")],
    foreground=[("selected", "#FFFFFF")],
)

def render_home_page():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    # Home Frame with improved styling
    home_frame = CTkFrame(master=main_frame, fg_color="#F8F9FA")
    home_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Top Navigation Bar with modern design
    top_nav = CTkFrame(home_frame, fg_color="#FFFFFF", height=70, corner_radius=10)
    top_nav.pack(fill="x", padx=10, pady=(0, 20))
    
    # Dashboard title with brand color
    title_label = CTkLabel(top_nav, text="Dashboard", font=("Poppins", 24, "bold"), text_color="#691612")
    title_label.pack(side="left", padx=25, pady=10)
    
    # Right side navigation elements
    right_nav = CTkFrame(top_nav, fg_color="transparent")
    right_nav.pack(side="right", padx=20, pady=10)
    
    # Modern search box
    search_icon = CTkLabel(right_nav, text="🔍", font=("Arial", 16))
    search_icon.pack(side="left", padx=(0, 5))
    search_entry = CTkEntry(right_nav, placeholder_text="Search...", width=220, height=38, 
                          border_width=0, fg_color="#F1F3F5", corner_radius=8)
    search_entry.pack(side="left", padx=5)
    
    # Notification and profile icons
    notif_button = CTkButton(right_nav, text="🔔", width=40, height=38, fg_color="#F1F3F5", 
                           text_color="#333", hover_color="#E9ECEF", corner_radius=8)
    notif_button.pack(side="left", padx=10)
    
    profile_button = CTkButton(right_nav, text="👤", width=40, height=38, fg_color="#F1F3F5", 
                             text_color="#333", hover_color="#E9ECEF", corner_radius=8)
    profile_button.pack(side="left", padx=5)
    
    # Main content container
    content_frame = CTkFrame(home_frame, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=10)
    
    # Stats Cards Section - Redesigned with modern cards
    stats_frame = CTkFrame(content_frame, fg_color="transparent")
    stats_frame.pack(fill="x", pady=(0, 25))
    
    cards = [
        {"title": "Total Forms", "value": "847", "change": "+12%", "icon": "forms_icon.png", "color": "#4361EE"},
        {"title": "Teachers Evaluated", "value": "42", "change": "+7%", "icon": "teachers_icon.png", "color": "#BF3131"},
        {"title": "Average Score", "value": "8.7", "change": "+3%", "icon": "score_icon.png", "color": "#2EC4B6"},
        {"title": "Pending Reviews", "value": "12", "change": "-5%", "icon": "score_icon.png", "color": "#691612"},
    ]
    
    # Create modern stat cards with more details
    for card in cards:
        card_frame = CTkFrame(stats_frame, fg_color="#FFFFFF", corner_radius=14, width=250, height=130)
        card_frame.pack(side="left", padx=10, pady=10, fill="y")
        card_frame.pack_propagate(False)
        
        # Card content with better layout
        content_wrapper = CTkFrame(card_frame, fg_color="transparent")
        content_wrapper.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Top section with title and icon
        top_section = CTkFrame(content_wrapper, fg_color="transparent")
        top_section.pack(fill="x")
        
        title = CTkLabel(top_section, text=card["title"], font=("Poppins", 15), text_color="#6C757D")
        title.pack(side="left")
        
        # Icon could be added here
        icon = CTkImage(dark_image=Image.open(card["icon"]), 
                       light_image=Image.open(card["icon"]), size=(24, 24))
        icon_label = CTkLabel(top_section, image=icon, text="")
        icon_label.pack(side="right")
        
        # Value with better spacing and styling
        value = CTkLabel(content_wrapper, text=card["value"], 
                       font=("Poppins", 30, "bold"), text_color="#212529")
        value.pack(anchor="w", pady=(10, 5))
        
        # Change indicator with arrow and color
        change_color = "#22C55E" if "+" in card["change"] else "#EF4444"
        change_arrow = "↑" if "+" in card["change"] else "↓"
        change = CTkLabel(content_wrapper, text=f"{change_arrow} {card['change']} this week", 
                        font=("Poppins", 13), text_color=change_color)
        change.pack(anchor="w")
        
        # Bottom indicator line with card color
        indicator = CTkFrame(card_frame, height=5, fg_color=card["color"], corner_radius=3)
        indicator.pack(side="bottom", fill="x")
    
    # Charts Section with improved layout
    charts_row = CTkFrame(content_frame, fg_color="transparent")
    charts_row.pack(fill="x", pady=(0, 20))
    
    # Activity chart - main chart
    activity_chart = CTkFrame(charts_row, fg_color="#FFFFFF", corner_radius=14, width=700, height=350)
    activity_chart.pack(side="left", padx=10, fill="both", expand=True)
    activity_chart.pack_propagate(False)
    
    # Chart header with filters
    chart_header = CTkFrame(activity_chart, fg_color="transparent")
    chart_header.pack(fill="x", padx=20, pady=(20, 10))
    
    CTkLabel(chart_header, text="Evaluation Activity", 
           font=("Poppins", 18, "bold"), text_color="#212529").pack(side="left")
    
    filter_frame = CTkFrame(chart_header, fg_color="transparent")
    filter_frame.pack(side="right")
    
    period_options = ["Weekly", "Monthly", "Yearly"]
    period_menu = CTkOptionMenu(filter_frame, values=period_options, fg_color="#F1F3F5", 
                              button_color="#E9ECEF", button_hover_color="#DDE2E6", 
                              text_color="#495057", dropdown_fg_color="#FFFFFF", width=120)
    period_menu.pack(side="right")
    period_menu.set("Monthly")
    
    # Chart placeholder
    chart_area = CTkFrame(activity_chart, fg_color="transparent")
    chart_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    chart_placeholder = CTkLabel(chart_area, text="Area Chart Will Render Here", 
                               font=("Arial", 14), text_color="#ADB5BD")
    chart_placeholder.place(relx=0.5, rely=0.5, anchor="center")
    
    # Right side smaller charts/stats
    right_stats = CTkFrame(charts_row, fg_color="transparent", width=300)
    right_stats.pack(side="right", padx=10, fill="both")
    
    # Top performers card
    performers_card = CTkFrame(right_stats, fg_color="#FFFFFF", corner_radius=14, height=170)
    performers_card.pack(fill="x", pady=(0, 10))
    performers_card.pack_propagate(False)
    
    CTkLabel(performers_card, text="Top Performers", 
           font=("Poppins", 16, "bold"), text_color="#212529").pack(anchor="w", padx=20, pady=(15, 10))
    
    for teacher in ["Patricia Acula", "Paul Cafe", "Jheammy Buenaflor"]:
        teacher_row = CTkFrame(performers_card, fg_color="transparent", height=35)
        teacher_row.pack(fill="x", padx=20, pady=2)
        
        CTkLabel(teacher_row, text=teacher, font=("Poppins", 14), text_color="#495057").pack(side="left")
        CTkLabel(teacher_row, text="9.8", font=("Poppins", 14, "bold"), text_color="#691612").pack(side="right")
    
    # Distribution chart card
    dist_card = CTkFrame(right_stats, fg_color="#FFFFFF", corner_radius=14, height=170)
    dist_card.pack(fill="x")
    dist_card.pack_propagate(False)
    
    CTkLabel(dist_card, text="Score Distribution", 
           font=("Poppins", 16, "bold"), text_color="#212529").pack(anchor="w", padx=20, pady=(15, 10))
    
    dist_placeholder = CTkFrame(dist_card, fg_color="transparent", height=100)
    dist_placeholder.pack(fill="x", padx=20, pady=5)
    CTkLabel(dist_placeholder, text="Distribution Chart", 
           font=("Arial", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")
    
    # Recent evaluations table
    table_section = CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=14)
    table_section.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    table_header = CTkFrame(table_section, fg_color="transparent")
    table_header.pack(fill="x", padx=20, pady=(20, 15))
    
    CTkLabel(table_header, text="Recent Evaluations", 
           font=("Poppins", 18, "bold"), text_color="#212529").pack(side="left")
    
    view_all_btn = CTkButton(table_header, text="View All", fg_color="#691612", hover_color="#8B1D18", 
                           corner_radius=6, height=32, width=100)
    view_all_btn.pack(side="right")
    
    columns_frame = CTkFrame(table_section, fg_color="#F8F9FA", height=40)
    columns_frame.pack(fill="x", padx=20, pady=(0, 10))
    
    columns = ["Teacher", "Subject", "Date", "Score", "Status"]
    column_widths = [0.25, 0.25, 0.2, 0.15, 0.15]
    
    for i, col in enumerate(columns):
        col_frame = CTkFrame(columns_frame, fg_color="transparent")
        col_frame.place(relx=sum(column_widths[:i]), rely=0, 
                      relwidth=column_widths[i], relheight=1)
        CTkLabel(col_frame, text=col, font=("Poppins", 14, "bold"), 
               text_color="#495057").place(relx=0.02, rely=0.5, anchor="w")
    
    CTkLabel(table_section, text="Your evaluation data table will be displayed here", 
           font=("Poppins", 14), text_color="#6C757D").pack(pady=40)
    
    footer = CTkFrame(home_frame, fg_color="transparent", height=40)
    footer.pack(fill="x", pady=(20, 0))
    
    footer_text = CTkLabel(footer, text="Pro Tip: Use filters to narrow down evaluation results by department or date range.", 
                         font=("Poppins", 12), text_color="#6C757D")
    footer_text.pack(side="left", padx=15)
    
    version_text = CTkLabel(footer, text="v1.2.0", font=("Poppins", 12), text_color="#ADB5BD")
    version_text.pack(side="right", padx=15)

#this supposed to be accounts page


def show_database_page():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    container = CTkFrame(master=main_frame, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = CTkLabel(
        container, 
        text="Database Viewer", 
        font=("Arial", 24, "bold"), 
        text_color="#691612"
    )
    title_label.pack(pady=(0, 20))
    
    # Create tabs for different tables
    tab_frame = CTkFrame(container, fg_color="transparent")
    tab_frame.pack(fill="x", pady=(0, 20))
    
    # Tab buttons
    tab_buttons = {}
    entities = ["Students", "Faculty", "Departments", "Subjects", "Blocks", "Enrollments", "Teaching Assignments"]
    
    for i, entity in enumerate(entities):
        btn = CTkButton(
            tab_frame,
            text=entity,
            command=lambda e=entity: show_table_tab(e),
            fg_color="#AC5353" if i == 0 else "#F1F3F5",
            text_color="#FFFFFF" if i == 0 else "#333333",
            hover_color="#BF3131" if i == 0 else "#E9ECEF",
            width=140,
            height=35,
            corner_radius=8
        )
        btn.pack(side="left", padx=5)
        tab_buttons[entity] = btn
    
    # Content area
    content_frame = CTkFrame(container, fg_color="#FFFFFF", corner_radius=10)
    content_frame.pack(fill="both", expand=True)
    
    def show_table_tab(table_name):
        # Update button colors
        for name, btn in tab_buttons.items():
            if name == table_name:
                btn.configure(fg_color="#AC5353", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#F1F3F5", text_color="#333333")
        
        # Clear content and show new table
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        # Header with search and export
        header_frame = CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
    
        CTkLabel(
            header_frame, 
            text=f"{table_name} Table", 
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
            height=32
        )
        search_entry.pack(side="left", padx=(0, 10))
        
        # Export button
        export_btn = CTkButton(
            search_frame,
            text="Export CSV",
            command=lambda: export_table_data(table_name),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 12, "bold"),
            height=32,
            corner_radius=6
        )
        export_btn.pack(side="left")
        
        # Table container
        table_container = CTkFrame(content_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create table based on table name
        if table_name == "Students":
            show_students_table(table_container, search_entry)
        elif table_name == "Faculty":
            show_faculty_table(table_container, search_entry)
        elif table_name == "Departments":
            show_departments_table(table_container, search_entry)
        elif table_name == "Subjects":
            show_subjects_table(table_container, search_entry)
        elif table_name == "Blocks":
            show_blocks_table(table_container, search_entry)
        elif table_name == "Enrollments":
            show_enrollments_table(table_container, search_entry)
        elif table_name == "Teaching Assignments":
            show_teaching_assignments_table(table_container, search_entry)
    
    def show_students_table(container, search_entry):
        # Create Treeview
        style = ttk.Style()
        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#333333",
            rowheight=30,
            fieldbackground="#FFFFFF"
        )
        style.configure(
            "Treeview.Heading",
            background="#F8F9FA",
            foreground="#691612",
            font=("Arial", 12, "bold")
        )
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
    
        # Scrollbar
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
    
        # Treeview
        tree = ttk.Treeview(
            container,
            columns=("ID", "Name", "Block"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        # Headings
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Student Name")
        tree.heading("Block", text="Block")
        
        # Columns
        tree.column("ID", width=80, anchor="center")
        tree.column("Name", width=300, anchor="w")
        tree.column("Block", width=200, anchor="center")
        
        # Load data
        def load_students_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT s.id, s.name, 
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block Assigned'
                               END as block_info
                        FROM students s
                        LEFT JOIN blocks b ON s.block_id = b.id
                        ORDER BY s.name
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load students: {str(e)}")
        
        # Search functionality
        def search_students(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT s.id, s.name, 
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block Assigned'
                               END as block_info
                        FROM students s
                        LEFT JOIN blocks b ON s.block_id = b.id
                        WHERE s.name LIKE ? OR b.section LIKE ?
                        ORDER BY s.name
                    """, (f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search students: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_students)
        load_students_data()
    
    def show_faculty_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Name", "Department", "Rank"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Faculty Name")
        tree.heading("Department", text="Department")
        tree.heading("Rank", text="Rank")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Name", width=250, anchor="w")
        tree.column("Department", width=200, anchor="w")
        tree.column("Rank", width=150, anchor="center")
        
        def load_faculty_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT f.id, f.name, 
                               COALESCE(d.name, 'No Department') as dept_name,
                               f.rank
                        FROM faculty f
                        LEFT JOIN departments d ON f.department_id = d.id
                        ORDER BY f.name
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load faculty: {str(e)}")
        
        def search_faculty(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT f.id, f.name, 
                               COALESCE(d.name, 'No Department') as dept_name,
                               f.rank
                        FROM faculty f
                        LEFT JOIN departments d ON f.department_id = d.id
                        WHERE f.name LIKE ? OR d.name LIKE ? OR f.rank LIKE ?
                        ORDER BY f.name
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search faculty: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_faculty)
        load_faculty_data()
    
    def show_departments_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Name", "Faculty Count"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Department Name")
        tree.heading("Faculty Count", text="Faculty Members")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Name", width=300, anchor="w")
        tree.column("Faculty Count", width=150, anchor="center")
        
        def load_departments_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT d.id, d.name, 
                               COUNT(f.id) as faculty_count
                        FROM departments d
                        LEFT JOIN faculty f ON d.id = f.department_id
                        GROUP BY d.id, d.name
                        ORDER BY d.name
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load departments: {str(e)}")
        
        def search_departments(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT d.id, d.name, 
                               COUNT(f.id) as faculty_count
                        FROM departments d
                        LEFT JOIN faculty f ON d.id = f.department_id
                        WHERE d.name LIKE ?
                        GROUP BY d.id, d.name
                        ORDER BY d.name
                    """, (f"%{search_term}%",))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search departments: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_departments)
        load_departments_data()
    
    def show_subjects_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Code", "Name", "Units"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Code", text="Subject Code")
        tree.heading("Name", text="Subject Name")
        tree.heading("Units", text="Units")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Code", width=150, anchor="center")
        tree.column("Name", width=350, anchor="w")
        tree.column("Units", width=100, anchor="center")
        
        def load_subjects_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("SELECT id, code, name, units FROM subjects ORDER BY code")
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load subjects: {str(e)}")
        
        def search_subjects(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT id, code, name, units 
                        FROM subjects 
                        WHERE code LIKE ? OR name LIKE ?
                        ORDER BY code
                    """, (f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search subjects: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_subjects)
        load_subjects_data()
    
    def show_blocks_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Year Level", "Section", "Student Count"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Year Level", text="Year Level")
        tree.heading("Section", text="Section")
        tree.heading("Student Count", text="Students")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Year Level", width=120, anchor="center")
        tree.column("Section", width=100, anchor="center")
        tree.column("Student Count", width=120, anchor="center")
        
        def load_blocks_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT b.id, b.year_level, b.section,
                               COUNT(s.id) as student_count
                        FROM blocks b
                        LEFT JOIN students s ON b.id = s.block_id
                        GROUP BY b.id, b.year_level, b.section
                        ORDER BY b.year_level, b.section
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load blocks: {str(e)}")
        
        def search_blocks(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT b.id, b.year_level, b.section,
                               COUNT(s.id) as student_count
                        FROM blocks b
                        LEFT JOIN students s ON b.id = s.block_id
                        WHERE CAST(b.year_level AS TEXT) LIKE ? OR b.section LIKE ?
                        GROUP BY b.id, b.year_level, b.section
                        ORDER BY b.year_level, b.section
                    """, (f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search blocks: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_blocks)
        load_blocks_data()
    
    def show_enrollments_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Student", "Subject", "Block"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Student", text="Student Name")
        tree.heading("Subject", text="Subject")
        tree.heading("Block", text="Block")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Student", width=250, anchor="w")
        tree.column("Subject", width=250, anchor="w")
        tree.column("Block", width=200, anchor="center")
        
        def load_enrollments_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT e.id, s.name as student_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info
                        FROM enrollments e
                        LEFT JOIN students s ON e.student_id = s.id
                        LEFT JOIN subjects sub ON e.subject_id = sub.id
                        LEFT JOIN blocks b ON e.block_id = b.id
                        ORDER BY s.name
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load enrollments: {str(e)}")
        
        def search_enrollments(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT e.id, s.name as student_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info
                        FROM enrollments e
                        LEFT JOIN students s ON e.student_id = s.id
                        LEFT JOIN subjects sub ON e.subject_id = sub.id
                        LEFT JOIN blocks b ON e.block_id = b.id
                        WHERE s.name LIKE ? OR sub.name LIKE ? OR b.section LIKE ?
                        ORDER BY s.name
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search enrollments: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_enrollments)
        load_enrollments_data()
    
    def show_teaching_assignments_table(container, search_entry):
        style = ttk.Style()
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=30, fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", background="#F8F9FA", foreground="#691612", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
        
        tree_scroll = CTkScrollbar(container, orientation="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        tree = ttk.Treeview(
            container,
            columns=("ID", "Faculty", "Subject", "Block", "Semester"),
            show="headings",
            style="Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        tree.heading("ID", text="ID")
        tree.heading("Faculty", text="Faculty Name")
        tree.heading("Subject", text="Subject")
        tree.heading("Block", text="Block")
        tree.heading("Semester", text="Semester")
        
        tree.column("ID", width=80, anchor="center")
        tree.column("Faculty", width=200, anchor="w")
        tree.column("Subject", width=200, anchor="w")
        tree.column("Block", width=180, anchor="center")
        tree.column("Semester", width=120, anchor="center")
        
        def load_teaching_assignments_data():
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT ta.id, f.name as faculty_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info,
                               COALESCE(ta.semester, 'Not Set') as semester
                        FROM teaching_assignments ta
                        LEFT JOIN faculty f ON ta.faculty_id = f.id
                        LEFT JOIN subjects sub ON ta.subject_id = sub.id
                        LEFT JOIN blocks b ON ta.block_id = b.id
                        ORDER BY f.name
                    """)
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to load teaching assignments: {str(e)}")
        
        def search_teaching_assignments(event):
            search_term = search_entry.get().lower()
            tree.delete(*tree.get_children())
            try:
                import db
                with db.connect() as conn:
                    cursor = conn.execute("""
                        SELECT ta.id, f.name as faculty_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info,
                               COALESCE(ta.semester, 'Not Set') as semester
                        FROM teaching_assignments ta
                        LEFT JOIN faculty f ON ta.faculty_id = f.id
                        LEFT JOIN subjects sub ON ta.subject_id = sub.id
                        LEFT JOIN blocks b ON ta.block_id = b.id
                        WHERE f.name LIKE ? OR sub.name LIKE ? OR b.section LIKE ? OR ta.semester LIKE ?
                        ORDER BY f.name
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                    for row in cursor.fetchall():
                        tree.insert("", "end", values=row)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to search teaching assignments: {str(e)}")
        
        search_entry.bind("<KeyRelease>", search_teaching_assignments)
        load_teaching_assignments_data()
    
    def export_table_data(table_name):
        try:
            import db
            import pandas as pd
            from tkinter import filedialog
            
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")],
                initialfile=f"{table_name.lower().replace(' ', '_')}_export"
            )
            
            if not file_path:
                return
            
            # Export data based on table
            with db.connect() as conn:
                if table_name == "Students":
                    df = pd.read_sql_query("""
                        SELECT s.id, s.name, 
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block Assigned'
                               END as block_info
                        FROM students s
                        LEFT JOIN blocks b ON s.block_id = b.id
                        ORDER BY s.name
                    """, conn)
                elif table_name == "Faculty":
                    df = pd.read_sql_query("""
                        SELECT f.id, f.name, 
                               COALESCE(d.name, 'No Department') as dept_name,
                               f.rank
                        FROM faculty f
                        LEFT JOIN departments d ON f.department_id = d.id
                        ORDER BY f.name
                    """, conn)
                elif table_name == "Departments":
                    df = pd.read_sql_query("""
                        SELECT d.id, d.name, 
                               COUNT(f.id) as faculty_count
                        FROM departments d
                        LEFT JOIN faculty f ON d.id = f.department_id
                        GROUP BY d.id, d.name
                        ORDER BY d.name
                    """, conn)
                elif table_name == "Subjects":
                    df = pd.read_sql_query("SELECT id, code, name, units FROM subjects ORDER BY code", conn)
                elif table_name == "Blocks":
                    df = pd.read_sql_query("""
                        SELECT b.id, b.year_level, b.section,
                               COUNT(s.id) as student_count
                        FROM blocks b
                        LEFT JOIN students s ON b.id = s.block_id
                        GROUP BY b.id, b.year_level, b.section
                        ORDER BY b.year_level, b.section
                    """, conn)
                elif table_name == "Enrollments":
                    df = pd.read_sql_query("""
                        SELECT e.id, s.name as student_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info
                        FROM enrollments e
                        LEFT JOIN students s ON e.student_id = s.id
                        LEFT JOIN subjects sub ON e.subject_id = sub.id
                        LEFT JOIN blocks b ON e.block_id = b.id
                        ORDER BY s.name
                    """, conn)
                elif table_name == "Teaching Assignments":
                    df = pd.read_sql_query("""
                        SELECT ta.id, f.name as faculty_name,
                               sub.name as subject_name,
                               CASE 
                                   WHEN b.year_level IS NOT NULL THEN 'Year ' || b.year_level || ' - Section ' || b.section
                                   ELSE 'No Block'
                               END as block_info,
                               COALESCE(ta.semester, 'Not Set') as semester
                        FROM teaching_assignments ta
                        LEFT JOIN faculty f ON ta.faculty_id = f.id
                        LEFT JOIN subjects sub ON ta.subject_id = sub.id
                        LEFT JOIN blocks b ON ta.block_id = b.id
                        ORDER BY f.name
                    """, conn)
                
                # Save file
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                
                messagebox.showinfo("Export Successful", f"{table_name} data exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    # Show default tab
    show_table_tab("Students")



# Navigation sidebar buttons
nav_actions = {
    "Dashboard": render_home_page,
    "Scan": lambda: ScanPage(main_frame, processed_results),
    "Print": lambda: print("Print clicked"),
    "Results": lambda: ResultsPage(main_frame, processed_results),
    "Accounts": lambda: acc_page(main_frame), 
    "Database": show_database_page
}

for item, action in nav_actions.items():
    CTkButton(
        master=sidebar_frame,
        image=load_icon(item),
        text=item,
        fg_color="#AC5353",
        font=("Arial", 14, "bold"),
        text_color="#FFFFFF",
        hover_color="#BF3131",
        width=160,
        height=45,
        anchor="w",
        compound="left",
        command=action
    ).pack(pady=15, padx=20)

# Render the home page by default
render_home_page()

app.mainloop()