"""
Embed Excel window inside a tkinter window using Windows COM automation.

This creates an actual Excel window embedded in tkinter, not just displaying data.
Requires: Excel installed on Windows, pywin32 (win32com)
"""

from customtkinter import *
from tkinter import filedialog, messagebox
import win32com.client
import pythoncom
import win32gui
import win32con
import threading
import os


class ExcelEmbeddedViewer:
    """Embed Excel application window inside a tkinter window."""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.excel_app = None
        self.excel_window = None
        self.embedded_frame = None
        self.file_path = None
        
    def open_excel_file(self, file_path=None):
        """Open Excel file and embed it in the parent window."""
        
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
        
        if not file_path or not os.path.exists(file_path):
            return False
        
        self.file_path = file_path
        
        try:
            # Initialize COM in this thread
            pythoncom.CoInitialize()
            
            # Create Excel application
            self.excel_app = win32com.client.Dispatch("Excel.Application")
            self.excel_app.Visible = True
            self.excel_app.DisplayAlerts = False  # Suppress Excel alerts
            
            # Open the workbook
            workbook = self.excel_app.Workbooks.Open(os.path.abspath(file_path))
            
            # Get the Excel window handle
            excel_hwnd = self.excel_app.Hwnd
            
            # Wait a moment for Excel to fully initialize
            import time
            time.sleep(0.5)
            
            # Embed Excel window into tkinter
            self._embed_excel_window(excel_hwnd)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Excel file:\n{str(e)}")
            if self.excel_app:
                try:
                    self.excel_app.Quit()
                except:
                    pass
            return False
    
    def _embed_excel_window(self, excel_hwnd):
        """Embed Excel window into a tkinter frame."""
        
        # Create a frame to hold the embedded Excel window
        if self.embedded_frame:
            self.embedded_frame.destroy()
        
        self.embedded_frame = CTkFrame(self.parent)
        self.embedded_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get the frame's window handle (tkinter window)
        # Note: This requires getting the actual HWND of the tkinter frame
        # For customtkinter, we need to get the underlying tkinter widget
        
        # Get the tkinter widget from CTkFrame
        tk_widget = self.embedded_frame.winfo_id()
        
        # Get parent window handle
        parent_hwnd = win32gui.FindWindow(None, self.parent.title())
        if parent_hwnd == 0:
            # Try to get it from the tk widget
            try:
                parent_hwnd = self.parent.winfo_id()
            except:
                pass
        
        # Set Excel window as child of our frame
        # Get the frame's actual HWND
        frame_hwnd = None
        def find_frame_hwnd(hwnd, extra):
            if win32gui.GetParent(hwnd) == parent_hwnd:
                class_name = win32gui.GetClassName(hwnd)
                if "TkFrame" in class_name or "Frame" in class_name:
                    extra.append(hwnd)
            return True
        
        frame_hwnds = []
        win32gui.EnumChildWindows(parent_hwnd, find_frame_hwnd, frame_hwnds)
        
        if frame_hwnds:
            frame_hwnd = frame_hwnds[-1]  # Get the last (most recent) frame
            
            # Set Excel window parent to our frame
            win32gui.SetParent(excel_hwnd, frame_hwnd)
            
            # Get frame dimensions
            frame_rect = win32gui.GetClientRect(frame_hwnd)
            frame_width = frame_rect[2] - frame_rect[0]
            frame_height = frame_rect[1] - frame_rect[1]
            
            # Resize and position Excel window to fill frame
            win32gui.SetWindowPos(
                excel_hwnd,
                win32con.HWND_TOP,
                0, 0,
                frame_width, frame_height,
                win32con.SWP_SHOWWINDOW
            )
            
            # Store for cleanup
            self.excel_window = excel_hwnd
            self.frame_hwnd = frame_hwnd
            
            # Update window position when frame is resized
            self._setup_resize_handler()
    
    def _setup_resize_handler(self):
        """Set up handler to resize Excel window when frame is resized."""
        def on_resize(event=None):
            if self.excel_window and self.frame_hwnd:
                try:
                    frame_rect = win32gui.GetClientRect(self.frame_hwnd)
                    frame_width = frame_rect[2] - frame_rect[0]
                    frame_height = frame_rect[3] - frame_rect[1]
                    
                    win32gui.SetWindowPos(
                        self.excel_window,
                        win32con.HWND_TOP,
                        0, 0,
                        frame_width, frame_height,
                        win32con.SWP_SHOWWINDOW
                    )
                except:
                    pass
        
        # Bind resize event
        self.embedded_frame.bind("<Configure>", on_resize)
        self.parent.bind("<Configure>", on_resize)
    
    def close(self):
        """Close Excel and cleanup."""
        if self.excel_app:
            try:
                self.excel_app.Quit()
                self.excel_app = None
            except:
                pass
        
        if self.embedded_frame:
            self.embedded_frame.destroy()
            self.embedded_frame = None
        
        try:
            pythoncom.CoUninitialize()
        except:
            pass


# ========== SIMPLER ALTERNATIVE: Open Excel in separate window but controlled ==========
def open_excel_controlled(file_path=None):
    """
    Alternative: Open Excel in a separate window but control it from tkinter.
    This is simpler and more reliable than embedding.
    """
    
    if not file_path:
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
    
    if not file_path or not os.path.exists(file_path):
        return
    
    try:
        pythoncom.CoInitialize()
        
        # Create Excel application
        excel_app = win32com.client.Dispatch("Excel.Application")
        excel_app.Visible = True
        excel_app.DisplayAlerts = False
        
        # Open workbook
        workbook = excel_app.Workbooks.Open(os.path.abspath(file_path))
        
        # Get Excel window and bring it to front
        excel_hwnd = excel_app.Hwnd
        win32gui.SetForegroundWindow(excel_hwnd)
        win32gui.ShowWindow(excel_hwnd, win32con.SW_MAXIMIZE)
        
        messagebox.showinfo(
            "Excel Opened",
            f"Excel file opened in separate window.\n\n"
            f"File: {os.path.basename(file_path)}\n"
            f"Close Excel when done."
        )
        
        # Note: Excel will stay open until user closes it or we call excel_app.Quit()
        # You can add a cleanup function if needed
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open Excel:\n{str(e)}")
        try:
            pythoncom.CoUninitialize()
        except:
            pass


# ========== DEMO WINDOW ==========
if __name__ == "__main__":
    app = CTk()
    app.title("Excel Embedded Viewer Demo")
    app.geometry("1000x700")
    
    # Header
    header = CTkFrame(app, fg_color="#BF3131", height=60)
    header.pack(fill="x")
    CTkLabel(
        header,
        text="Excel Embedded Viewer",
        font=("Poppins", 18, "bold"),
        text_color="#FFFFFF"
    ).pack(side="left", padx=20, pady=15)
    
    # Buttons frame
    buttons_frame = CTkFrame(app, fg_color="transparent")
    buttons_frame.pack(fill="x", padx=10, pady=10)
    
    viewer = ExcelEmbeddedViewer(app)
    
    def open_embedded():
        viewer.open_excel_file()
    
    def open_separate():
        open_excel_controlled()
    
    CTkButton(
        buttons_frame,
        text="Open Excel (Embedded)",
        command=open_embedded,
        width=200,
        height=40,
        font=("Poppins", 12)
    ).pack(side="left", padx=10)
    
    CTkButton(
        buttons_frame,
        text="Open Excel (Separate Window)",
        command=open_separate,
        width=200,
        height=40,
        font=("Poppins", 12)
    ).pack(side="left", padx=10)
    
    def on_closing():
        viewer.close()
        app.destroy()
    
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

