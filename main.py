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
from scanner import WIAScanner
import threading
import datetime
import os

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

def render_user_page():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    container = CTkFrame(master=main_frame, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=20)
    
    title_frame = CTkFrame(master=container, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 15))
    
    CTkLabel(
        title_frame, 
        text="User Management", 
        font=("Arial", 18, "bold"), 
        text_color="#691612"
    ).pack(anchor="w")
    
    top_section = CTkFrame(master=container, fg_color="transparent")
    top_section.pack(fill="x", pady=(0, 15))
    
    form_frame = CTkFrame(master=top_section, fg_color="#FFFFFF", corner_radius=10)
    form_frame.pack(side="left", fill="both", padx=(0, 10))
    
    form_title = CTkFrame(master=form_frame, fg_color="#691612", corner_radius=5)
    form_title.pack(fill="x", padx=10, pady=10)
    CTkLabel(
        form_title, 
        text="User Information", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    ).pack(anchor="w", padx=10, pady=5)
    
    fields_frame = CTkFrame(master=form_frame, fg_color="transparent")
    fields_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    field_pairs = [
        ("Full Name:", "name_entry"),
        ("Username:", "username_entry"),
        ("Password:", "password_entry"),
        ("Role:", "role_option")
    ]
    
    for i, (label_text, entry_name) in enumerate(field_pairs):
        field_row = CTkFrame(master=fields_frame, fg_color="transparent")
        field_row.pack(fill="x", pady=8)
        
        CTkLabel(
            field_row, 
            text=label_text, 
            font=("Arial", 12), 
            text_color="#333333",
            width=80
        ).pack(side="left")
        
        if entry_name == "role_option":
            role_option = CTkOptionMenu(
                field_row,
                values=["Student", "Faculty", "Admin"],
                fg_color="#BF3131",
                button_color="#691612",
                button_hover_color="#AC5353",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#333333",
                dropdown_hover_color="#F0F0F0",
                text_color="#FFFFFF",
                width=200
            )
            role_option.pack(side="left", fill="x", expand=True)
            role_option.set("Student")
        else:
            entry = CTkEntry(
                field_row, 
                fg_color="#F8F8F8", 
                border_color="#E0E0E0",
                corner_radius=5,
                height=32,
                placeholder_text=label_text.replace(":", ""),
                width=200
            )
            entry.pack(side="left", fill="x", expand=True)
            
            if entry_name == "password_entry":
                entry.configure(show="•")
            
            locals()[entry_name] = entry
    
    btn_frame = CTkFrame(master=top_section, fg_color="#FFFFFF", corner_radius=10)
    btn_frame.pack(side="right", fill="both", expand=True)
    
    buttons_title = CTkFrame(master=btn_frame, fg_color="#691612", corner_radius=5)
    buttons_title.pack(fill="x", padx=10, pady=10)
    CTkLabel(
        buttons_title, 
        text="Actions", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    ).pack(anchor="w", padx=10, pady=5)
    
    buttons_container = CTkFrame(master=btn_frame, fg_color="transparent")
    buttons_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    button_configs = [
        {
            "text": "Add User",
            "fg_color": "#691612",
            "hover_color": "#AC5353",
            "command": "add_user"
        },
        {
            "text": "Update User",
            "fg_color": "#BF3131",
            "hover_color": "#AC5353", 
            "command": "update_user"
        },
        {
            "text": "Delete User",
            "fg_color": "#AC5353",
            "hover_color": "#BF3131",
            "command": "delete_user"
        },
        {
            "text": "Clear Form",
            "fg_color": "#888888",
            "hover_color": "#666666",
            "command": "clear_form"
        }
    ]
    
    btn_grid = CTkFrame(master=buttons_container, fg_color="transparent")
    btn_grid.pack(fill="both", expand=True, pady=10)
    
    btn_grid.columnconfigure(0, weight=1)
    btn_grid.columnconfigure(1, weight=1)
    btn_grid.rowconfigure(0, weight=1)
    btn_grid.rowconfigure(1, weight=1)
    
    buttons = []
    for i, btn_config in enumerate(button_configs):
        row = i // 2
        col = i % 2
        
        btn_pad = CTkFrame(master=btn_grid, fg_color="transparent")
        btn_pad.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        btn = CTkButton(
            btn_pad,
            text=btn_config["text"],
            font=("Arial", 11, "bold"),
            fg_color=btn_config["fg_color"],
            hover_color=btn_config["hover_color"],
            text_color="#FFFFFF",
            height=30,
            width=120,
            corner_radius=5
        )
        btn.pack(expand=True)
        buttons.append(btn)
    
    table_frame = CTkFrame(master=container, fg_color="#FFFFFF", corner_radius=10)
    table_frame.pack(fill="both", expand=True, pady=(0, 10))
    
    table_title = CTkFrame(master=table_frame, fg_color="#691612", corner_radius=5)
    table_title.pack(fill="x", padx=10, pady=10)
    
    title_contents = CTkFrame(master=table_title, fg_color="transparent")
    title_contents.pack(fill="x", padx=10, pady=5)
    
    CTkLabel(
        title_contents, 
        text="User List", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    ).pack(side="left")
    
    search_frame = CTkFrame(master=title_contents, fg_color="transparent")
    search_frame.pack(side="right")
    
    CTkLabel(
        search_frame, 
        text="Search:", 
        font=("Arial", 11), 
        text_color="#FFFFFF"
    ).pack(side="left", padx=(0, 5))
    
    search_entry = CTkEntry(
        search_frame, 
        fg_color="#FFFFFF", 
        border_color="#E0E0E0",
        text_color="#333333",
        corner_radius=5,
        width=130,
        height=22
    )
    search_entry.pack(side="left")
    
    table_container = CTkFrame(master=table_frame, fg_color="transparent")
    table_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    style = ttk.Style()
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground="#333333",
        rowheight=28,
        fieldbackground="#FFFFFF"
    )
    style.configure(
        "Treeview.Heading",
        background="#F0F0F0",
        foreground="#691612",
        font=("Arial", 11, "bold")
    )
    style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
    
    tree_scroll = CTkScrollbar(table_container, orientation="vertical")
    tree_scroll.pack(side="right", fill="y")
    
    user_table = ttk.Treeview(
        table_container,
        columns=("Name", "Username", "Password", "Role"),
        show="headings",
        style="Treeview",
        yscrollcommand=tree_scroll.set
    )
    tree_scroll.configure(command=user_table.yview)
    user_table.pack(fill="both", expand=True)
    
    user_table.heading("Name", text="Full Name")
    user_table.heading("Username", text="Username")
    user_table.heading("Password", text="Password")
    user_table.heading("Role", text="Role")
    
    user_table.column("Name", anchor="w", width=150, minwidth=120)
    user_table.column("Username", anchor="w", width=150, minwidth=120)
    user_table.column("Password", anchor="center", width=150, minwidth=100)
    user_table.column("Role", anchor="center", width=100, minwidth=80)
    
    user_table._selected_index = None
    
    def clear_form():
        name_entry.delete(0, 'end')
        username_entry.delete(0, 'end')
        password_entry.delete(0, 'end')
        role_option.set("Student")
        user_table.selection_clear()
        
    def add_user():
        data = [name_entry.get(), username_entry.get(), password_entry.get(), role_option.get()]
        if all(data):
            user_data.append(data)
            update_table()
            clear_form()
            messagebox.showinfo("Success", "User added successfully")
        else:
            messagebox.showerror("Error", "Please fill in all fields")
    
    def update_user():
        selected = user_table.get_selected()
        if selected:
            index = user_table._selected_index
            user_data[index] = [name_entry.get(), username_entry.get(), password_entry.get(), role_option.get()]
            update_table()
            clear_form()
            messagebox.showinfo("Success", "User updated successfully")
        else:
            messagebox.showerror("Error", "Please select a user to update")
    
    def delete_user():
        selected = user_table.get_selected()
        if selected:
            index = user_table._selected_index
            user_data.pop(index)
            update_table()
            clear_form()
            messagebox.showinfo("Success", "User deleted successfully")
        else:
            messagebox.showerror("Error", "Please select a user to delete")
    
    def update_table():
        user_table.delete(*user_table.get_children())
        for i, row in enumerate(user_data):
            user_table.insert("", "end", iid=i, values=row)
    
    def on_select(event):
        selected = user_table.focus()
        if selected:
            user_table._selected_index = int(selected)
            vals = user_table.item(selected, "values")
            name_entry.delete(0, "end")
            name_entry.insert(0, vals[0])
            username_entry.delete(0, "end")
            username_entry.insert(0, vals[1])
            password_entry.delete(0, "end")
            password_entry.insert(0, vals[2])
            role_option.set(vals[3])
    
    def get_selected():
        selected = user_table.focus()
        return user_table.item(selected, "values") if selected else None
    
    def filter_users(event):
        search_text = search_entry.get().lower()
        user_table.delete(*user_table.get_children())
        
        for i, row in enumerate(user_data):
            if any(search_text in str(field).lower() for field in row):
                user_table.insert("", "end", iid=i, values=row)
    
    buttons[0].configure(command=add_user)
    buttons[1].configure(command=update_user)
    buttons[2].configure(command=delete_user)
    buttons[3].configure(command=clear_form)
    
    user_table.get_selected = get_selected
    user_table.bind("<<TreeviewSelect>>", on_select)
    search_entry.bind("<KeyRelease>", filter_users)
    
    status_frame = CTkFrame(master=container, fg_color="#F8F8F8", corner_radius=5, height=25)
    status_frame.pack(fill="x")
    
    status_label = CTkLabel(
        status_frame, 
        text="Ready", 
        font=("Arial", 10), 
        text_color="#666666"
    )
    status_label.pack(side="left", padx=10)
    
    update_table()

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
            if not teacher_var.get():
                messagebox.showerror("Error", "Please select a teacher before scanning.")
                return
            scanner = WIAScanner()
            info = scanner.initialize()
            status_label.configure(text=f"Scanner detected: {info['name']}")
            pages_scanned = scanner.scan_batch()
            if pages_scanned > 0:
                status_label.configure(text=f"Batch scan completed. {pages_scanned} page(s) scanned.")
                messagebox.showinfo("Scanning Complete", f"Successfully scanned {pages_scanned} page(s)")
                results = process_work_folder(teacher_var.get())
                if results:
                    processed_results.update(results)
                    status_label.configure(text="Processing complete! Go to Results page to view output.")
                    update_preview(results.get(teacher_var.get(), []))
                else:
                    status_label.configure(text="No documents found to process.")
            else:
                status_label.configure(text="No documents found in ADF.")
                messagebox.showwarning("No Documents", "No documents found in ADF. Checking for existing files...")
        except Exception as e:
            status_label.configure(text="Scanner error occurred")
            messagebox.showerror("Scanner Error", str(e))

    def scan_existing():
        if not teacher_var.get():
            messagebox.showerror("Error", "Please select a teacher before processing.")
            return
        results = process_work_folder(teacher_var.get())
        if results:
            processed_results.update(results)
            status_label.configure(text="Processing complete! Go to Results page to view output.")
            update_preview(results.get(teacher_var.get(), []))
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
    teacher_dropdown = CTkOptionMenu(
        teacher_frame,
        variable=teacher_var,
        values=["Mr. Daniel Maligat", "Ma'am Brigueras"],
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
    teacher_dropdown.pack(padx=15, pady=10)

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
    "Accounts": render_user_page
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