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
global processed_results

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
    global main_frame
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
    
    # This would be where you implement your actual chart
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
    
    # Simplified performers list
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
    
    # Placeholder for distribution chart
    dist_placeholder = CTkFrame(dist_card, fg_color="transparent", height=100)
    dist_placeholder.pack(fill="x", padx=20, pady=5)
    CTkLabel(dist_placeholder, text="Distribution Chart", 
           font=("Arial", 14), text_color="#ADB5BD").place(relx=0.5, rely=0.5, anchor="center")
    
    # Recent evaluations table
    table_section = CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=14)
    table_section.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    # Table header with title and action button
    table_header = CTkFrame(table_section, fg_color="transparent")
    table_header.pack(fill="x", padx=20, pady=(20, 15))
    
    CTkLabel(table_header, text="Recent Evaluations", 
           font=("Poppins", 18, "bold"), text_color="#212529").pack(side="left")
    
    view_all_btn = CTkButton(table_header, text="View All", fg_color="#691612", hover_color="#8B1D18", 
                           corner_radius=6, height=32, width=100)
    view_all_btn.pack(side="right")
    
    # Table columns headers
    columns_frame = CTkFrame(table_section, fg_color="#F8F9FA", height=40)
    columns_frame.pack(fill="x", padx=20, pady=(0, 10))
    
    columns = ["Teacher", "Subject", "Date", "Score", "Status"]
    column_widths = [0.25, 0.25, 0.2, 0.15, 0.15]  # Proportional widths
    
    for i, col in enumerate(columns):
        col_frame = CTkFrame(columns_frame, fg_color="transparent")
        col_frame.place(relx=sum(column_widths[:i]), rely=0, 
                      relwidth=column_widths[i], relheight=1)
        CTkLabel(col_frame, text=col, font=("Poppins", 14, "bold"), 
               text_color="#495057").place(relx=0.02, rely=0.5, anchor="w")
    
    # Placeholder for actual table data
    # Here you would implement your treeview or custom table
    # For now just showing a placeholder message
    CTkLabel(table_section, text="Your evaluation data table will be displayed here", 
           font=("Poppins", 14), text_color="#6C757D").pack(pady=40)
    
    # Footer
    footer = CTkFrame(home_frame, fg_color="transparent", height=40)
    footer.pack(fill="x", pady=(20, 0))
    
    footer_text = CTkLabel(footer, text="Pro Tip: Use filters to narrow down evaluation results by department or date range.", 
                         font=("Poppins", 12), text_color="#6C757D")
    footer_text.pack(side="left", padx=15)
    
    # Version info
    version_text = CTkLabel(footer, text="v1.2.0", font=("Poppins", 12), text_color="#ADB5BD")
    version_text.pack(side="right", padx=15)

