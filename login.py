import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, UnidentifiedImageError
import os, sqlite3, hashlib, hmac, base64
import bcrypt
import main
import utils

# ── Theme / Palette
PRIMARY = "#691612"
PRIMARY_HOVER = "#8E1616"
BG = "#F5F5F5"
CARD_BG = "white"
TEXT = "#1F2937"
TEXT_MUTED = "#6B7280"
BORDER = "#E5E5E5"

# ── Roles shown in UI → saved to DB in lowercase
ROLES_UI = ["Admin", "Dean", "Operator"]
ROLE_MAP = {"Admin": "admin", "Dean": "dean", "Operator": "operator"}
documents_path = os.path.join(os.environ['USERPROFILE'], 'Documents', 'MyWork')
DB_PATH = os.path.join(documents_path, 'ter_db2.sqlite')
# ── Password hashing helpers
try:
    
    def hash_password(pw: str) -> str:
        return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    def verify_password(pw: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
except Exception:
    # Fallback: PBKDF2-HMAC (salted). Format: pbkdf2$<salt b64>$<hash b64>
    def _pbkdf2(pw: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 200_000, dklen=32)
    def hash_password(pw: str) -> str:
        salt = os.urandom(16)
        dk = _pbkdf2(pw, salt)
        return "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()
    def verify_password(pw: str, hashed: str) -> bool:
        try:
            algo, b64salt, b64hash = hashed.split("$", 2)
            if algo != "pbkdf2":
                return False
            salt = base64.b64decode(b64salt)
            expect = base64.b64decode(b64hash)
            cand = _pbkdf2(pw, salt)
            return hmac.compare_digest(cand, expect)
        except Exception:
            return False

ctk.set_appearance_mode("light")


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class LoginApp(ctk.CTk):
    def __init__(self, logo_path: str | None = "logo.png"):
        super().__init__()

        self._resize_job = None
        self._width_bucket = None
        self.departments = []          # list[(id, name)]
        self.dept_name_to_id = {}      # name -> id

        # Window
        self.title("Camarines Norte State College")
        self.geometry("960x840")
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

        # Load departments from DB before building forms
        self._load_departments()

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
        # Center the window on screen
        # Center window after full render
        self.after(10, lambda: self.after(10, self._center_on_screen))



    # ---------- DB utils ----------
    def _load_departments(self):
        """Populate self.departments and self.dept_name_to_id from DB."""
        try:
            with db_connect() as conn:
                rows = conn.execute("SELECT id, name FROM departments ORDER BY name;").fetchall()
                self.departments = [(r["id"], r["name"]) for r in rows]
                self.dept_name_to_id = {name: did for did, name in self.departments}
        except sqlite3.Error as e:
            self.departments = []
            self.dept_name_to_id = {}
            messagebox.showerror("Database Error", f"Failed to load departments:\n{e}")

    # ---------- Login Page ----------
    def _build_login_page(self):
        self.login_page = ctk.CTkFrame(self.card, fg_color="transparent")
        self.login_page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.login_page, text="Sign in to your account",
                     font=self.font_label, text_color=TEXT).grid(row=0, column=0, pady=(18, 8))

        ctk.CTkLabel(self.login_page, text="Username", font=self.font_label, text_color=TEXT)\
            .grid(row=1, column=0, sticky="w", padx=22)
        self.login_username = ctk.CTkEntry(self.login_page, height=40, corner_radius=10,
                                           placeholder_text="Enter your username",
                                           fg_color="white", text_color=TEXT, border_color=BORDER)
        self.login_username.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 10))

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
        self.login_username.bind("<Return>", lambda e: self._handle_login())
        self.login_password.bind("<Return>", lambda e: self._handle_login())

    # ---------- Register Page ----------
    def _build_register_page(self):
        self.register_page = ctk.CTkFrame(self.card, fg_color="transparent")
        self.register_page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.register_page, text="Create your account",
                     font=self.font_label, text_color=TEXT).grid(row=0, column=0, pady=(18, 8))

        # Username
        ctk.CTkLabel(self.register_page, text="Username", font=self.font_label, text_color=TEXT)\
            .grid(row=1, column=0, sticky="w", padx=22)
        self.reg_username = ctk.CTkEntry(self.register_page, height=40, corner_radius=10,
                                         placeholder_text="e.g., your_username",
                                         fg_color="white", text_color=TEXT, border_color=BORDER)
        self.reg_username.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Password + confirm
        ctk.CTkLabel(self.register_page, text="Password", font=self.font_label, text_color=TEXT)\
            .grid(row=3, column=0, sticky="w", padx=22)
        pw_row = ctk.CTkFrame(self.register_page, fg_color="transparent")
        pw_row.grid(row=4, column=0, sticky="ew", padx=22, pady=(4, 6))
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

        ctk.CTkLabel(self.register_page, text="Confirm Password", font=self.font_label, text_color=TEXT)\
            .grid(row=5, column=0, sticky="w", padx=22)
        self.reg_confirm = ctk.CTkEntry(self.register_page, height=40, corner_radius=10,
                                        placeholder_text="Re-type your password",
                                        fg_color="white", text_color=TEXT, border_color=BORDER, show="•")
        self.reg_confirm.grid(row=6, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Department (dropdown from DB)
        ctk.CTkLabel(self.register_page, text="Department", font=self.font_label, text_color=TEXT)\
            .grid(row=7, column=0, sticky="w", padx=22)
        dept_names = [name for _, name in self.departments] or ["(No departments found)"]
        self.reg_department = ctk.CTkOptionMenu(
            self.register_page, values=dept_names, height=40, corner_radius=10,
            fg_color="white", text_color=TEXT, button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER, font=self.font_label,
            dropdown_fg_color="white", dropdown_hover_color="#F3F4F6",
            dropdown_text_color=TEXT
        )
        if dept_names:
            self.reg_department.set(dept_names[0])
        self.reg_department.grid(row=8, column=0, sticky="ew", padx=22, pady=(4, 10))

        # Role (Admin/Dean/Operator)
        ctk.CTkLabel(self.register_page, text="Role", font=self.font_label, text_color=TEXT)\
            .grid(row=9, column=0, sticky="w", padx=22)
        self.reg_role = ctk.CTkOptionMenu(
            self.register_page, values=ROLES_UI, height=40, corner_radius=10,
            fg_color="white", text_color=TEXT, button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER, font=self.font_label,
            dropdown_fg_color="white", dropdown_hover_color="#F3F4F6",
            dropdown_text_color=TEXT, command=self._on_role_change
        )
        self.reg_role.grid(row=10, column=0, sticky="ew", padx=22, pady=(4, 10))
        self.reg_role.set(ROLES_UI[0])  # default "Admin" to demonstrate dept disabling
        self._on_role_change(ROLES_UI[0])

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
        for w in (self.reg_username, self.reg_password, self.reg_confirm):
            w.bind("<Return>", lambda e: self._handle_register())

    # Enable/disable department depending on role
    def _on_role_change(self, choice: str):
        role = ROLE_MAP.get(choice, "operator")
        if role == "admin":
            self.reg_department.configure(state="disabled")
        else:
            self.reg_department.configure(state="normal")

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
        username = self.reg_username.get().strip()
        pw = self.reg_password.get()
        pw2 = self.reg_confirm.get()
        role_ui = self.reg_role.get()
        role = ROLE_MAP.get(role_ui, "operator")

        self.reg_error.configure(text="")

        if not username or not pw or not pw2 or not role:
            self.reg_error.configure(text="Please fill in all fields.")
            return
        if len(pw) < 8:
            self.reg_error.configure(text="Password must be at least 8 characters.")
            return
        if pw != pw2:
            self.reg_error.configure(text="Passwords do not match.")
            return

        # Department handling
        department_id = None
        if role != "admin":
            if not self.departments:
                self.reg_error.configure(text="No departments available. Contact admin.")
                return
            dept_name = self.reg_department.get()
            department_id = self.dept_name_to_id.get(dept_name)
            if department_id is None:
                self.reg_error.configure(text="Please select a department.")
                return

        # Insert into DB
        try:
            with db_connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (username, password_hash, role, department_id, is_active, created_at) "
                    "VALUES (?, ?, ?, ?, 1, datetime('now'))",
                    (username, hash_password(pw), role, department_id)
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            # likely UNIQUE(username) violation
            self.reg_error.configure(text="Username is already taken.")
            return
        except sqlite3.Error as e:
            self.reg_error.configure(text=f"Database error: {e}")
            return

        messagebox.showinfo("Registered", f"Account created as {role_ui}. You can now log in.")
        # Prefill login
        self._show_login()
        self.login_username.delete(0, "end")
        self.login_username.insert(0, username)
        self.login_password.delete(0, "end")
        self.login_password.insert(0, pw)

    def _handle_login(self):
        username = self.login_username.get().strip()
        pw = self.login_password.get()

        self.login_error.configure(text="")

        if not username or not pw:
            self.login_error.configure(text="Please enter both username and password.")
            return

        try:
            with db_connect() as conn:
                user = conn.execute(
                    "SELECT id, username, password_hash, role, is_active, department_id FROM users WHERE username=?",
                    (username,)
                ).fetchone()
                if not user:
                    self.login_error.configure(text="Invalid username or password.")
                    return
                if not user["is_active"]:
                    self.login_error.configure(text="Account disabled. Contact admin.")
                    return
                if not verify_password(pw, user["password_hash"]):
                    self.login_error.configure(text="Invalid username or password.")
                    return

                # Update last_login_at
                conn.execute("UPDATE users SET last_login_at = datetime('now') WHERE id=?", (user["id"],))
                conn.commit()
        except sqlite3.Error as e:
            self.login_error.configure(text=f"Database error: {e}")
            return

        role = user["role"]
        dept_id = user["department_id"]  # may be None for admin
        utils.set_current_user(name=username, role=role, department_id=dept_id)
        self._redirect_to_role(role, username, dept_id)

    # ---------- Role redirect (placeholder) ----------
    def _redirect_to_role(self, role: str, username: str, department_id: int | None):
        # Close login window, then launch the main app with a callback that reopens login on logout
        self.destroy()

        def _back_to_login():
            try:
                app = LoginApp(logo_path="logo.png")
                app.mainloop()
            except Exception as exc:  # guard against unexpected UI errors
                print(f"Failed to reopen login: {exc}")

        main.create_app(
            role=role,
            username=username,
            department_id=department_id,
            on_logout=_back_to_login,
        )


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

        # Clamp widths to available space
        max_card_w = max(360, min(bucket_card_w, w - 160))
        entry_w = max(300, min(bucket_entry_w, max_card_w - 80))

        if bucket == self._width_bucket and getattr(self, "_last_card_w", None) == max_card_w:
            return
        self._width_bucket = bucket
        self._last_card_w = max_card_w

        self.card.configure(width=max_card_w)

        # Active page fields
        if self.login_page.winfo_ismapped():
            self.login_username.configure(width=entry_w)
            self.login_password.configure(width=entry_w - 80)  # leave room for toggle
            self.btn_login.configure(width=entry_w)

        if self.register_page.winfo_ismapped():
            for wdg in (self.reg_username, self.reg_password, self.reg_confirm,
                        self.btn_register, self.reg_role, self.reg_department):
                wdg.configure(width=entry_w)

        if self.logo_image:
            self.logo_image.configure(size=(logo, logo))

    def _center_on_screen(self):
        self.update_idletasks()  # force geometry calculation

        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # Compute perfect center
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        # Apply new geometry without resizing
        self.geometry(f"{w}x{h}+{x}+{y}")

    
if __name__ == "__main__":
    app = LoginApp(logo_path="logo.png")
    app.mainloop()
