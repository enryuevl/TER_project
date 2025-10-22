import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, UnidentifiedImageError
import os, re

# ── Theme / Palette
PRIMARY = "#691612"
PRIMARY_HOVER = "#8E1616"
BG = "#F5F5F5"
CARD_BG = "white"
TEXT = "#1F2937"
TEXT_MUTED = "#6B7280"
BORDER = "#E5E5E5"

ROLES = ["Dean", "Evaluator", "Faculty"]   # Student removed as requested
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ctk.set_appearance_mode("light")


class LoginApp(ctk.CTk):
    def __init__(self, logo_path: str | None = "logo.png"):
        super().__init__()

        self._resize_job = None
        self._width_bucket = None
        self.users: dict[str, dict] = {}

        # Window
        self.title("Camarines Norte State College")
        self.geometry("960x640")
        self.minsize(760, 540)
        self.configure(fg_color=PRIMARY)

        # Fullscreen
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)

        # Fonts
        self.font_title = ctk.CTkFont("Poppins", 28, "bold")
        self.font_subtitle = ctk.CTkFont("Poppins", 14)
        self.font_label = ctk.CTkFont("Poppins", 12)
        self.font_button = ctk.CTkFont("Poppins", 13, "bold")
        self.font_small = ctk.CTkFont("Poppins", 11)

        # Root layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Background
        self.main_frame = ctk.CTkFrame(self, fg_color=BG)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Centering container
        self.center = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.center.grid(row=1, column=0, sticky="nsew")
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_rowconfigure(0, weight=1)
        self.center.grid_rowconfigure(2, weight=1)

        # Stack (header + card)
        self.stack = ctk.CTkFrame(self.center, fg_color="transparent")
        self.stack.grid(row=1, column=0, sticky="n")
        self.stack.grid_columnconfigure(0, weight=1)

        # Header (logo + titles)
        self.header = ctk.CTkFrame(self.stack, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="n", pady=(10, 4))
        self.header.grid_columnconfigure(0, weight=1)

        self.logo_image = None
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(img, size=(96, 96))
                ctk.CTkLabel(self.header, image=self.logo_image, text="").grid(row=0, column=0, pady=(0, 6))
            except (UnidentifiedImageError, OSError):
                self.logo_image = None

        ctk.CTkLabel(self.header, text="Camarines Norte State College",
                     font=self.font_title, text_color=PRIMARY).grid(row=1, column=0, pady=(0, 2))
        ctk.CTkLabel(self.header, text="Automatic Tallying System",
                     font=self.font_subtitle, text_color=TEXT_MUTED).grid(row=2, column=0)

        # Card container
        self.card = ctk.CTkFrame(self.stack, fg_color=CARD_BG, corner_radius=16,
                                 border_width=1, border_color=BORDER)
        self.card.grid(row=1, column=0, sticky="n", pady=(12, 24))
        self.card.grid_columnconfigure(0, weight=1)

        # Build pages
        self._build_login_page()
        self._build_register_page()
        self._show_login()

        # Footer
        self.footer = ctk.CTkLabel(self.main_frame, text="© 2025 Camarines Norte State College",
                                   font=self.font_small, text_color=TEXT_MUTED)
        self.footer.grid(row=2, column=0, pady=(0, 10))

        # Responsive (debounced)
        self.bind("<Configure>", self._on_resize)
        self._apply_responsive()

    # ---------- Login Page ----------
    def _build_login_page(self):
        self.login_page = ctk.CTkFrame(self.card, fg_color="transparent")
        self.login_page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.login_page, text="Sign in to your account",
                     font=self.font_label, text_color=TEXT).grid(row=0, column=0, pady=(18, 8))

        ctk.CTkLabel(self.login_page, text="Email", font=self.font_label, text_color=TEXT)\
            .grid(row=1, column=0, sticky="w", padx=22)
        self.login_email = ctk.CTkEntry(self.login_page, height=40, corner_radius=10,
                                        placeholder_text="Enter your email",
                                        fg_color="white", text_color=TEXT, border_color=BORDER)
        self.login_email.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 10))

        ctk.CTkLabel(self.login_page, text="Password", font=self.font_label, text_color=TEXT)\
            .grid(row=3, column=0, sticky="w", padx=22)

        pw_row = ctk.CTkFrame(self.login_page, fg_color="transparent")
        pw_row.grid(row=4, column=0, sticky="ew", padx=22, pady=(4, 6))
        pw_row.grid_columnconfigure(0, weight=1)

        self.login_password = ctk.CTkEntry(pw_row, height=40, corner_radius=10,
                                           placeholder_text="Enter your password",
                                           fg_color="white", text_color=TEXT, border_color=BORDER, show="•")
        self.login_password.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._login_pw_visible = False
        self.login_toggle_pw = ctk.CTkButton(pw_row, text="Show", width=74, height=40,
                                             corner_radius=10, fg_color="white", hover_color="#F3F4F6",
                                             text_color=TEXT, font=self.font_small,
                                             command=lambda: self._toggle_pw(self.login_password, "login"))
        self.login_toggle_pw.grid(row=0, column=1)

        self.login_error = ctk.CTkLabel(self.login_page, text="", font=self.font_small, text_color="#B91C1C")
        self.login_error.grid(row=5, column=0, sticky="w", padx=22, pady=(2, 2))

        self.btn_login = ctk.CTkButton(self.login_page, text="Log In", height=42, corner_radius=12,
                                       font=self.font_button, fg_color=PRIMARY,
                                       hover_color=PRIMARY_HOVER, text_color="white",
                                       command=self._handle_login)
        self.btn_login.grid(row=6, column=0, sticky="ew", padx=22, pady=(8, 6))

        links = ctk.CTkFrame(self.login_page, fg_color="transparent")
        links.grid(row=7, column=0, sticky="ew", padx=18, pady=(6, 8))
        links.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(links, text="Create an Account",
                      fg_color="transparent", hover_color="#F5F5F5",
                      text_color=PRIMARY, font=self.font_small,
                      command=self._show_register).grid(row=0, column=0, sticky="w", padx=4)

        ctk.CTkButton(links, text="Forgot your password?",
                      fg_color="transparent", hover_color="#F5F5F5",
                      text_color=PRIMARY, font=self.font_small,
                      command=lambda: messagebox.showinfo("Forgot Password",
                                                          "Please contact the administrator to reset your password.")
                      ).grid(row=0, column=1, sticky="e", padx=4)

        # Enter to submit
        self.login_email.bind("<Return>", lambda e: self._handle_login())
        self.login_password.bind("<Return>", lambda e: self._handle_login())

    # ---------- Register Page ----------
    def _build_register_page(self):
        self.register_page = ctk.CTkFrame(self.card, fg_color="transparent")
        self.register_page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.register_page, text="Create your account",
                     font=self.font_label, text_color=TEXT).grid(row=0, column=0, pady=(18, 8))

        # Full Name
        ctk.CTkLabel(self.register_page, text="Full Name", font=self.font_label, text_color=TEXT)\
            .grid(row=1, column=0, sticky="w", padx=22)
        self.reg_name = ctk.CTkEntry(self.register_page, height=40, corner_radius=10,
                                     placeholder_text="e.g., Juan Dela Cruz",
                                     fg_color="white", text_color=TEXT, border_color=BORDER)
        self.reg_name.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Email
        ctk.CTkLabel(self.register_page, text="Email", font=self.font_label, text_color=TEXT)\
            .grid(row=3, column=0, sticky="w", padx=22)
        self.reg_email = ctk.CTkEntry(self.register_page, height=40, corner_radius=10,
                                      placeholder_text="e.g., name@example.com",
                                      fg_color="white", text_color=TEXT, border_color=BORDER)
        self.reg_email.grid(row=4, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Password row + toggle
        ctk.CTkLabel(self.register_page, text="Password", font=self.font_label, text_color=TEXT)\
            .grid(row=5, column=0, sticky="w", padx=22)
        pw_row = ctk.CTkFrame(self.register_page, fg_color="transparent")
        pw_row.grid(row=6, column=0, sticky="ew", padx=22, pady=(4, 6))
        pw_row.grid_columnconfigure(0, weight=1)

        self.reg_password = ctk.CTkEntry(pw_row, height=40, corner_radius=10,
                                         placeholder_text="At least 8 characters",
                                         fg_color="white", text_color=TEXT, border_color=BORDER, show="•")
        self.reg_password.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._reg_pw_visible = False
        self.reg_toggle_pw = ctk.CTkButton(pw_row, text="Show", width=74, height=40,
                                           corner_radius=10, fg_color="white", hover_color="#F3F4F6",
                                           text_color=TEXT, font=self.font_small,
                                           command=lambda: self._toggle_pw(self.reg_password, "reg"))
        self.reg_toggle_pw.grid(row=0, column=1)

        # Confirm password
        ctk.CTkLabel(self.register_page, text="Confirm Password", font=self.font_label, text_color=TEXT)\
            .grid(row=7, column=0, sticky="w", padx=22)
        self.reg_confirm = ctk.CTkEntry(self.register_page, height=40, corner_radius=10,
                                        placeholder_text="Re-type your password",
                                        fg_color="white", text_color=TEXT, border_color=BORDER, show="•")
        self.reg_confirm.grid(row=8, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Role (✅ non-transparent dropdown + themed)
        ctk.CTkLabel(self.register_page, text="Role", font=self.font_label, text_color=TEXT)\
            .grid(row=9, column=0, sticky="w", padx=22)
        self.reg_role = ctk.CTkOptionMenu(
            self.register_page, values=ROLES, height=40, corner_radius=10,
            fg_color="white",               # button background (not transparent)
            text_color=TEXT,
            button_color=PRIMARY,           # button color
            button_hover_color=PRIMARY_HOVER,
            font=self.font_label,
            dropdown_fg_color="white",      # dropdown panel background (solid)
            dropdown_hover_color="#F3F4F6", # hover color for items
            dropdown_text_color=TEXT        # text color in dropdown items
        )
        self.reg_role.grid(row=10, column=0, sticky="ew", padx=22, pady=(4, 10))
        self.reg_role.set(ROLES[0])

        self.reg_error = ctk.CTkLabel(self.register_page, text="", font=self.font_small, text_color="#B91C1C")
        self.reg_error.grid(row=11, column=0, sticky="w", padx=22, pady=(2, 2))

        # Buttons
        btn_row = ctk.CTkFrame(self.register_page, fg_color="transparent")
        btn_row.grid(row=12, column=0, sticky="ew", padx=22, pady=(6, 12))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_register = ctk.CTkButton(btn_row, text="Register", height=42, corner_radius=12,
                                          font=self.font_button, fg_color=PRIMARY,
                                          hover_color=PRIMARY_HOVER, text_color="white",
                                          command=self._handle_register)
        self.btn_register.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(btn_row, text="Back to Login", height=42, corner_radius=12,
                      font=self.font_button, fg_color="white",
                      hover_color="#F3F4F6", text_color=PRIMARY,
                      command=self._show_login).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Enter to submit
        for w in (self.reg_name, self.reg_email, self.reg_password, self.reg_confirm):
            w.bind("<Return>", lambda e: self._handle_register())

    # ---------- Page switches ----------
    def _show_login(self):
        self.register_page.grid_forget()
        self.login_page.grid(row=0, column=0, sticky="n")
        self._apply_responsive()

    def _show_register(self):
        self.login_page.grid_forget()
        self.register_page.grid(row=0, column=0, sticky="n")
        self._apply_responsive()

    # ---------- Handlers ----------
    def _handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        pw = self.reg_password.get()
        pw2 = self.reg_confirm.get()
        role = self.reg_role.get()

        self.reg_error.configure(text="")

        if not all([name, email, pw, pw2, role]):
            self.reg_error.configure(text="Please fill in all fields.")
            return
        if not EMAIL_RE.match(email):
            self.reg_error.configure(text="Invalid email format.")
            return
        if len(pw) < 8:
            self.reg_error.configure(text="Password must be at least 8 characters.")
            return
        if pw != pw2:
            self.reg_error.configure(text="Passwords do not match.")
            return
        if email in self.users:
            self.reg_error.configure(text="Email is already registered.")
            return

        # Save to in-memory store
        self.users[email] = {"name": name, "password": pw, "role": role}

        messagebox.showinfo("Registered", f"Account created as {role}. You can now login.")
        self._show_login()
        # Prefill login
        self.login_email.delete(0, "end")
        self.login_email.insert(0, email)
        self.login_password.delete(0, "end")
        self.login_password.insert(0, pw)

    def _handle_login(self):
        email = self.login_email.get().strip()
        pw = self.login_password.get()

        self.login_error.configure(text="")

        if not email or not pw:
            self.login_error.configure(text="Please enter both email and password.")
            return
        if not EMAIL_RE.match(email):
            self.login_error.configure(text="Invalid email format.")
            return
        if email not in self.users or self.users[email]["password"] != pw:
            self.login_error.configure(text="Invalid email or password.")
            return

        role = self.users[email]["role"]
        self._redirect_to_role(role, self.users[email]["name"], email)

    # ---------- Role redirect (no DB) ----------
    def _redirect_to_role(self, role: str, name: str, email: str):
        self.withdraw()
        dash = ctk.CTkToplevel(self)
        dash.title(f"{role} Dashboard – CNSC ATS")
        dash.geometry("900x560")
        dash.minsize(720, 480)

        dash.grid_rowconfigure(0, weight=0)
        dash.grid_rowconfigure(1, weight=1)
        dash.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(dash, fg_color=BG)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text=f"Welcome, {name} ({role})",
                             font=ctk.CTkFont("Poppins", 20, "bold"),
                             text_color=PRIMARY)
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        subtitle = ctk.CTkLabel(header, text=f"Email: {email}",
                                font=ctk.CTkFont("Poppins", 12),
                                text_color=TEXT_MUTED)
        subtitle.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        body = ctk.CTkFrame(dash, fg_color="white", corner_radius=12, border_width=1, border_color=BORDER)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(body,
                     text=f"This is a placeholder {role} dashboard.\nHook your {role}-specific UI here.",
                     font=self.font_label, text_color=TEXT, justify="center").grid(row=0, column=0)

        def _logout():
            dash.destroy()
            self.deiconify()

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.grid(row=0, column=1, rowspan=2, sticky="e", padx=12)
        ctk.CTkButton(btn_row, text="Logout", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                      text_color="white", corner_radius=10,
                      command=_logout).grid(row=0, column=0, padx=4, pady=8)

        dash.protocol("WM_DELETE_WINDOW", _logout)

    # ---------- Shared helpers ----------
    def _toggle_pw(self, entry: ctk.CTkEntry, kind: str):
        if kind == "login":
            self._login_pw_visible = not self._login_pw_visible
            entry.configure(show="" if self._login_pw_visible else "•")
            self.login_toggle_pw.configure(text="Hide" if self._login_pw_visible else "Show")
        else:
            self._reg_pw_visible = not self._reg_pw_visible
            entry.configure(show="" if self._reg_pw_visible else "•")
            self.reg_toggle_pw.configure(text="Hide" if self._reg_pw_visible else "Show")

    def _toggle_fullscreen(self, _=None):
        self.attributes("-fullscreen", not bool(self.attributes("-fullscreen")))

    def _exit_fullscreen(self, _=None):
        if self.attributes("-fullscreen"):
            self.attributes("-fullscreen", False)

    # ---------- Responsive ----------
    def _on_resize(self, _evt=None):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._apply_responsive)

    def _apply_responsive(self):
        self._resize_job = None
        w = max(self.winfo_width(), 600)  # guard if geometry not yet set

        # Bucket targets (preferred max widths)
        if w < 840:
            bucket = "sm"; bucket_card_w = 440; bucket_entry_w = 380; logo = 84
        elif w < 1080:
            bucket = "md"; bucket_card_w = 520; bucket_entry_w = 440; logo = 96
        else:
            bucket = "lg"; bucket_card_w = 600; bucket_entry_w = 520; logo = 110

        # Clamp widths to available space (👍 works great when not fullscreen)
        max_card_w = max(360, min(bucket_card_w, w - 160))     # keep ~80px margin on each side
        entry_w = max(300, min(bucket_entry_w, max_card_w - 80))

        if bucket == self._width_bucket and getattr(self, "_last_card_w", None) == max_card_w:
            return
        self._width_bucket = bucket
        self._last_card_w = max_card_w

        self.card.configure(width=max_card_w)

        # Active page fields
        if self.login_page.winfo_ismapped():
            self.login_email.configure(width=entry_w)
            self.login_password.configure(width=entry_w - 80)  # leave room for toggle
            self.btn_login.configure(width=entry_w)

        if self.register_page.winfo_ismapped():
            for wdg in (self.reg_name, self.reg_email, self.reg_password, self.reg_confirm,
                        self.btn_register, self.reg_role):
                wdg.configure(width=entry_w)

        if self.logo_image:
            self.logo_image.configure(size=(logo, logo))


if __name__ == "__main__":
    app = LoginApp(logo_path="logo.png")
    app.mainloop()