def render_user_page():
    """Render the user management page with improved styling and structure"""
    # Clear existing widgets
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    # Main container with padding
    container = CTkFrame(master=main_frame, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Page title
    title_frame = CTkFrame(master=container, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 15))
    
    CTkLabel(
        title_frame, 
        text="User Management", 
        font=("Arial", 18, "bold"), 
        text_color="#691612"
    ).pack(anchor="w")
    
    # Top section - form and actions
    top_section = CTkFrame(master=container, fg_color="transparent")
    top_section.pack(fill="x", pady=(0, 15))
    
    # User form
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
    
    # Form fields container
    fields_frame = CTkFrame(master=form_frame, fg_color="transparent")
    fields_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Form fields
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
            
            # Store entry reference in locals for later access
            locals()[entry_name] = entry
    
    # Buttons section
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
    
    # Button definitions with consistent styling - SMALLER SIZE
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
    
    # Create a grid for buttons - 2x2 layout
    btn_grid = CTkFrame(master=buttons_container, fg_color="transparent")
    btn_grid.pack(fill="both", expand=True, pady=10)
    
    # Configure grid
    btn_grid.columnconfigure(0, weight=1)
    btn_grid.columnconfigure(1, weight=1)
    btn_grid.rowconfigure(0, weight=1)
    btn_grid.rowconfigure(1, weight=1)
    
    # Position buttons in the grid
    buttons = []
    for i, btn_config in enumerate(button_configs):
        row = i // 2
        col = i % 2
        
        # Create button frame for padding
        btn_pad = CTkFrame(master=btn_grid, fg_color="transparent")
        btn_pad.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        btn = CTkButton(
            btn_pad,
            text=btn_config["text"],
            font=("Arial", 11, "bold"),
            fg_color=btn_config["fg_color"],
            hover_color=btn_config["hover_color"],
            text_color="#FFFFFF",
            height=30,  # Reduced height
            width=120,  # Fixed width
            corner_radius=5
        )
        btn.pack(expand=True)
        buttons.append(btn)
    
    # Table section
    table_frame = CTkFrame(master=container, fg_color="#FFFFFF", corner_radius=10)
    table_frame.pack(fill="both", expand=True, pady=(0, 10))
    
    table_title = CTkFrame(master=table_frame, fg_color="#691612", corner_radius=5)
    table_title.pack(fill="x", padx=10, pady=10)
    
    # Table title with search - reorganized to fit better
    title_contents = CTkFrame(master=table_title, fg_color="transparent")
    title_contents.pack(fill="x", padx=10, pady=5)
    
    CTkLabel(
        title_contents, 
        text="User List", 
        font=("Arial", 14, "bold"), 
        text_color="#FFFFFF"
    ).pack(side="left")
    
    # Search field - made more compact
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
        height=22  # Made smaller
    )
    search_entry.pack(side="left")
    
    # Table with scrollbar
    table_container = CTkFrame(master=table_frame, fg_color="transparent")
    table_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Configure custom ttk style for treeview
    style = ttk.Style()
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground="#333333",
        rowheight=28,  # Slightly smaller row height
        fieldbackground="#FFFFFF"
    )
    style.configure(
        "Treeview.Heading",
        background="#F0F0F0",
        foreground="#691612",
        font=("Arial", 11, "bold")
    )
    style.map("Treeview", background=[("selected", "#BF3131")], foreground=[("selected", "#FFFFFF")])
    
    # Create treeview with scrollbar
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
    
    # Configure columns
    user_table.heading("Name", text="Full Name")
    user_table.heading("Username", text="Username")
    user_table.heading("Password", text="Password")
    user_table.heading("Role", text="Role")
    
    user_table.column("Name", anchor="w", width=150, minwidth=120)
    user_table.column("Username", anchor="w", width=150, minwidth=120)
    user_table.column("Password", anchor="center", width=150, minwidth=100)
    user_table.column("Role", anchor="center", width=100, minwidth=80)
    
    user_table._selected_index = None
    
    # CRUD Functions
    def clear_form():
        """Clear all form fields"""
        name_entry.delete(0, 'end')
        username_entry.delete(0, 'end')
        password_entry.delete(0, 'end')
        role_option.set("Student")
        user_table.selection_clear()
        
    def add_user():
        """Add a new user to the table"""
        data = [name_entry.get(), username_entry.get(), password_entry.get(), role_option.get()]
        if all(data):
            user_data.append(data)
            update_table()
            clear_form()
            messagebox.showinfo("Success", "User added successfully")
        else:
            messagebox.showerror("Error", "Please fill in all fields")
    
    def update_user():
        """Update the selected user"""
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
        """Delete the selected user"""
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
        """Update the table with current user data"""
        user_table.delete(*user_table.get_children())
        for i, row in enumerate(user_data):
            user_table.insert("", "end", iid=i, values=row)
    
    def on_select(event):
        """Handle table row selection"""
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
        """Get the selected row data"""
        selected = user_table.focus()
        return user_table.item(selected, "values") if selected else None
    
    def filter_users(event):
        """Filter the user table based on search input"""
        search_text = search_entry.get().lower()
        user_table.delete(*user_table.get_children())
        
        for i, row in enumerate(user_data):
            # Check if any field contains the search text
            if any(search_text in str(field).lower() for field in row):
                user_table.insert("", "end", iid=i, values=row)
    
    # Connect functions to buttons
    buttons[0].configure(command=add_user)
    buttons[1].configure(command=update_user)
    buttons[2].configure(command=delete_user)
    buttons[3].configure(command=clear_form)
    
    # Set up event bindings
    user_table.get_selected = get_selected
    user_table.bind("<<TreeviewSelect>>", on_select)
    search_entry.bind("<KeyRelease>", filter_users)
    
    # Compact status bar
    status_frame = CTkFrame(master=container, fg_color="#F8F8F8", corner_radius=5, height=25)
    status_frame.pack(fill="x")
    
    status_label = CTkLabel(
        status_frame, 
        text="Ready", 
        font=("Arial", 10), 
        text_color="#666666"
    )
    status_label.pack(side="left", padx=10)
    
    # Initialize table 
    update_table()

