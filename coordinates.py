import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class CoordinateMapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Coordinate Mapper")
        
        # Set initial window size to 80% of screen size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for image
        self.canvas = tk.Canvas(self.main_frame, width=window_width-30, height=window_height-100)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        self.v_scroll = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.h_scroll = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        
        # Create info frame
        self.info_frame = ttk.Frame(root)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create labels for coordinates
        self.coord_label = ttk.Label(self.info_frame, text="Click coordinates: None", font=('Arial', 10))
        self.coord_label.pack(side=tk.LEFT, padx=5)
        
        self.rect_label = ttk.Label(self.info_frame, text="Selection: None", font=('Arial', 10))
        self.rect_label.pack(side=tk.LEFT, padx=5)
        
        # Create buttons
        self.clear_btn = ttk.Button(self.info_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Initialize variables
        self.image = None
        self.photo = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.click_count = 0
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows mousewheel
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux mousewheel up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux mousewheel down
        
        # Load image
        self.load_image()
        
    def on_mousewheel(self, event):
        # Handle mousewheel scrolling
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        
    def load_image(self):
        try:
            # Get the path to the image
            documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
            work_folder = os.path.join(documents_folder, "MyWork")
            scanned_folder = os.path.join(work_folder, "Scanned")
            image_path = os.path.join(scanned_folder, "scan_066.bmp")
            
            print(f"Loading image from: {image_path}")
            
            # Load and resize the image
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                raise Exception("Failed to load image")
                
            # Resize to standard size used in main code
            cv_img = cv2.resize(cv_img, (850, 1550))
            
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            self.image = Image.fromarray(rgb_img)
            
            # Create PhotoImage
            self.photo = ImageTk.PhotoImage(self.image)
            
            # Configure canvas
            self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
            
            # Display image
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            print(f"Image loaded successfully. Size: {self.image.width}x{self.image.height}")
            
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def on_click(self, event):
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.start_x = canvas_x
        self.start_y = canvas_y
        
        # Update coordinate label
        self.coord_label.config(text=f"Click coordinates: ({int(canvas_x)}, {int(canvas_y)})")
        
        # Clear previous rectangle if it exists
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def on_drag(self, event):
        if self.start_x is None:
            return
            
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Clear previous rectangle if it exists
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # Draw new rectangle
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, canvas_x, canvas_y,
            outline='red', width=2
        )
        
        # Update rectangle coordinates label
        x1, y1 = int(min(self.start_x, canvas_x)), int(min(self.start_y, canvas_y))
        x2, y2 = int(max(self.start_x, canvas_x)), int(max(self.start_y, canvas_y))
        self.rect_label.config(text=f"Selection: [{y1}:{y2}, {x1}:{x2}]")
    
    def on_release(self, event):
        # Final update of coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        x1, y1 = int(min(self.start_x, canvas_x)), int(min(self.start_y, canvas_y))
        x2, y2 = int(max(self.start_x, canvas_x)), int(max(self.start_y, canvas_y))
        
        print(f"Selected region: [{y1}:{y2}, {x1}:{x2}]")
    
    def clear_selection(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        self.coord_label.config(text="Click coordinates: None")
        self.rect_label.config(text="Selection: None")
        self.start_x = None
        self.start_y = None

def main():
    root = tk.Tk()
    app = CoordinateMapper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
