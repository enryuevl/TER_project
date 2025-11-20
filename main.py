from customtkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkinter import filedialog
import utils
import main_code  # if used elsewhere
import pandas as pd
import cv2
import numpy as np
from tksheet import Sheet
import db
from scanner import WIAScanner
import threading
import datetime
import os
# ── module Imports ──
from accounts_page import AccountsDatabasePage
from scan_page import ScanPage
from results_page import ResultsPage
from Dean_evaluation_form import DeanEvaluationForm
from home_page import HomePage
from dataclasses import dataclass  



@dataclass
class AppContext:
    role: str
    username: str
    department_id: int | None



def create_app(role: str, username: str, department_id: int | None):    
    """Start the main ATS window with role-based navigation."""
    # Initialize database (creates Documents/MyWork/ter_db.sqlite on first run)
    db.initialize_database()

    # App & theme
    app = CTk()
    app.title("Automatic Tallying System")
    app.after(10, lambda: app.state("zoomed"))
    set_appearance_mode("light")

    # Global state containers
    processed_results = {}
    user_data = []  # kept for compatibility with any render_user_page usage

    # ── Sidebar
    sidebar_frame = CTkFrame(master=app, fg_color="#691612", width=220, corner_radius=0)
    sidebar_frame.pack_propagate(0)
    sidebar_frame.pack(fill="y", side="left")

    # Logo
    try:
        logo_img_data = Image.open("logo.png").convert("RGBA")
        logo_img = CTkImage(light_image=logo_img_data, dark_image=logo_img_data, size=(120, 120))
        logo_label = CTkLabel(master=sidebar_frame, text="", image=logo_img, bg_color="transparent")
        logo_label.pack(pady=(30, 20))
    except Exception:
        pass

    # Navigation Icons
    icons = {
        "Dashboard": "dashboard.png",
        "Scan": "scan.png",
        "Evaluation": "admin.png",
        "Results": "results.png",
        "Management": "accounts.png",
        "Logout": "logout.png"
    }

    def load_icon(name):
        try:
            img = Image.open(icons[name])
            return CTkImage(light_image=img, dark_image=img, size=(20, 20))
        except Exception:
            return None

    def confirm_logout():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            app.destroy()

    logout_btn = CTkButton(
        master=sidebar_frame,
        image=load_icon("Logout"),
        text="Logout",
        fg_color="#AC5353",
        font=("Poppins", 14, "bold"),
        text_color="#FFFFFF",
        hover_color="#BF3131",
        width=160,
        height=45,
        anchor="w",
        compound="left",
        command=confirm_logout
    )
    logout_btn.pack(pady=30, padx=20, side="bottom")

    # ── Topbar
    topbar = CTkFrame(master=app, height=60, fg_color="#BF3131", corner_radius=0)
    topbar.pack(side="top", fill="x")

    # Shadow
    shadow = CTkFrame(master=app, height=2, fg_color="#B22222")
    shadow.pack(side="top", fill="x")

    CTkLabel(
        master=topbar,
        text=f"Camarines Norte State College  •  {username} ({role})",
        font=("Poppins", 18, "bold"),
        text_color="#FFFFFF"
    ).place(relx=0.02, rely=0.5, anchor="w")

    # ── Main content
    main_frame = CTkFrame(master=app, fg_color="#F5F5F5")
    main_frame.pack(fill="both", expand=True)

    # ttk style
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground="#333333",
        rowheight=25,
        fieldbackground="#FFFFFF",
        font=("Poppins", 12)
    )
    style.configure(
        "Treeview.Heading",
        background="#691612",
        foreground="#FFFFFF",
        font=("Poppins", 12, "bold")
    )
    style.map(
        "Treeview",
        background=[("selected", "#BF3131")],
        foreground=[("selected", "#FFFFFF")],
    )

    # ── Navigation
    sidebar_buttons = {}
    # Set global app context
    ctx = AppContext(role=role, username=username, department_id=department_id)
    
    def add_nav_button(name, action):
        btn = CTkButton(
            master=sidebar_frame,
            image=load_icon(name),
            text=name,
            fg_color="#AC5353",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            hover_color="#BF3131",
            width=160,
            height=45,
            anchor="w",
            compound="left",
            command=action
        )
        btn.pack(pady=15, padx=20)
        sidebar_buttons[name] = btn

    # Actions (pages)
    nav_actions = {
        "Dashboard": lambda: HomePage(main_frame),
        "Scan": lambda: ScanPage(main_frame, processed_results),
        "Evaluation": lambda: DeanEvaluationForm(main_frame, processed_results),
        "Results": lambda: ResultsPage(main_frame, processed_results),
        "Management": lambda: AccountsDatabasePage(main_frame, ctx),
    }

    # Role-based visibility
    role = (role or "").lower()
    if role == "admin":
        allowed = {"Dashboard", "Scan", "Evaluation", "Results", "Management"}
    elif role == "dean":
        allowed = {"Dashboard", "Scan", "Evaluation", "Results", "Management"}  
    else:  # operator or unknown
        allowed = {"Dashboard", "Scan", "Results", "Management"}  

    for name, action in nav_actions.items():
        if name in allowed:
            add_nav_button(name, action)

    # Export buttons to utils (used by ScanPage to disable/enable during long ops)
    utils.sidebar_buttons = sidebar_buttons

    def set_sidebar_state(state="normal"):
        """Enable or disable all sidebar nav buttons."""
        for btn in sidebar_buttons.values():
            try:
                btn.configure(state=state)
            except Exception:
                pass

    # Default page
    HomePage(main_frame)  # or: ScanPage(main_frame, processed_results)

    # Shortcuts
    def toggle_fullscreen(event=None):
        app.attributes("-fullscreen", not app.attributes("-fullscreen"))

    def end_fullscreen(event=None):
        app.attributes("-fullscreen", False)

    app.bind("<F11>", toggle_fullscreen)
    app.bind("<Escape>", end_fullscreen)

    app.mainloop()


# Standalone run (double-click friendly): opens as admin
if __name__ == "__main__":
    create_app(role="admin", username="Admin", department_id=1)
