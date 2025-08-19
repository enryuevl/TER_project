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
def render_user_page():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    container = CTkFrame(master=main_frame, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = CTkLabel(
        container, 
        text="Database Management", 
        font=("Arial", 24, "bold"), 
        text_color="#691612"
    )
    title_label.pack(pady=(0, 20))
    
    # Create tabs for different entity types
    tab_frame = CTkFrame(container, fg_color="transparent")
    tab_frame.pack(fill="x", pady=(0, 20))
    
    # Tab buttons
    tab_buttons = {}
    tab_content = {}
    
    entities = ["Students", "Faculty", "Departments", "Subjects", "Blocks", "Teaching Assignments", "Enrollments"]
    
    for i, entity in enumerate(entities):
        btn = CTkButton(
            tab_frame,
            text=entity,
            command=lambda e=entity: show_tab(e),
            fg_color="#AC5353" if i == 0 else "#F1F3F5",
            text_color="#FFFFFF" if i == 0 else "#333333",
            hover_color="#BF3131" if i == 0 else "#E9ECEF",
            width=120,
            height=35,
            corner_radius=8
        )
        btn.pack(side="left", padx=5)
        tab_buttons[entity] = btn
    
    # Content area
    content_frame = CTkFrame(container, fg_color="#FFFFFF", corner_radius=10)
    content_frame.pack(fill="both", expand=True)
    
    # Success message indicator (non-blocking)
    success_frame = CTkFrame(container, fg_color="#10B981", corner_radius=8, height=0)
    success_frame.pack(fill="x", pady=(0, 10))
    success_frame.pack_propagate(False)
    
    success_label = CTkLabel(
        success_frame, 
        text="", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    )
    success_label.pack(pady=10)
    
    def show_success_message(message):
        success_label.configure(text=message)
        success_frame.configure(height=50)
        # Auto-hide after 3 seconds
        container.after(3000, lambda: success_frame.configure(height=0))
    
    def show_tab(entity_name):
        # Update button colors
        for name, btn in tab_buttons.items():
            if name == entity_name:
                btn.configure(fg_color="#AC5353", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#F1F3F5", text_color="#333333")
        
        # Clear content and show new form
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        if entity_name == "Students":
            show_student_form()
        elif entity_name == "Faculty":
            show_faculty_form()
        elif entity_name == "Departments":
            show_department_form()
        elif entity_name == "Subjects":
            show_subject_form()
        elif entity_name == "Blocks":
            show_block_form()
        elif entity_name == "Teaching Assignments":
            show_teaching_assignment_form()
        elif entity_name == "Enrollments":
            show_enrollment_form()
    
    def show_student_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        CTkLabel(
            form_frame, 
            text="Add New Student", 
            font=("Arial", 20, "bold"), 
        text_color="#691612"
        ).pack(pady=(0, 20))
        
        # Form fields
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Student name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Student Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Block selection
        block_frame = CTkFrame(fields_frame, fg_color="transparent")
        block_frame.pack(fill="x", pady=10)
        CTkLabel(block_frame, text="Block:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        # Get blocks from database
        blocks = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, year_level, section FROM blocks")
                blocks = cursor.fetchall()
        except:
            pass
        
        if blocks:
            block_options = [f"Year {b[1]} - Section {b[2]}" for b in blocks]
            block_var = StringVar()
            block_dropdown = CTkOptionMenu(
                block_frame,
                variable=block_var,
                values=block_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            block_dropdown.pack(fill="x", pady=(5, 0))
            if block_options:
                block_dropdown.set(block_options[0])
        else:
            CTkLabel(block_frame, text="No blocks available. Create blocks first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Student",
            command=lambda: add_student(name_entry.get(), block_var.get() if 'block_var' in locals() else None),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_faculty_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Faculty Member", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Faculty name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Faculty Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Department selection
        dept_frame = CTkFrame(fields_frame, fg_color="transparent")
        dept_frame.pack(fill="x", pady=10)
        CTkLabel(dept_frame, text="Department:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        departments = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM departments")
                departments = cursor.fetchall()
        except:
            pass
        
        if departments:
            dept_options = [d[1] for d in departments]
            dept_var = StringVar()
            dept_dropdown = CTkOptionMenu(
                dept_frame,
                variable=dept_var,
                values=dept_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            dept_dropdown.pack(fill="x", pady=(5, 0))
            dept_dropdown.set(dept_options[0])
        else:
            CTkLabel(dept_frame, text="No departments available. Create departments first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Rank selection
        rank_frame = CTkFrame(fields_frame, fg_color="transparent")
        rank_frame.pack(fill="x", pady=10)
        CTkLabel(rank_frame, text="Rank:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        rank_var = StringVar()
        rank_dropdown = CTkOptionMenu(
            rank_frame,
            variable=rank_var,
            values=["Instructor", "Assistant Professor", "Associate Professor", "Professor"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        rank_dropdown.pack(fill="x", pady=(5, 0))
        rank_dropdown.set("Instructor")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Faculty Member",
            command=lambda: add_faculty(name_entry.get(), dept_var.get() if 'dept_var' in locals() else None, rank_var.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
        font=("Arial", 14, "bold"), 
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_department_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Department", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Department name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Department Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Department",
            command=lambda: add_department(name_entry.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_subject_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Subject", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Subject code
        code_frame = CTkFrame(fields_frame, fg_color="transparent")
        code_frame.pack(fill="x", pady=10)
        CTkLabel(code_frame, text="Subject Code:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        code_entry = CTkEntry(code_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        code_entry.pack(fill="x", pady=(5, 0))
        
        # Subject name
        name_frame = CTkFrame(fields_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        CTkLabel(name_frame, text="Subject Name:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        name_entry = CTkEntry(name_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Units
        units_frame = CTkFrame(fields_frame, fg_color="transparent")
        units_frame.pack(fill="x", pady=10)
        CTkLabel(units_frame, text="Units:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        units_entry = CTkEntry(units_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        units_entry.pack(fill="x", pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Subject",
            command=lambda: add_subject(code_entry.get(), name_entry.get(), units_entry.get()),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def show_block_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Block", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Year level
        year_frame = CTkFrame(fields_frame, fg_color="transparent")
        year_frame.pack(fill="x", pady=10)
        CTkLabel(year_frame, text="Year Level:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        year_entry = CTkEntry(year_frame, fg_color="#F8F9FA", border_color="#E9ECEF", height=35, font=("Arial", 14))
        year_entry.pack(fill="x", pady=(5, 0))
        
        # Section
        section_frame = CTkFrame(fields_frame, fg_color="transparent")
        section_frame.pack(fill="x", pady=10)
        CTkLabel(section_frame, text="Section:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        section_var = StringVar()
        section_dropdown = CTkOptionMenu(
            section_frame,
            variable=section_var,
            values=["A", "B", "C"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        section_dropdown.pack(fill="x", pady=(5, 0))
        section_dropdown.set("A")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Block",
            command=lambda: add_block(year_entry.get(), section_var.get()),
            fg_color="#691612",
            hover_color="#AC5353",
                text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    # Database functions
    def add_student(name, block_info):
        if not name:
            messagebox.showerror("Error", "Please enter student name")
            return

        try:
            import db
            with db.connect() as conn:
                if block_info:
                    # Extract block ID from the display text
                    block_parts = block_info.split(" - Section ")
                    year = int(block_parts[0].replace("Year ", ""))
                    section = block_parts[1]

                    cursor = conn.execute(
                        "SELECT id FROM blocks WHERE year_level = ? AND section = ?",
                        (year, section)
                    )
                    block_id = cursor.fetchone()

                    if block_id:
                        conn.execute(
                            "INSERT INTO students (name, block_id) VALUES (?, ?)",
                            (name, block_id[0])
                        )
                        conn.commit()
                        show_success_message(f"Student '{name}' added successfully!")
                    else:
                        messagebox.showerror("Error", "Selected block not found")
                else:
                    # No block info provided, insert student without block_id
                    conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
                    conn.commit()
                    show_success_message(f"Student '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add student: {str(e)}")

    
    def add_faculty(name, dept_name, rank):
        if not name:
            messagebox.showerror("Error", "Please enter faculty name")
            return
        
        try:
            import db
            with db.connect() as conn:
                if dept_name:
                    cursor = conn.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
                    dept_id = cursor.fetchone()
                    
                    if dept_id:
                        conn.execute("INSERT INTO faculty (name, department_id, rank) VALUES (?, ?, ?)", (name, dept_id[0], rank))
                        conn.commit()
                        show_success_message(f"Faculty member '{name}' added successfully!")
                    else:
                        messagebox.showerror("Error", "Selected department not found")
                else:
                    conn.execute("INSERT INTO faculty (name, rank) VALUES (?, ?)", (name, rank))
                    conn.commit()
                    show_success_message(f"Faculty member '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add faculty member: {str(e)}")
    
    def add_department(name):
        if not name:
            messagebox.showerror("Error", "Please enter department name")
            return
        
        try:
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
                conn.commit()
                show_success_message(f"Department '{name}' added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add department: {str(e)}")
    
    def add_subject(code, name, units):
        if not all([code, name, units]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            units_float = float(units)
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO subjects (code, name, units) VALUES (?, ?, ?)", (code, name, units_float))
                conn.commit()
                show_success_message(f"Subject '{name}' added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Units must be a valid number")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add subject: {str(e)}")
    
    def add_block(year, section):
        if not year:
            messagebox.showerror("Error", "Please enter year level")
            return
        
        try:
            year_int = int(year)
            import db
            with db.connect() as conn:
                conn.execute("INSERT INTO blocks (year_level, section) VALUES (?, ?)", (year_int, section))
                conn.commit()
                show_success_message(f"Block Year {year_int} Section {section} added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Year level must be a valid number")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add block: {str(e)}")
    
    def show_teaching_assignment_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Teaching Assignment", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Faculty selection
        faculty_frame = CTkFrame(fields_frame, fg_color="transparent")
        faculty_frame.pack(fill="x", pady=10)
        CTkLabel(faculty_frame, text="Faculty Member:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        faculty_members = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM faculty")
                faculty_members = cursor.fetchall()
        except:
            pass
        
        if faculty_members:
            faculty_options = [f[1] for f in faculty_members]
            faculty_var = StringVar()
            faculty_dropdown = CTkOptionMenu(
                faculty_frame,
                variable=faculty_var,
                values=faculty_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            faculty_dropdown.pack(fill="x", pady=(5, 0))
            faculty_dropdown.set(faculty_options[0])
        else:
            CTkLabel(faculty_frame, text="No faculty members available. Create faculty first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Subject selection
        subject_frame = CTkFrame(fields_frame, fg_color="transparent")
        subject_frame.pack(fill="x", pady=10)
        CTkLabel(subject_frame, text="Subject:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        subjects = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, code, name FROM subjects")
                subjects = cursor.fetchall()
        except:
            pass
        
        if subjects:
            subject_options = [f"{s[1]} - {s[2]}" for s in subjects]
            subject_var = StringVar()
            subject_dropdown = CTkOptionMenu(
                subject_frame,
                variable=subject_var,
                values=subject_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            subject_dropdown.pack(fill="x", pady=(5, 0))
            subject_dropdown.set(subject_options[0])
        else:
            CTkLabel(subject_frame, text="No subjects available. Create subjects first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Block selection
        block_frame = CTkFrame(fields_frame, fg_color="transparent")
        block_frame.pack(fill="x", pady=10)
        CTkLabel(block_frame, text="Block:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        blocks = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, year_level, section FROM blocks")
                blocks = cursor.fetchall()
        except:
            pass
        
        if blocks:
            block_options = [f"Year {b[1]} - Section {b[2]}" for b in blocks]
            block_var = StringVar()
            block_dropdown = CTkOptionMenu(
                block_frame,
                variable=block_var,
                values=block_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            block_dropdown.pack(fill="x", pady=(5, 0))
            if block_options:
                block_dropdown.set(block_options[0])
        else:
            CTkLabel(block_frame, text="No blocks available. Create blocks first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Semester
        semester_frame = CTkFrame(fields_frame, fg_color="transparent")
        semester_frame.pack(fill="x", pady=10)
        CTkLabel(semester_frame, text="Semester:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        semester_var = StringVar()
        semester_dropdown = CTkOptionMenu(
            semester_frame,
            variable=semester_var,
            values=["First Semester", "Second Semester", "Summer"],
            fg_color="#F8F9FA",
            button_color="#E9ECEF",
            button_hover_color="#DDE2E6",
            text_color="#333333",
            height=35,
            font=("Arial", 14)
        )
        semester_dropdown.pack(fill="x", pady=(5, 0))
        semester_dropdown.set("First Semester")
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Teaching Assignment",
            command=lambda: add_teaching_assignment(
                faculty_var.get() if 'faculty_var' in locals() else None,
                subject_var.get() if 'subject_var' in locals() else None,
                block_var.get() if 'block_var' in locals() else None,
                semester_var.get()
            ),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def add_teaching_assignment(faculty_name, subject_info, block_info, semester):
        if not all([faculty_name, subject_info, block_info]):
            messagebox.showerror("Error", "Please select faculty, subject, and block")
            return
        
        try:
            import db
            with db.connect() as conn:
                # Get faculty ID
                cursor = conn.execute("SELECT id FROM faculty WHERE name = ?", (faculty_name,))
                faculty_id = cursor.fetchone()
                
                if not faculty_id:
                    messagebox.showerror("Error", "Selected faculty member not found")
                    return
                
                # Get subject ID
                subject_code = subject_info.split(" - ")[0]
                cursor = conn.execute("SELECT id FROM subjects WHERE code = ?", (subject_code,))
                subject_id = cursor.fetchone()
                
                if not subject_id:
                    messagebox.showerror("Error", "Selected subject not found")
                    return
                
                # Get block ID
                block_parts = block_info.split(" - Section ")
                year = int(block_parts[0].replace("Year ", ""))
                section = block_parts[1]
                
                cursor = conn.execute("SELECT id FROM blocks WHERE year_level = ? AND section = ?", (year, section))
                block_id = cursor.fetchone()
                
                if not block_id:
                    messagebox.showerror("Error", "Selected block not found")
                    return
                
                # Insert teaching assignment
                conn.execute(
                    "INSERT INTO teaching_assignments (faculty_id, subject_id, block_id, semester) VALUES (?, ?, ?, ?)",
                    (faculty_id[0], subject_id[0], block_id[0], semester)
                )
                conn.commit()
                show_success_message(f"Teaching assignment for {faculty_name} added successfully!")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add teaching assignment: {str(e)}")
    
    def show_enrollment_form():
        form_frame = CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        CTkLabel(
            form_frame, 
            text="Add New Enrollment", 
            font=("Arial", 20, "bold"), 
            text_color="#691612"
        ).pack(pady=(0, 20))
        
        fields_frame = CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(fill="x")
        
        # Student selection
        student_frame = CTkFrame(fields_frame, fg_color="transparent")
        student_frame.pack(fill="x", pady=10)
        CTkLabel(student_frame, text="Student:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        students = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, name FROM students")
                students = cursor.fetchall()
        except:
            pass
        
        if students:
            student_options = [s[1] for s in students]
            student_var = StringVar()
            student_dropdown = CTkOptionMenu(
                student_frame,
                variable=student_var,
                values=student_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            student_dropdown.pack(fill="x", pady=(5, 0))
            student_dropdown.set(student_options[0])
        else:
            CTkLabel(student_frame, text="No students available. Create students first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Subject selection
        subject_frame = CTkFrame(fields_frame, fg_color="transparent")
        subject_frame.pack(fill="x", pady=10)
        CTkLabel(subject_frame, text="Subject:", font=("Arial", 14), text_color="#333333").pack(anchor="w")
        
        subjects = []
        try:
            import db
            with db.connect() as conn:
                cursor = conn.execute("SELECT id, code, name FROM subjects")
                subjects = cursor.fetchall()
        except:
            pass
        
        if subjects:
            subject_options = [f"{s[1]} - {s[2]}" for s in subjects]
            subject_var = StringVar()
            subject_dropdown = CTkOptionMenu(
                subject_frame,
                variable=subject_var,
                values=subject_options,
                fg_color="#F8F9FA",
                button_color="#E9ECEF",
                button_hover_color="#DDE2E6",
                text_color="#333333",
                height=35,
                font=("Arial", 14)
            )
            subject_dropdown.pack(fill="x", pady=(5, 0))
            subject_dropdown.set(subject_options[0])
        else:
            CTkLabel(subject_frame, text="No subjects available. Create subjects first.", font=("Arial", 12), text_color="#6C757D").pack(pady=(5, 0))
        
        # Submit button
        submit_btn = CTkButton(
            form_frame,
            text="Add Enrollment",
            command=lambda: add_enrollment(
                student_var.get() if 'student_var' in locals() else None,
                subject_var.get() if 'subject_var' in locals() else None
            ),
            fg_color="#691612",
            hover_color="#AC5353",
            text_color="#FFFFFF",
        font=("Arial", 14, "bold"), 
            height=40,
            corner_radius=8
        )
        submit_btn.pack(pady=30)
    
    def add_enrollment(student_name, subject_info):
        if not all([student_name, subject_info]):
            messagebox.showerror("Error", "Please select student and subject")
            return
        
        try:
            import db
            with db.connect() as conn:
                # Get student and their assigned block
                cursor = conn.execute("SELECT id, block_id FROM students WHERE name = ?", (student_name,))
                student_row = cursor.fetchone()
                
                if not student_row:
                    messagebox.showerror("Error", "Selected student not found")
                    return
                student_id, student_block_id = student_row[0], student_row[1]
                if student_block_id is None:
                    messagebox.showerror("Error", "Selected student has no assigned block. Assign a block first in the Students tab.")
                    return
                
                # Get subject ID
                subject_code = subject_info.split(" - ")[0]
                cursor = conn.execute("SELECT id FROM subjects WHERE code = ?", (subject_code,))
                subject_id = cursor.fetchone()
                
                if not subject_id:
                    messagebox.showerror("Error", "Selected subject not found")
                    return
                
                # Check if enrollment already exists
                cursor = conn.execute(
                    "SELECT id FROM enrollments WHERE student_id = ? AND subject_id = ? AND block_id = ?",
                    (student_id, subject_id[0], student_block_id)
                )
                if cursor.fetchone():
                    messagebox.showerror("Error", "Student is already enrolled in this subject for this block")
                    return
                
                # Insert enrollment
                conn.execute(
                    "INSERT INTO enrollments (student_id, subject_id, block_id) VALUES (?, ?, ?)",
                    (student_id, subject_id[0], student_block_id)
                )
                conn.commit()
                show_success_message(f"Enrollment for {student_name} added successfully!")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add enrollment: {str(e)}")
    
    # Show default tab
    show_tab("Students")

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

def render_scan_page(main_frame, processed_results):
    for widget in main_frame.winfo_children():
        widget.destroy()

    content_frame = CTkFrame(master=main_frame, fg_color="#F8F9FA")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)

    main_layout = CTkFrame(content_frame, fg_color="transparent")
    main_layout.pack(fill="both", expand=True, padx=10)
    main_layout.grid_columnconfigure(0, weight=1)
    main_layout.grid_columnconfigure(1, weight=3)

    left_column = CTkFrame(main_layout, fg_color="transparent")
    left_column.grid(row=0, column=0, sticky="nsew", padx=10)

    scanner_frame = CTkFrame(left_column, fg_color="#FFFFFF", corner_radius=10)
    scanner_frame.pack(fill="x", pady=10)

    scanner_title = CTkLabel(
        scanner_frame,
        text="Document Scanner",
        font=('Montserrat', 18, 'bold'),
        text_color="#334155"
    )
    scanner_title.pack(pady=(15, 10), padx=15, anchor="w")

    button_frame = CTkFrame(scanner_frame, fg_color="transparent")
    button_frame.pack(fill="x", pady=10, padx=15)

    def start_scan():
        try:
            # Validate selections
            teacher_name = teacher_var.get()
            subject_label = subject_var.get()
            block_label = block_var.get()

            if not teacher_name or teacher_name in ("Loading...", "No assigned teachers", "Error loading teachers"):
                messagebox.showerror("Error", "Please select a teacher before scanning.")
                return
            if not subject_label or subject_label in ("No subjects", "Error"):
                messagebox.showerror("Error", "Please select a subject before scanning.")
                return
            if not block_label or block_label in ("No blocks", "Error"):
                messagebox.showerror("Error", "Please select a block before scanning.")
                return
            scanner = WIAScanner()
            info = scanner.initialize()
            status_label.configure(text=f"Scanner detected: {info['name']}")
            pages_scanned = scanner.scan_batch()
            if pages_scanned > 0:
                status_label.configure(text=f"Batch scan completed. {pages_scanned} page(s) scanned.")
                messagebox.showinfo("Scanning Complete", f"Successfully scanned {pages_scanned} page(s)")
                results = process_work_folder(teacher_name)
                if results:
                    processed_results.update(results)
                    status_label.configure(text="Processing complete! Go to Results page to view output.")
                    update_preview(results.get(teacher_name, []))
                else:
                    status_label.configure(text="No documents found to process.")
            else:
                status_label.configure(text="No documents found in ADF.")
                messagebox.showwarning("No Documents", "No documents found in ADF. Checking for existing files...")
        except Exception as e:
            status_label.configure(text="Scanner error occurred")
            messagebox.showerror("Scanner Error", str(e))

    def scan_existing():
        teacher_name = teacher_var.get()
        subject_label = subject_var.get()
        block_label = block_var.get()
        if not teacher_name or teacher_name in ("Loading...", "No assigned teachers", "Error loading teachers"):
            messagebox.showerror("Error", "Please select a teacher before processing.")
            return
        if not subject_label or subject_label in ("No subjects", "Error"):
            messagebox.showerror("Error", "Please select a subject before processing.")
            return
        if not block_label or block_label in ("No blocks", "Error"):
            messagebox.showerror("Error", "Please select a block before processing.")
            return
        results = process_work_folder(teacher_name)
        if results:
            processed_results.update(results)
            status_label.configure(text="Processing complete! Go to Results page to view output.")
            update_preview(results.get(teacher_name, []))
        else:
            status_label.configure(text="No documents found to process.")

    def clear_scan():
        img_label.configure(image=None)
        img_label.image = None
        scan_info_label.configure(text="No scan loaded")
        progress_bar.set(0)
        status_indicator.configure(fg_color="#EF4444")
        status_label.configure(text="Scanner ready")
        process_button.configure(state="disabled", fg_color="#94A3B8")
        save_button.configure(state="disabled", fg_color="#94A3B8")
        document_listbox.configure(values=["No documents loaded"])
        document_listbox.set("No documents loaded")
        processed_results.clear()

    button_configs = [
        {"text": "Scan", "command": start_scan, "fg_color": "#691612", "hover_color": "#550d0a"},
        {"text": "Check Existing", "command": scan_existing, "fg_color": "#BF3131", "hover_color": "#a82626"},
        {"text": "Clear Documents Folder", "command": clear_scan, "fg_color": "#AC5353", "hover_color": "#964646"}
    ]

    for config in button_configs:
        CTkButton(
            button_frame,
            text=config["text"],
            command=config["command"],
            fg_color=config["fg_color"],
            hover_color=config["hover_color"],
            text_color="#FFFFFF",
            font=('Montserrat', 14),
            height=40,
            corner_radius=8
        ).pack(fill="x", pady=5)

    teacher_frame = CTkFrame(left_column, fg_color="#FFFFFF", corner_radius=10)
    teacher_frame.pack(fill="x", pady=10)

    teacher_title = CTkLabel(
        teacher_frame,
        text="Select Teacher",
        font=('Montserrat', 16, 'bold'),
        text_color="#334155"
    )
    teacher_title.pack(pady=(10, 5), padx=15, anchor="w")

    teacher_var = StringVar()
    subject_var = StringVar()
    block_var = StringVar()

    # Mappings to keep track of selected IDs
    teacher_name_to_id = {}
    subject_code_to_id = {}
    block_label_to_id = {}

    def on_teacher_change(selected_teacher_name: str):
        # Load subjects for selected teacher
        subject_code_to_id.clear()
        subject_values = ["No subjects"]
        try:
            fid = teacher_name_to_id.get(selected_teacher_name)
            import db
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT s.id, s.code, s.name FROM teaching_assignments ta "
                    "JOIN subjects s ON ta.subject_id = s.id "
                    "WHERE ta.faculty_id = ? ORDER BY s.code",
                    (fid,)
                ).fetchall()
            if rows:
                subject_values = [f"{code} - {name}" for (sid, code, name) in rows]
                for (sid, code, name) in rows:
                    subject_code_to_id[code] = sid
        except Exception:
            subject_values = ["Error"]
        subject_dropdown.configure(state="normal" if subject_values and subject_values[0] not in ("No subjects", "Error") else "disabled", values=subject_values)
        subject_dropdown.set(subject_values[0])
        # Trigger blocks load for the first subject
        if subject_values and subject_values[0] not in ("No subjects", "Error"):
            on_subject_change(subject_values[0])
        else:
            block_dropdown.configure(state="disabled", values=["No blocks"])
            block_dropdown.set("No blocks")

    def on_subject_change(selected_subject_label: str):
        # Load blocks for selected teacher + subject
        block_label_to_id.clear()
        block_values = ["No blocks"]
        try:
            if not selected_subject_label or " - " not in selected_subject_label:
                raise Exception("Invalid subject selection")
            code = selected_subject_label.split(" - ")[0]
            sid = subject_code_to_id.get(code)
            fid = teacher_name_to_id.get(teacher_var.get())
            import db
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT b.id, b.year_level, b.section FROM teaching_assignments ta "
                    "JOIN blocks b ON ta.block_id = b.id "
                    "WHERE ta.faculty_id = ? AND ta.subject_id = ? ORDER BY b.year_level, b.section",
                    (fid, sid)
                ).fetchall()
            if rows:
                block_values = [f"Year {y} - Section {s}" for (bid, y, s) in rows]
                for (bid, y, s) in rows:
                    block_label_to_id[f"Year {y} - Section {s}"] = bid
        except Exception:
            block_values = ["Error"]
        block_dropdown.configure(state="normal" if block_values and block_values[0] not in ("No blocks", "Error") else "disabled", values=block_values)
        block_dropdown.set(block_values[0])

    def load_teachers():
        values = ["No assigned teachers"]
        try:
            import db
            with db.connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT f.id, f.name FROM teaching_assignments ta "
                    "JOIN faculty f ON ta.faculty_id = f.id ORDER BY f.name"
                ).fetchall()
            if rows:
                values = [name for (fid, name) in rows]
                teacher_name_to_id.clear()
                for (fid, name) in rows:
                    teacher_name_to_id[name] = fid
        except Exception:
            values = ["Error loading teachers"]
        teacher_dropdown.configure(values=values)
        teacher_dropdown.set(values[0])
        if values and values[0] not in ("No assigned teachers", "Error loading teachers"):
            on_teacher_change(values[0])

    teacher_dropdown = CTkOptionMenu(
        teacher_frame,
        variable=teacher_var,
        values=["Loading..."],
        command=on_teacher_change,
        fg_color="#BF3131",
        button_color="#691612",
        button_hover_color="#AC5353",
        dropdown_fg_color="#FFFFFF",
        dropdown_text_color="#333333",
        dropdown_hover_color="#F0F0F0",
        text_color="#FFFFFF",
        font=('Montserrat', 14),
        width=250,
        height=35
    )
    teacher_dropdown.pack(padx=15, pady=(10, 5))

    # Subject selection (depends on teacher)
    subject_label = CTkLabel(
        teacher_frame,
        text="Select Subject",
        font=('Montserrat', 14, 'bold'),
        text_color="#334155"
    )
    subject_label.pack(pady=(5, 0), padx=15, anchor="w")

    subject_dropdown = CTkOptionMenu(
        teacher_frame,
        variable=subject_var,
        values=["No subjects"],
        command=on_subject_change,
        fg_color="#BF3131",
        button_color="#691612",
        button_hover_color="#AC5353",
        dropdown_fg_color="#FFFFFF",
        dropdown_text_color="#333333",
        dropdown_hover_color="#F0F0F0",
        text_color="#FFFFFF",
        font=('Montserrat', 14),
        width=250,
        height=35,
        state="disabled"
    )
    subject_dropdown.pack(padx=15, pady=5)

    # Block selection (depends on subject)
    block_label = CTkLabel(
        teacher_frame,
        text="Select Block",
        font=('Montserrat', 14, 'bold'),
        text_color="#334155"
    )
    block_label.pack(pady=(5, 0), padx=15, anchor="w")

    block_dropdown = CTkOptionMenu(
        teacher_frame,
        variable=block_var,
        values=["No blocks"],
        fg_color="#BF3131",
        button_color="#691612",
        button_hover_color="#AC5353",
        dropdown_fg_color="#FFFFFF",
        dropdown_text_color="#333333",
        dropdown_hover_color="#F0F0F0",
        text_color="#FFFFFF",
        font=('Montserrat', 14),
        width=250,
        height=35,
        state="disabled"
    )
    block_dropdown.pack(padx=15, pady=(5, 10))

    # Load initial teacher list from DB
    load_teachers()

    status_frame = CTkFrame(scanner_frame, fg_color="transparent")
    status_frame.pack(fill="x", padx=15, pady=5)

    status_indicator = CTkFrame(status_frame, width=12, height=12, corner_radius=6, fg_color="#EF4444")
    status_indicator.pack(side="left", padx=(0, 8))

    status_label = CTkLabel(status_frame, text="Scanner disconnected", font=('Montserrat', 14), text_color="#64748B")
    status_label.pack(side="left")

    results_frame = CTkFrame(left_column, fg_color="#FFFFFF", corner_radius=10)
    results_frame.pack(fill="x", pady=10)

    results_title = CTkLabel(
        results_frame,
        text="Evaluation Results",
        font=('Montserrat', 18, 'bold'),
        text_color="#334155"
    )
    results_title.pack(pady=(15, 10), padx=15, anchor="w")

    progress_frame = CTkFrame(results_frame, fg_color="transparent")
    progress_frame.pack(fill="x", padx=15, pady=5)

    progress_label = CTkLabel(progress_frame, text="Processing Status", font=('Montserrat', 14), text_color="#64748B")
    progress_label.pack(anchor="w")

    progress_bar = CTkProgressBar(progress_frame, width=250, height=10, corner_radius=5, progress_color="#BF3131")
    progress_bar.pack(fill="x", pady=5)
    progress_bar.set(0)

    scan_info_label = CTkLabel(results_frame, text="No scan loaded", font=('Montserrat', 12), text_color="#64748B")
    scan_info_label.pack(anchor="w", padx=15, pady=5)

    def process_scan():
        if processed_results:
            progress_bar.set(0.5)
            progress_label.configure(text="Processing...")
            content_frame.after(1000, lambda: progress_bar.set(0.8))
            content_frame.after(1500, lambda: progress_bar.set(1.0))
            content_frame.after(2000, lambda: progress_label.configure(text="Processing Complete"))
            content_frame.after(2000, lambda: messagebox.showinfo("Success", "Teacher evaluation processed successfully!"))
        else:
            messagebox.showwarning("Warning", "No scan found to process. Please scan or import.")

    def save_result():
        if processed_results:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")]
            )
            if file_path:
                df = pd.DataFrame.from_dict(processed_results, orient="index")
                if file_path.endswith('.csv'):
                    df.to_csv(file_path)
                else:
                    df.to_excel(file_path)
                messagebox.showinfo("Saved", f"Results saved to {os.path.basename(file_path)}")
        else:
            messagebox.showwarning("Warning", "Nothing to save. Please process first.")

    action_frame = CTkFrame(results_frame, fg_color="transparent")
    action_frame.pack(fill="x", pady=10, padx=15)

    process_button = CTkButton(
        action_frame,
        text="Process Evaluation",
        command=process_scan,
        fg_color="#94A3B8",
        hover_color="#550d0a",
        text_color="#FFFFFF",
        font=('Montserrat', 14),
        height=40,
        corner_radius=8,
        state="disabled"
    )
    process_button.pack(fill="x", pady=5)

    save_button = CTkButton(
        action_frame,
        text="Save Results",
        command=save_result,
        fg_color="#94A3B8",
        hover_color="#a82626",
        text_color="#FFFFFF",
        font=('Montserrat', 14),
        height=40,
        corner_radius=8,
        state="disabled"
    )
    save_button.pack(fill="x", pady=5)

    right_column = CTkFrame(main_layout, fg_color="transparent")
    right_column.grid(row=0, column=1, sticky="nsew", padx=10)

    preview_frame = CTkFrame(right_column, fg_color="#FFFFFF", corner_radius=10)
    preview_frame.pack(fill="both", expand=True)

    preview_title = CTkLabel(
        preview_frame,
        text="Document Preview",
        font=('Montserrat', 18, 'bold'),
        text_color="#ffffff",
    )
    preview_title.pack(pady=(15,0))

    doc_frame = CTkFrame(preview_frame, fg_color="transparent")
    doc_frame.pack(pady=5)

    document_listbox = CTkOptionMenu(
        doc_frame,
        values=["No documents loaded"],
        fg_color="#BF3131",
        button_color="#691612",
        button_hover_color="#AC5353",
        dropdown_fg_color="#FFFFFF",
        dropdown_text_color="#333333",
        dropdown_hover_color="#F0F0F0",
        text_color="#ffffff",
        font=('Montserrat', 14),
        width=250,
        height=35
    )
    document_listbox.pack(fill="x", padx=20)

    img_container = CTkFrame(preview_frame, fg_color="#E2E8F0", corner_radius=5)
    img_container.pack(padx=20, pady=10, fill="both", expand=True)

    img_label = CTkLabel(
        img_container,
        text="No image loaded",
        font=('Montserrat', 14),
        text_color="#ffffff",
        fg_color="#555555",
        width=400,
        height=500,
        corner_radius=5
    )
    img_label.pack(padx=10, pady=20, fill="both", expand=True)

    def update_preview(teacher_results):
        document_listbox.configure(values=[filename for filename, _ in teacher_results])
        if teacher_results:
            document_listbox.set(teacher_results[0][0])
            display_image(teacher_results[0][0], teacher_var.get())
            process_button.configure(state="normal", fg_color="#691612")
            save_button.configure(state="normal", fg_color="#BF3131")
        else:
            document_listbox.configure(values=["No documents loaded"])
            document_listbox.set("No documents loaded")
            img_label.configure(image=None, text="No image loaded")
            img_label.image = None

    def display_image(filename, teacher):
        if filename and filename != "No documents loaded":
            documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
            file_path = os.path.join(documents_folder, "MyWork", "Scan", teacher, filename)
            try:
                pil_img = Image.open(file_path)
                pil_img = pil_img.resize((400, 500), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(pil_img)
                img_label.configure(image=img_tk, text="")
                img_label.image = img_tk
            except Exception as e:
                img_label.configure(image=None, text="Error loading image")
                img_label.image = None
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    document_listbox.configure(command=lambda value: display_image(value, teacher_var.get()))

    def process_work_folder(teacher):
        documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
        scanned_folder = os.path.join(documents_folder, "MyWork", "Scan", teacher)
        if not os.path.exists(scanned_folder):
            messagebox.showerror("Error", f"Scanned folder for {teacher} not found!")
            return {}
        files = [f for f in os.listdir(scanned_folder) if f.endswith(('.bmp', '.jpg', '.jpeg', '.png'))]
        if not files:
            messagebox.showwarning("Warning", f"No documents found for {teacher}!")
            return {}
        results = []
        processed_count = 0
        failed_count = 0
        for file in files:
            try:
                file_path = os.path.join(scanned_folder, file)
                status_label.configure(text=f"Processing {teacher} - {file}...")
                content_frame.update()
                pil_img = Image.open(file_path)
                pil_img = main_code.fix_orientation(pil_img)
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                result = main_code.process_sections(cv_img)
                results.append((file, result))
                processed_count += 1
            except Exception as e:
                print(f"Error processing {file} for {teacher}: {e}")
                failed_count += 1
        if processed_count > 0:
            status = f"Processed {processed_count} document(s) for {teacher}"
            if failed_count > 0:
                status += f"\nFailed to process {failed_count} document(s)"
            print(status)
        return {teacher: results}

    help_text = CTkLabel(
        preview_frame,
        text="Select a teacher and scan/import to view document preview",
        font=('Montserrat', 12),
        text_color="#64748B"
    )
    help_text.pack(pady=(0, 15))

def render_result_page(main_frame, processed_results):
    for widget in main_frame.winfo_children():
        widget.destroy()

    if not processed_results:
        CTkLabel(
            main_frame,
            text="No results available. Please scan or process documents first.",
            font=('Montserrat', 16),
            text_color="black"
        ).pack(pady=20)
        return

    content_frame = CTkFrame(master=main_frame, fg_color="#F8F9FA")
    content_frame.pack(fill="both", expand=True, padx=20, pady=10)  # Reduced pady from 20 to 10
    
    tabs_frame = CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=10)
    tabs_frame.pack(fill="x", pady=(0, 5))  # Reduced pady from 10 to 5
    
    tab_buttons_container = CTkFrame(tabs_frame, fg_color="transparent")
    tab_buttons_container.pack(fill="x", padx=10, pady=5)
    
    sheet_container = CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=10)
    sheet_container.pack(fill="both", expand=False)  # Changed expand=True to expand=False
    
    tab_buttons = []
    
    def show_teacher_results(teacher_name):
        for widget in sheet_container.winfo_children():
            widget.destroy()
        
        for btn in tab_buttons:
            if btn.cget("text") == teacher_name:
                btn.configure(fg_color="#691612", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#475569")
        
        teacher_data = processed_results.get(teacher_name, [])
        if not teacher_data:
            CTkLabel(
                sheet_container,
                text=f"No results available for {teacher_name}",
                font=('Montserrat', 14),
                text_color="#64748B"
            ).pack(pady=20)
            return
        
        headers = ["Section/Row"]
        for idx, (filename, _) in enumerate(teacher_data):
            headers.append(f"Doc {idx + 1}")
        
        sheet_data = [headers]
        
        all_rows = {}
        for _, results in teacher_data:
            for section, rows in results.items():
                for row_num in range(1, 6):
                    row_key = f"{section} Row {row_num}"
                    if row_key not in all_rows:
                        all_rows[row_key] = []
        
        for row_key in sorted(all_rows.keys()):
            row_data = [row_key]
            for _, results in teacher_data:
                section = row_key.split(" Row ")[0]
                row_num = int(row_key.split(" Row ")[1])
                score = results.get(section, {}).get(row_num, "")
                row_data.append(score)
            sheet_data.append(row_data)
        
        total_row = ["Total"]
        for _, results in teacher_data:
            total = sum(sum(rows.values()) for rows in results.values())
            total_row.append(total)
        sheet_data.append(total_row)
        
        table = Sheet(
            sheet_container,
            data=sheet_data[1:],
            headers=sheet_data[0],
            width=800,
            height=400  # Reduced height from 600 to 400
        )
        
        table.enable_bindings((
            "single_select", "row_select", "column_width_resize",
            "arrowkeys", "right_click_popup_menu", "rc_select", "copy"
        ))
        
        table.header_font(("Montserrat", 12, "bold"))
        table.font(("Montserrat", 12, "normal"))
        
        export_frame = CTkFrame(sheet_container, fg_color="transparent")
        export_frame.pack(fill="x", pady=5, padx=10)  # Reduced pady from 10 to 5
        
        def export_teacher_results():
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
        
        CTkButton(
            export_frame,
            text="Export Results",
            command=export_teacher_results,
            fg_color="#691612",
            hover_color="#550d0a",
            text_color="#FFFFFF",
            font=("Arial", 14),
            width=150,
            height=35,
            corner_radius=8
        ).pack(side="right", padx=10)
        
        table.pack(fill="both", expand=True, padx=10, pady=(0, 5))  # Reduced pady from 10 to 5
    
    for i, teacher in enumerate(processed_results.keys()):
        btn = CTkButton(
            tab_buttons_container,
            text=teacher,
            command=lambda name=teacher: show_teacher_results(name),
            fg_color="transparent" if i > 0 else "#691612",
            text_color="#475569" if i > 0 else "#FFFFFF",
            hover_color="#F1F5F9",
            width=150,
            height=35,
            corner_radius=8
        )
        btn.pack(side="left", padx=5)
        tab_buttons.append(btn)
    
    if processed_results:
        first_teacher = next(iter(processed_results.keys()))
        show_teacher_results(first_teacher)
# Navigation sidebar buttons
nav_actions = {
    "Dashboard": render_home_page,
    "Scan": lambda: render_scan_page(main_frame, processed_results),
    "Print": lambda: print("Print clicked"),
    "Results": lambda: render_result_page(main_frame, processed_results),
    "Accounts": render_user_page,
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