from customtkinter import *
from tkinter import messagebox
import db


class AccountsPage:
    def __init__(self, master):
        """Accounts management page (Faculty & Departments only)."""
        self.master = master
        self.tab_buttons = {}
        self.current_tab = None

        self._build_ui()

    # ---------------- UI ---------------- #
    def _build_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.container = CTkFrame(self.master, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        CTkLabel(
            self.container,
            text="Accounts Management",
            font=("Arial", 24, "bold"),
            text_color="#691612"
        ).pack(pady=(0, 20))

        # Tabs
        self.tab_frame = CTkFrame(self.container, fg_color="transparent")
        self.tab_frame.pack(fill="x", pady=(0, 20))

        # Content
        self.content_frame = CTkFrame(self.container, fg_color="#FFFFFF", corner_radius=10)
        self.content_frame.pack(fill="both", expand=True)

        # Success message
        self.success_label = CTkLabel(
            self.container, text="", font=("Arial", 14, "bold"), text_color="#FFFFFF"
        )
        self.success_label.pack_forget()

        # Build tab buttons
        for i, entity in enumerate(["Faculty", "Departments"]):
            btn = CTkButton(
                self.tab_frame,
                text=entity,
                command=lambda e=entity: self.show_tab(e),
                fg_color="#AC5353" if i == 0 else "#F1F3F5",
                text_color="#FFFFFF" if i == 0 else "#333333",
                hover_color="#BF3131" if i == 0 else "#E9ECEF",
                width=160,
                height=35,
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons[entity] = btn

        # Default tab
        self.show_tab("Faculty")

    def show_success(self, msg):
        self.success_label.configure(text=msg, fg_color="#10B981")
        self.success_label.pack(fill="x", pady=(0, 10))
        self.container.after(3000, lambda: self.success_label.pack_forget())

    def show_tab(self, name):
        # Highlight active tab
        for tab, btn in self.tab_buttons.items():
            if tab == name:
                btn.configure(fg_color="#AC5353", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#F1F3F5", text_color="#333333")

        # Reset content
        for w in self.content_frame.winfo_children():
            w.destroy()

        if name == "Faculty":
            self._faculty_form()
        elif name == "Departments":
            self._department_form()

    # ---------------- FORMS ---------------- #
    def _faculty_form(self):
        frame = CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=30)

        CTkLabel(frame, text="Add Faculty Member",
                 font=("Arial", 20, "bold"), text_color="#691612").pack(pady=(0, 20))

        # Name
        name_entry = CTkEntry(frame, placeholder_text="Faculty Name",
                              height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=10)

        # Department dropdown
        dept_var, dept_options = StringVar(), []
        try:
            with db.connect() as conn:
                rows = conn.execute("SELECT id, name FROM departments").fetchall()
                dept_options = [r[1] for r in rows]
        except Exception as e:
            print("DB error:", e)

        if dept_options:
            dept_dropdown = CTkOptionMenu(frame, variable=dept_var,
                                          values=dept_options, height=35, font=("Arial", 14))
            dept_dropdown.pack(fill="x", pady=10)
            dept_dropdown.set(dept_options[0])
        else:
            CTkLabel(frame, text="No departments available. Create one first.",
                     text_color="#6C757D").pack()

        # Rank
        rank_var = StringVar(value="Instructor")
        CTkOptionMenu(frame, variable=rank_var,
                      values=["Instructor", "Assistant Professor",
                              "Associate Professor", "Professor"],
                      height=35, font=("Arial", 14)).pack(fill="x", pady=10)

        # Subrank
        subrank_var = StringVar(value="I")
        CTkOptionMenu(frame, variable=subrank_var,
                      values=["I", "II", "III", "IV"],
                      height=35, font=("Arial", 14)).pack(fill="x", pady=10)

        def submit():
            name, dept, rank, subrank = name_entry.get(), dept_var.get(), rank_var.get(), subrank_var.get()
            if not name:
                messagebox.showerror("Error", "Enter faculty name")
                return
            try:
                with db.connect() as conn:
                    dept_id = conn.execute("SELECT id FROM departments WHERE name=?", (dept,)).fetchone()
                    if not dept_id:
                        messagebox.showerror("Error", "Department not found")
                        return
                    conn.execute(
                        "INSERT INTO faculty (name, department_id, rank, subrank) VALUES (?,?,?,?)",
                        (name, dept_id[0], rank, subrank)
                    )
                    conn.commit()
                self.show_success(f"Faculty '{name}' added successfully!")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(frame, text="Add Faculty", command=submit,
                  fg_color="#691612", hover_color="#AC5353",
                  text_color="#FFF", height=40,
                  font=("Arial", 14, "bold")).pack(pady=30)

    def _department_form(self):
        frame = CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=30)

        CTkLabel(frame, text="Add Department",
                 font=("Arial", 20, "bold"), text_color="#691612").pack(pady=(0, 20))

        name_entry = CTkEntry(frame, placeholder_text="Department Name",
                              height=35, font=("Arial", 14))
        name_entry.pack(fill="x", pady=10)

        def submit():
            name = name_entry.get()
            if not name:
                messagebox.showerror("Error", "Enter department name")
                return
            try:
                with db.connect() as conn:
                    conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
                    conn.commit()
                self.show_success(f"Department '{name}' added successfully!")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        CTkButton(frame, text="Add Department", command=submit,
                  fg_color="#691612", hover_color="#AC5353",
                  text_color="#FFF", height=40,
                  font=("Arial", 14, "bold")).pack(pady=30)
