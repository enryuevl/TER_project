"""
Standalone tester script to simulate how the QC error dialog
from the scan page looks, without running the full app.
"""

from customtkinter import (
    CTk,
    CTkFrame,
    CTkToplevel,
    CTkLabel,
    CTkScrollableFrame,
    CTkButton,
)


def show_qc_error_dialog(parent, qc_errors):
    """
    Local copy of the ScanPage QC error dialog UI, so we can
    preview it without importing the full ScanPage class.
    """
    TOPBAR = "#BF3131"
    SIDEBAR_BTN = "#AC5353"
    HOVER = "#BF3131"
    PANEL_BG = "#F5F5F5"
    LIGHT_TEXT = "#FFEFEF"
    WHITE = "#FFFFFF"

    # --- Dialog Window ---
    dialog = CTkToplevel(parent)
    dialog.title("QC Errors Detected")
    dialog.geometry("560x360")
    dialog.resizable(False, False)

    dialog.transient(parent)
    dialog.grab_set()

    # --- Main container ---
    main_frame = CTkFrame(dialog, fg_color=PANEL_BG, corner_radius=12)
    main_frame.pack(fill="both", expand=True, padx=16, pady=16)

    # --- Header bar ---
    header = CTkFrame(main_frame, fg_color=TOPBAR, corner_radius=10)
    header.pack(fill="x", padx=8, pady=(8, 4))

    CTkLabel(
        header,
        text="Incomplete / Blank Pages Detected",
        font=("Poppins", 16, "bold"),
        text_color=WHITE,
    ).pack(side="left", padx=12, pady=8)

    CTkLabel(
        header,
        text="ERROR",
        font=("Poppins", 11, "bold"),
        text_color=TOPBAR,
        fg_color=LIGHT_TEXT,
        corner_radius=999,
        padx=10,
        pady=4,
    ).pack(side="right", padx=12, pady=8)

    # --- Body ---
    body = CTkFrame(main_frame, fg_color=WHITE, corner_radius=10)
    body.pack(fill="both", expand=True, padx=8, pady=(4, 8))

    CTkLabel(
        body,
        text=(
            "The following documents have missing keys and were discarded.\n"
            "Please rescan these page(s):"
        ),
        font=("Poppins", 12),
        text_color="#333333",
        justify="left",
    ).pack(anchor="w", padx=12, pady=(10, 6))

    # --- Scrollable list of errors ---
    list_frame = CTkScrollableFrame(
        body,
        fg_color=PANEL_BG,
        corner_radius=8,
        height=160,
    )
    list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    if qc_errors:
        for fname, reason in qc_errors:
            CTkLabel(
                list_frame,
                text=f"• {fname} → {reason}",
                font=("Poppins", 11),
                text_color="#333333",
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=2)
    else:
        CTkLabel(
            list_frame,
            text="No details available.",
            font=("Poppins", 11, "italic"),
            text_color="#555555",
        ).pack(pady=10)

    # --- Footer buttons ---
    footer = CTkFrame(main_frame, fg_color=PANEL_BG)
    footer.pack(fill="x", padx=8, pady=(0, 8))

    def close_dialog():
        dialog.destroy()

    CTkButton(
        footer,
        text="OK, I will rescan",
        font=("Poppins", 12, "bold"),
        fg_color=SIDEBAR_BTN,
        hover_color=HOVER,
        text_color=WHITE,
        corner_radius=8,
        width=150,
        command=close_dialog,
    ).pack(side="right", padx=12, pady=4)

    # Center relative to parent
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

    dialog.wait_window(dialog)


def main():
    app = CTk()
    app.title("QC Error Dialog Preview")
    app.geometry("900x600")

    container = CTkFrame(app)
    container.pack(fill="both", expand=True, padx=20, pady=20)

    qc_errors = [
        ("SCAN_001.png", "Missing faculty signature"),
        ("SCAN_002.png", "Answer sheet too faint / not detected"),
        ("SCAN_003.png", "Blank page detected"),
    ]

    # Show dialog on startup
    app.after(100, lambda: show_qc_error_dialog(container, qc_errors))

    app.mainloop()


if __name__ == "__main__":
    main()


