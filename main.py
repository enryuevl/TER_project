from customtkinter import *
from tkinter import ttk, messagebox
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
from accounts_page import AccountsDatabasePage
from scan_page import ScanPage
from results_page import ResultsPage
from Dean_evaluation_form import DeanEvaluationForm



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







sidebar_buttons = {}
# Navigation sidebar buttons
nav_actions = {
    "Dashboard": render_home_page,
    "Scan": lambda: ScanPage(main_frame, processed_results),
    "Dean": lambda: DeanEvaluationForm(main_frame, processed_results),
    "Results": lambda: ResultsPage(main_frame, processed_results),
    "Accounts": lambda: AccountsDatabasePage(main_frame), 
    
}

for item, action in nav_actions.items():
    btn = CTkButton(
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
    sidebar_buttons[item] = btn

utils.sidebar_buttons = sidebar_buttons

def set_sidebar_state(state="normal"):
        """Enable or disable all sidebar navigation buttons."""
        for btn in sidebar_buttons.values():
            try:
                btn.configure(state=state)
            except Exception:
                pass
             
# Render the home page by default
render_home_page()

app.mainloop()