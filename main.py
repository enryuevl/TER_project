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
from home_page import HomePage


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
    "Admin": "admin.png",
    "Results": "results.png",
    "Database": "accounts.png",
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
    font=("Poppins", 14, "bold"),
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
    font=("Poppins", 18, "bold"),
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



#this supposed to be accounts page







sidebar_buttons = {}
# Navigation sidebar buttons
nav_actions = {
    "Dashboard": lambda: HomePage(main_frame),
    "Scan": lambda: ScanPage(main_frame, processed_results),
    "Admin": lambda: DeanEvaluationForm(main_frame, processed_results),
    "Results": lambda: ResultsPage(main_frame, processed_results),
    "Database": lambda: AccountsDatabasePage(main_frame), 
    
}

for item, action in nav_actions.items():
    btn = CTkButton(
        master=sidebar_frame,
        image=load_icon(item),
        text=item,
        fg_color="#AC5353",
        font=("Poppins", 14, "bold"),
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
ScanPage(main_frame, processed_results)


def toggle_fullscreen(event=None):
    app.attributes("-fullscreen", not app.attributes("-fullscreen"))

def end_fullscreen(event=None):
    app.attributes("-fullscreen", False)

app.bind("<F11>", toggle_fullscreen)   # F11 to toggle fullscreen
app.bind("<Escape>", end_fullscreen)   # Esc to exit fullscreen


app.mainloop()