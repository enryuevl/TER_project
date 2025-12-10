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
import shutil 
import sys

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


def create_app(role: str, username: str, department_id: int | None, on_logout=None):
    """Start the main ATS window with role-based navigation.

    on_logout: optional callback that will be called after the app window is destroyed.
               Use this to show your login page again if you want.
    """
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
        logo_path = utils.resource_path("logo.png")
        logo_img_data = Image.open(logo_path).convert("RGBA")
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
            img_path = utils.resource_path(icons[name])
            img = Image.open(img_path)

            return CTkImage(light_image=img, dark_image=img, size=(20, 20))
        except Exception:
            return None

    # ───────────── CUSTOM LOGOUT DIALOG ─────────────
    def show_logout_dialog():
        """
        Custom ATS-themed logout confirmation dialog.
        Returns True if user confirms logout, False otherwise.
        """
        TOPBAR = "#BF3131"
        SIDEBAR_BTN = "#AC5353"
        HOVER = "#BF3131"
        PANEL_BG = "#F5F5F5"
        LIGHT_TEXT = "#FFEFEF"
        WHITE = "#FFFFFF"

        dialog = CTkToplevel(app)
        dialog.title("Confirm Logout")
        dialog.geometry("480x260")
        dialog.resizable(False, False)

        dialog.transient(app)
        dialog.grab_set()

        main_frame = CTkFrame(dialog, fg_color=PANEL_BG, corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # Header bar
        header = CTkFrame(main_frame, fg_color=TOPBAR, corner_radius=10)
        header.pack(fill="x", padx=8, pady=(8, 4))

        CTkLabel(
            header,
            text="Logout from ATS?",
            font=("Poppins", 16, "bold"),
            text_color=WHITE
        ).pack(side="left", padx=12, pady=8)

        CTkLabel(
            header,
            text="SESSION",
            font=("Poppins", 11, "bold"),
            text_color=TOPBAR,
            fg_color=LIGHT_TEXT,
            corner_radius=999,
            padx=10,
            pady=4,
        ).pack(side="right", padx=12, pady=8)

        # Body
        body = CTkFrame(main_frame, fg_color=WHITE, corner_radius=10)
        body.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        CTkLabel(
            body,
            text=(
                "You are about to logout from the Teaching Efficiency Rating –\n"
                "Automatic Tallying System.\n\n"
                "Do you want to end this session and return to the login screen?"
            ),
            font=("Poppins", 12),
            text_color="#333333",
            justify="left"
        ).pack(anchor="w", padx=12, pady=(12, 8))

        # Footer buttons
        footer = CTkFrame(main_frame, fg_color=PANEL_BG)
        footer.pack(fill="x", padx=8, pady=(0, 8))

        result = {"confirmed": False}

        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()

        def on_logout_click():
            result["confirmed"] = True
            dialog.destroy()

        CTkButton(
            footer,
            text="Cancel",
            font=("Poppins", 12, "bold"),
            fg_color="#E5E7EB",
            hover_color="#D1D5DB",
            text_color="#111827",
            corner_radius=8,
            width=120,
            command=on_cancel
        ).pack(side="right", padx=8, pady=4)

        CTkButton(
            footer,
            text="Logout",
            font=("Poppins", 12, "bold"),
            fg_color=SIDEBAR_BTN,
            hover_color=HOVER,
            text_color=WHITE,
            corner_radius=8,
            width=120,
            command=on_logout_click
        ).pack(side="right", padx=8, pady=4)

        # Center dialog over main app
        dialog.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = app.winfo_rooty() + (app.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window(dialog)
        return result["confirmed"]

    def confirm_logout():
        if show_logout_dialog():
            # Close main ATS window
            app.destroy()
            # Optional: go back to login page
            if callable(on_logout):
                on_logout()

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

    # Top bar
    topbar = CTkFrame(master=app, height=60, fg_color="#BF3131", corner_radius=0)
    topbar.pack(side="top", fill="x")

    # Shadow
    shadow = CTkFrame(master=app, height=2, fg_color="#B22222")
    shadow.pack(side="top", fill="x")

    # --- SUBTITLE ---
    CTkLabel(
        master=topbar,
        text=f"Teaching Efficiency Rating – Automatic Tallying System  •  {username} ({role})",
        font=("Poppins", 14),
        text_color="#FFEFEF"
    ).place(relx=0.02, rely=0.72, anchor="w")

    # --- TITLE ---
    CTkLabel(
        master=topbar,
        text="Camarines Norte State College",
        font=("Poppins", 20, "bold"),
        text_color="#FFFFFF"
    ).place(relx=0.02, rely=0.36, anchor="w")

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
        "Evaluation": lambda: DeanEvaluationForm(main_frame, processed_results, ctx=ctx),
        "Results": lambda: ResultsPage(main_frame, processed_results),
        "Management": lambda: AccountsDatabasePage(main_frame, ctx),
    }

    # Role-based visibility
    role_lower = (role or "").lower()
    if role_lower == "admin":
        allowed = {"Dashboard", "Scan", "Evaluation", "Results", "Management"}
    elif role_lower == "dean":
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



def initialize_user_data():
    """
    On first run: copy default DB and results.pkl
    from the application folder into Documents/MyWork.
    """
    # Source folder (EXE folder when bundled)
    if getattr(sys, 'frozen', False):
        app_dir = sys._MEIPASS  # PyInstaller temp dir
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Destination folder
    user_dir = os.path.join(os.environ['USERPROFILE'], "Documents", "MyWork")
    os.makedirs(user_dir, exist_ok=True)

    files_to_copy = [
        "ter_db2.sqlite",
        "results.pkl",
        "template.xlsx",
        "summary.xlsx",
    ]

    for filename in files_to_copy:
        src = os.path.join(base_dir, filename)
        dst = os.path.join(user_dir, filename)

        # Only copy if not yet created
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
                print(f"[INIT] Copied {filename} to {dst}")
            except Exception as e:
                print(f"[INIT ERROR] Failed to copy {filename}: {e}")


# Standalone run (double-click friendly): opens as admin
if __name__ == "__main__":
    initialize_user_data()
    create_app(role="admin", username="Admin", department_id=1)