def render_scan_page():
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Main content frame with a clean background
    content_frame = CTkFrame(master=main_frame, fg_color="#F8F9FA")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Page title
    title_label = CTkLabel(
        content_frame, 
        text="Document Scanner", 
        font=('Montserrat', 24, 'bold'),
        text_color="#1E293B"
    )
    title_label.pack(pady=(0, 20))

    # Two-column layout
    main_layout = CTkFrame(content_frame, fg_color="transparent")
    main_layout.pack(fill="both", expand=True, padx=10)
    main_layout.grid_columnconfigure(0, weight=1)
    main_layout.grid_columnconfigure(1, weight=1)

    # === LEFT COLUMN - Scanner Controls ===
    left_column = CTkFrame(main_layout, fg_color="transparent")
    left_column.grid(row=0, column=0, sticky="nsew", padx=10)

    # Scanner actions section
    scanner_frame = CTkFrame(left_column, fg_color="#FFFFFF", corner_radius=10)
    scanner_frame.pack(fill="x", pady=10)
    
    scanner_title = CTkLabel(
        scanner_frame, 
        text="Scanner Controls", 
        font=('Montserrat', 18, 'bold'),
        text_color="#334155"
    )
    scanner_title.pack(pady=(15, 10), padx=15, anchor="w")

    # Scanner status indicator
    status_frame = CTkFrame(scanner_frame, fg_color="transparent")
    status_frame.pack(fill="x", padx=15, pady=5)
    
    status_indicator = CTkFrame(status_frame, width=12, height=12, corner_radius=6, fg_color="#EF4444")
    status_indicator.pack(side="left", padx=(0, 8))
    
    status_label = CTkLabel(status_frame, text="Scanner disconnected", font=('Montserrat', 14), text_color="#64748B")
    status_label.pack(side="left")

    # Action buttons
    def start_scan():
        # Update status indicator
        status_indicator.configure(fg_color="#10B981")
        status_label.configure(text="Scanning in progress...")
        
        # Your scanner logic here
        messagebox.showinfo("Start Scan", "Scanner activated. Please place documents.")

    def import_image():
        global processed_results
        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            try:
                # Update status
                status_indicator.configure(fg_color="#3B82F6")
                status_label.configure(text="Processing image...")
                
                # Process the image
                pil_img = Image.open(file_path)
                pil_img = main_code.fix_orientation(pil_img)
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                processed_results = main_code.process_sections(cv_img)

                # Update preview
                preview_img = pil_img.resize((400, 500))
                img = ImageTk.PhotoImage(preview_img)
                img_label.configure(image=img)
                img_label.image = img
                
                # Update status and info
                status_indicator.configure(fg_color="#10B981")
                status_label.configure(text="Image imported successfully")
                scan_info_label.configure(text=f"File: {os.path.basename(file_path)}")
                
                # Update progress indicators
                progress_bar.set(1.0)
                process_button.configure(state="normal", fg_color="#691612")
                save_button.configure(state="normal", fg_color="#BF3131")
                
            except Exception as e:
                status_indicator.configure(fg_color="#EF4444")
                status_label.configure(text="Error processing image")
                messagebox.showerror("Error", f"Failed to process image: {e}")

    def clear_scan():
        # Reset the UI
        img_label.configure(image=None)
        img_label.image = None
        scan_info_label.configure(text="No scan loaded")
        progress_bar.set(0)
        
        # Reset status
        status_indicator.configure(fg_color="#EF4444")
        status_label.configure(text="Scanner ready")
        
        # Disable buttons
        process_button.configure(state="disabled", fg_color="#94A3B8")
        save_button.configure(state="disabled", fg_color="#94A3B8")
        
        # Clear results
        global processed_results
        processed_results = {}

    button_frame = CTkFrame(scanner_frame, fg_color="transparent")
    button_frame.pack(fill="x", pady=10, padx=15)
    
    CTkButton(
        button_frame, 
        text="Start Scan", 
        command=start_scan,
        fg_color="#691612",  # Original dark red color 
        hover_color="#550d0a",  # Original hover color
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        height=40,
        corner_radius=8
    ).pack(fill="x", pady=5)
    
    CTkButton(
        button_frame, 
        text="Import Image", 
        command=import_image,
        fg_color="#BF3131",  # Original medium red color
        hover_color="#a82626",  # Original hover color
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        height=40,
        corner_radius=8
    ).pack(fill="x", pady=5)
    
    CTkButton(
        button_frame, 
        text="Clear", 
        command=clear_scan,
        fg_color="#AC5353",  # Original light red color
        hover_color="#964646",  # Original hover color
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        height=40,
        corner_radius=8
    ).pack(fill="x", pady=5)

    # Results action section
    results_frame = CTkFrame(left_column, fg_color="#FFFFFF", corner_radius=10)
    results_frame.pack(fill="x", pady=10)
    
    results_title = CTkLabel(
        results_frame, 
        text="Evaluation Results", 
        font=('Montserrat', 18, 'bold'),
        text_color="#334155"
    )
    results_title.pack(pady=(15, 10), padx=15, anchor="w")

    # Progress indicator
    progress_frame = CTkFrame(results_frame, fg_color="transparent")
    progress_frame.pack(fill="x", padx=15, pady=5)
    
    progress_label = CTkLabel(progress_frame, text="Processing Status", font=('Montserrat', 14), text_color="#64748B")
    progress_label.pack(anchor="w")
    
    progress_bar = CTkProgressBar(progress_frame, width=250, height=10, corner_radius=5, progress_color="#BF3131")
    progress_bar.pack(fill="x", pady=5)
    progress_bar.set(0)  # Initial state
    
    scan_info_label = CTkLabel(results_frame, text="No scan loaded", font=('Montserrat', 12), text_color="#64748B")
    scan_info_label.pack(anchor="w", padx=15, pady=5)

    # Result action buttons
    def process_scan():
        if processed_results:
            # Show processing animation
            progress_bar.set(0.5)
            progress_label.configure(text="Processing...")
            
            # Simulate processing time
            content_frame.after(1000, lambda: progress_bar.set(0.8))
            content_frame.after(1500, lambda: progress_bar.set(1.0))
            content_frame.after(2000, lambda: progress_label.configure(text="Processing Complete"))
            
            # Show success message
            content_frame.after(2000, lambda: messagebox.showinfo("Success", "Teacher evaluation processed successfully!"))
        else:
            messagebox.showwarning("Warning", "No scan found to process. Please scan or import.")

    def save_result():
        if processed_results:
            # Get save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")]
            )
            
            if file_path:
                # Save the data
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
        fg_color="#94A3B8",  # Disabled color
        hover_color="#550d0a",  # Original hover color
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
        fg_color="#94A3B8",  # Disabled color
        hover_color="#a82626",  # Original hover color 
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        height=40,
        corner_radius=8,
        state="disabled"
    )
    save_button.pack(fill="x", pady=5)

    # === RIGHT COLUMN - Preview Area ===
    right_column = CTkFrame(main_layout, fg_color="transparent")
    right_column.grid(row=0, column=1, sticky="nsew", padx=10)

    preview_frame = CTkFrame(right_column, fg_color="#FFFFFF", corner_radius=10)
    preview_frame.pack(fill="both", expand=True)
    
    preview_title = CTkLabel(
        preview_frame, 
        text="Document Preview", 
        font=('Montserrat', 18, 'bold'),
        text_color="#334155"
    )
    preview_title.pack(pady=(15, 10))

    # Image preview with border
    img_container = CTkFrame(preview_frame, fg_color="#E2E8F0", corner_radius=5)
    img_container.pack(padx=20, pady=10, fill="both", expand=True)
    
    img_label = CTkLabel(
        img_container, 
        text="No image loaded", 
        font=('Montserrat', 14),
        text_color="#64748B",
        fg_color="#F1F5F9", 
        width=400, 
        height=500, 
        corner_radius=5
    )
    img_label.pack(padx=10, pady=10, fill="both", expand=True)

    # Help text
    help_text = CTkLabel(
        preview_frame, 
        text="Import an image or start scanning to view document preview",
        font=('Montserrat', 12),
        text_color="#64748B"
    )
    help_text.pack(pady=(0, 15))

def render_result_page():
    global processed_results
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Main container
    content_frame = CTkFrame(master=main_frame, fg_color="#F8F9FA")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header section with title and actions
    header_frame = CTkFrame(content_frame, fg_color="transparent")
    header_frame.pack(fill="x", pady=(0, 15))
    
    # Title with evaluation details
    title_frame = CTkFrame(header_frame, fg_color="transparent")
    title_frame.pack(side="left", anchor="w")
    
    CTkLabel(
        title_frame, 
        text="Evaluation Results", 
        font=("Montserrat", 24, "bold"), 
        text_color="#691612"
    ).pack(anchor="w")
    
    # Get current date for the report
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    CTkLabel(
        title_frame, 
        text=f"Generated on {current_date}", 
        font=("Montserrat", 14), 
        text_color="#64748B"
    ).pack(anchor="w")
    
    # Action buttons in header
    action_frame = CTkFrame(header_frame, fg_color="transparent")
    action_frame.pack(side="right", anchor="e")
    
    def export_results():
        if not processed_results:
            messagebox.showwarning("No Data", "No evaluation data available to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx"), ("PDF Files", "*.pdf")]
        )
        
        if file_path:
            if file_path.endswith('.csv'):
                # Export as CSV
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(sheet_data)
                messagebox.showinfo("Export Successful", f"Results exported to {os.path.basename(file_path)}")
            elif file_path.endswith('.xlsx'):
                # Export as Excel
                df = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Results exported to {os.path.basename(file_path)}")
            elif file_path.endswith('.pdf'):
                # Export as PDF (would require a PDF library implementation)
                messagebox.showinfo("Export Initiated", "PDF export started. File will be ready shortly.")
    
    def print_report():
        if not processed_results:
            messagebox.showwarning("No Data", "No evaluation data available to print.")
            return
        # Print dialog and functionality
        messagebox.showinfo("Print", "Sending evaluation report to printer...")
    
    def new_evaluation():
        # Clear current results and navigate to scan page
        global processed_results
        processed_results = {}
        render_scan_page()
    
    CTkButton(
        action_frame, 
        text="New Evaluation", 
        command=new_evaluation,
        fg_color="#691612", 
        hover_color="#550d0a", 
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        width=150,
        height=38,
        corner_radius=8
    ).pack(side="left", padx=5)
    
    CTkButton(
        action_frame, 
        text="Export Results", 
        command=export_results,
        fg_color="#BF3131", 
        hover_color="#a82626", 
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        width=150,
        height=38,
        corner_radius=8,
        state="normal" if processed_results else "disabled"
    ).pack(side="left", padx=5)
    
    CTkButton(
        action_frame, 
        text="Print Report", 
        command=print_report,
        fg_color="#AC5353", 
        hover_color="#964646", 
        text_color="#FFFFFF", 
        font=('Montserrat', 14),
        width=150,
        height=38,
        corner_radius=8,
        state="normal" if processed_results else "disabled"
    ).pack(side="left", padx=5)

    # Check if we have processed results
    has_results = bool(processed_results)
    
    # Main content container
    main_content = CTkFrame(content_frame, fg_color="#FFFFFF", corner_radius=10)
    main_content.pack(fill="both", expand=True)
    
    if has_results:
        # Main content with tabs for different views
        # Tab buttons
        tab_buttons_frame = CTkFrame(main_content, fg_color="transparent")
        tab_buttons_frame.pack(fill="x", padx=20, pady=(15, 0))
        
        current_tab = CTkStringVar(value="Summary")
        
        def switch_tab(tab_name):
            current_tab.set(tab_name)
            show_selected_tab()
            
            # Update tab button styles
            for btn in tab_buttons:
                if btn.cget("text") == tab_name:
                    btn.configure(fg_color="#691612", text_color="#FFFFFF")
                else:
                    btn.configure(fg_color="transparent", text_color="#475569")
        
        tab_buttons = []
        for tab in ["Summary", "Detailed View", "Analytics"]:
            btn = CTkButton(
                tab_buttons_frame,
                text=tab,
                command=lambda t=tab: switch_tab(t),
                fg_color="transparent" if tab != "Summary" else "#691612",
                text_color="#475569" if tab != "Summary" else "#FFFFFF",
                hover_color="#F1F5F9",
                width=120,
                height=35,
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            tab_buttons.append(btn)
        
        # Content container for tab contents
        tab_content_frame = CTkFrame(main_content, fg_color="transparent")
        tab_content_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Create data for the sheet
        sheet_data = [["Category", "Question", "Score", "Comments"]]
        total_score = 0
        
        # Process the data from processed_results
        for section, rows in processed_results.items():
            current_category = section
            for i in range(1, 6):  # Assuming 5 rows per section
                label = section if i == 1 else ""
                question = f"Question {i}"
                score = rows.get(i, "")  # Get row score or blank
                
                # Add score to total (if it's a valid number)
                try:
                    score_value = int(score) if score else 0
                    total_score += score_value
                except ValueError:
                    score_value = score  # If score is not a number, leave it as is
                
                sheet_data.append([label, question, score_value, ""])
        
        def show_selected_tab():
            # Clear the current content
            for widget in tab_content_frame.winfo_children():
                widget.destroy()
            
            tab_name = current_tab.get()
            
            if tab_name == "Summary":
                # Create a summary view with metrics and table
                summary_frame = CTkFrame(tab_content_frame, fg_color="transparent")
                summary_frame.pack(fill="both", expand=True)
                
                # Summary metrics at the top
                metrics_frame = CTkFrame(summary_frame, fg_color="transparent")
                metrics_frame.pack(fill="x", pady=(0, 15))
                
                # Calculate metrics
                score_items = [row[2] for row in sheet_data[1:] if isinstance(row[2], int)]
                total_items = len(score_items)
                max_possible = total_items * 5  # Assuming max score of 5 per item
                percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
                avg_score = total_score / total_items if total_items > 0 else 0
                
                # Create metric cards
                metrics = [
                    {"label": "Total Score", "value": f"{total_score}/{max_possible}", "color": "#691612"},
                    {"label": "Performance", "value": f"{percentage:.1f}%", "color": "#BF3131"},
                    {"label": "Average Rating", "value": f"{avg_score:.1f}/5", "color": "#AC5353"}
                ]
                
                for i, metric in enumerate(metrics):
                    metric_card = CTkFrame(metrics_frame, fg_color="#FFFFFF", corner_radius=8)
                    metric_card.grid(row=0, column=i, padx=10, sticky="nsew")
                    metrics_frame.grid_columnconfigure(i, weight=1)
                    
                    CTkLabel(
                        metric_card, 
                        text=metric["label"], 
                        font=("Montserrat", 14), 
                        text_color="#64748B"
                    ).pack(pady=(10, 5))
                    
                    CTkLabel(
                        metric_card, 
                        text=metric["value"], 
                        font=("Montserrat", 24, "bold"), 
                        text_color=metric["color"]
                    ).pack(pady=(0, 10))
                
                # Table for summary data
                table_container = CTkFrame(summary_frame, fg_color="#FFFFFF", corner_radius=8, border_width=1, border_color="#E2E8F0")
                table_container.pack(fill="both", expand=True)
                
                # Calculate category summaries
                category_data = {}
                current_category = None
                for row in sheet_data[1:]:  # Skip header
                    category = row[0] if row[0] else current_category
                    current_category = category
                    
                    if category not in category_data:
                        category_data[category] = {"total": 0, "count": 0}
                    
                    if isinstance(row[2], int):
                        category_data[category]["total"] += row[2]
                        category_data[category]["count"] += 1
                
                # Create summary headers
                summary_headers = ["Category", "Average Score", "Rating"]
                summary_rows = []
                
                for category, data in category_data.items():
                    avg = data["total"] / data["count"] if data["count"] > 0 else 0
                    
                    # Convert average to rating text
                    if avg >= 4.5:
                        rating = "Excellent"
                    elif avg >= 3.5:
                        rating = "Good"
                    elif avg >= 2.5:
                        rating = "Average"
                    elif avg >= 1.5:
                        rating = "Below Average"
                    else:
                        rating = "Poor"
                    
                    summary_rows.append([category, f"{avg:.1f}", rating])
                
                # Create summary table
                summary_table = Sheet(
                    table_container,
                    data=summary_rows,
                    headers=summary_headers,
                    header_font=("Montserrat", 12, "bold"),
                    font=("Montserrat", 12),
                    show_x_scrollbar=False,
                    show_y_scrollbar=True,
                    height=250
                )
                
                summary_table.enable_bindings((
                    "single_select", "row_select", "copy"
                ))
                
                # Style the table
                summary_table.heading_font(("Montserrat", 12, "bold"))
                summary_table.font(("Montserrat", 12))
                summary_table.column_width(0, 150)
                summary_table.column_width(1, 120)
                summary_table.column_width(2, 120)
                
                # Color coding for ratings
                for i, row in enumerate(summary_rows):
                    rating = row[2]
                    if rating == "Excellent":
                        summary_table.highlight_cells(row=i, column=2, bg="#10B981", fg="white")
                    elif rating == "Good":
                        summary_table.highlight_cells(row=i, column=2, bg="#3B82F6", fg="white")
                    elif rating == "Average":
                        summary_table.highlight_cells(row=i, column=2, bg="#F59E0B", fg="white")
                    elif rating == "Below Average":
                        summary_table.highlight_cells(row=i, column=2, bg="#F97316", fg="white")
                    else:
                        summary_table.highlight_cells(row=i, column=2, bg="#EF4444", fg="white")
                
                summary_table.pack(fill="both", expand=True, padx=1, pady=1)
                
            elif tab_name == "Detailed View":
                # Create the detailed table with all data
                detail_frame = CTkFrame(tab_content_frame, fg_color="transparent")
                detail_frame.pack(fill="both", expand=True)
                
                # Add search/filter options
                filter_frame = CTkFrame(detail_frame, fg_color="transparent")
                filter_frame.pack(fill="x", pady=(0, 10))
                
                CTkLabel(
                    filter_frame, 
                    text="Filter by:", 
                    font=("Montserrat", 14), 
                    text_color="#64748B"
                ).pack(side="left", padx=(0, 10))
                
                # Dropdown for category filter
                categories = list(set(row[0] for row in sheet_data[1:] if row[0]))
                category_var = CTkStringVar(value="All Categories")
                
                CTkComboBox(
                    filter_frame,
                    values=["All Categories"] + categories,
                    variable=category_var,
                    width=200,
                    height=30,
                    dropdown_font=("Montserrat", 12),
                    font=("Montserrat", 12)
                ).pack(side="left", padx=5)
                
                # Create detailed table
                table_container = CTkFrame(detail_frame, fg_color="#FFFFFF", corner_radius=8, border_width=1, border_color="#E2E8F0")
                table_container.pack(fill="both", expand=True)
                
                detail_table = Sheet(
                    table_container,
                    data=sheet_data[1:],  # Skip header row
                    headers=sheet_data[0],  # Use the first row as header
                    header_font=("Montserrat", 12, "bold"),
                    font=("Montserrat", 12),
                    show_x_scrollbar=False,
                    show_y_scrollbar=True,
                    height=350
                )
                
                detail_table.enable_bindings((
                    "single_select", "row_select", "column_width_resize",
                    "arrowkeys", "right_click_popup_menu", "rc_select", "copy"
                ))
                
                # Style the table
                detail_table.heading_font(("Montserrat", 12, "bold"))
                detail_table.font(("Montserrat", 12))
                detail_table.column_width(0, 150)  # Category
                detail_table.column_width(1, 100)  # Question
                detail_table.column_width(2, 80)   # Score
                detail_table.column_width(3, 250)  # Comments
                
                # Color code scores
                for i, row in enumerate(sheet_data[1:]):
                    if isinstance(row[2], int):
                        if row[2] >= 4:
                            detail_table.highlight_cells(row=i, column=2, bg="#10B981", fg="white")
                        elif row[2] == 3:
                            detail_table.highlight_cells(row=i, column=2, bg="#F59E0B", fg="white")
                        else:
                            detail_table.highlight_cells(row=i, column=2, bg="#EF4444", fg="white")
                
                detail_table.pack(fill="both", expand=True, padx=1, pady=1)
                
            elif tab_name == "Analytics":
                # Create analytics view with charts
                analytics_frame = CTkFrame(tab_content_frame, fg_color="transparent")
                analytics_frame.pack(fill="both", expand=True)
                
                # Split view for charts
                top_charts = CTkFrame(analytics_frame, fg_color="transparent")
                top_charts.pack(fill="x", pady=(0, 15))
                top_charts.grid_columnconfigure(0, weight=1)
                top_charts.grid_columnconfigure(1, weight=1)
                
                # Chart 1: Category Performance
                chart1_frame = CTkFrame(top_charts, fg_color="#FFFFFF", corner_radius=8)
                chart1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
                
                CTkLabel(
                    chart1_frame, 
                    text="Category Performance", 
                    font=("Montserrat", 16, "bold"), 
                    text_color="#334155"
                ).pack(pady=(15, 10))
                
                chart_placeholder1 = CTkFrame(chart1_frame, fg_color="#F1F5F9", corner_radius=5, height=200)
                chart_placeholder1.pack(fill="x", padx=15, pady=(0, 15))
                
                CTkLabel(
                    chart_placeholder1, 
                    text="Bar Chart: Category Averages", 
                    font=("Montserrat", 14), 
                    text_color="#64748B"
                ).pack(expand=True)
                
                # Chart 2: Score Distribution
                chart2_frame = CTkFrame(top_charts, fg_color="#FFFFFF", corner_radius=8)
                chart2_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
                
                CTkLabel(
                    chart2_frame, 
                    text="Score Distribution", 
                    font=("Montserrat", 16, "bold"), 
                    text_color="#334155"
                ).pack(pady=(15, 10))
                
                chart_placeholder2 = CTkFrame(chart2_frame, fg_color="#F1F5F9", corner_radius=5, height=200)
                chart_placeholder2.pack(fill="x", padx=15, pady=(0, 15))
                
                CTkLabel(
                    chart_placeholder2, 
                    text="Pie Chart: Score Distribution", 
                    font=("Montserrat", 14), 
                    text_color="#64748B"
                ).pack(expand=True)
                
                # Bottom chart: Performance Trend
                bottom_chart = CTkFrame(analytics_frame, fg_color="#FFFFFF", corner_radius=8)
                bottom_chart.pack(fill="both", expand=True)
                
                CTkLabel(
                    bottom_chart, 
                    text="Question Performance", 
                    font=("Montserrat", 16, "bold"), 
                    text_color="#334155"
                ).pack(pady=(15, 10))
                
                chart_placeholder3 = CTkFrame(bottom_chart, fg_color="#F1F5F9", corner_radius=5)
                chart_placeholder3.pack(fill="both", expand=True, padx=15, pady=(0, 15))
                
                CTkLabel(
                    chart_placeholder3, 
                    text="Line Chart: Question-by-Question Performance", 
                    font=("Montserrat", 14), 
                    text_color="#64748B"
                ).pack(expand=True)
        
        # Show default tab
        show_selected_tab()
        
    else:
        # No results view
        no_results_frame = CTkFrame(main_content, fg_color="transparent")
        no_results_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Center the content vertically
        no_results_frame.grid_rowconfigure(0, weight=1)
        no_results_frame.grid_rowconfigure(2, weight=1)
        no_results_frame.grid_columnconfigure(0, weight=1)
        
        # No results message and icon
        message_frame = CTkFrame(no_results_frame, fg_color="transparent")
        message_frame.grid(row=1, column=0)
        
        # Icon placeholder (in a real app, replace with an actual icon)
        icon_frame = CTkFrame(message_frame, width=100, height=100, fg_color="#F1F5F9", corner_radius=50)
        icon_frame.pack(pady=20)
        
        CTkLabel(
            icon_frame,
            text="📄",  # Document emoji as placeholder
            font=("Arial", 40),
            text_color="#64748B"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        CTkLabel(
            message_frame,
            text="No Evaluation Results",
            font=("Montserrat", 24, "bold"),
            text_color="#334155"
        ).pack()
        
        CTkLabel(
            message_frame,
            text="There are no processed evaluation results to display.\nPlease scan or import an evaluation form to get started.",
            font=("Montserrat", 14),
            text_color="#64748B",
            justify="center"
        ).pack(pady=10)
        
        # Action button
        CTkButton(
            message_frame,
            text="Scan New Evaluation",
            command=render_scan_page,
            fg_color="#691612",
            hover_color="#550d0a",
            text_color="#FFFFFF",
            font=('Montserrat', 16),
            width=200,
            height=45,
            corner_radius=8
        ).pack(pady=20)

# Navigation sidebar buttons
nav_actions = {
    "Dashboard": render_home_page,
    "Scan": render_scan_page, 
    "Print": lambda: print("Print clicked"),
    "Results": render_result_page,
    "Accounts": render_user_page
}

for item, action in nav_actions.items():
    CTkButton(
        master=sidebar_frame,
        image=load_icon(item),
        text=item,
        fg_color="#AC5353" if item == "Results" else "#AC5353",  # Highlight active tab
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