import cv2
import numpy as np

import cv2
import numpy as np

# --- Current user context for logging ----------------------------------------
CURRENT_USER = {"name": None, "role": None, "department_id": None}

def set_current_user(name: str | None, role: str | None, department_id: int | None = None):
    global CURRENT_USER
    CURRENT_USER = {"name": name, "role": role, "department_id": department_id}

def get_current_user():
    return CURRENT_USER

# --- Line and shaded area detection utilities ---------------------------------
def detect_vertical_lines(section_img, section_name="Section"):
    """
    Process the section image to detect vertical lines.
    Returns the output image (with drawn lines), a list of filtered x-coordinates,
    and a list of column ranges (each as a tuple: (start_x, end_x)).
    """
    # Convert to grayscale
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast
    gray = cv2.equalizeHist(gray)
    
    # Invert to make lines white
    gray = cv2.bitwise_not(gray)
    
    # Binarize image with adaptive threshold
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Morphology to isolate vertical lines using a tall, narrow kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))  # Increased kernel height
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Hough Transform to detect vertical line segments 
    # pls dont fucking touch this
    lines = cv2.HoughLinesP(vertical_lines, 1, np.pi / 180,
                            threshold=100,  # Reduced from 6
                            minLineLength=35,  # Reduced from 20
                            maxLineGap=200)  # Reduced from 300
    
    # Copy the section image to draw the lines on
    output = section_img.copy()
    x_coords_raw = []
    
    # If any lines are detected, process them
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle > 80:  # Reduced from 85 to detect slightly slanted lines
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                x_avg = (x1 + x2) // 2
                x_coords_raw.append(x_avg)
    
    # Sort the x-coordinates and filter duplicates (close ones)
    x_coords_raw.sort()
    x_coords_filtered = []
    duplicate_threshold = 8  # Reduced from 10
    
    for x in x_coords_raw:
        if not x_coords_filtered or abs(x - x_coords_filtered[-1]) > duplicate_threshold:
            x_coords_filtered.append(x)
    
    # Draw the filtered vertical lines
    for x in x_coords_filtered:
        cv2.line(output, (x, 0), (x, output.shape[0]), (0, 255, 0), 2)
    
    return output, x_coords_filtered

def detect_horizontal_lines(section_img, section_name="Section"):
    """
    Detect horizontal lines in the given section image.
    """
    # Convert image to grayscale
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast
    gray = cv2.equalizeHist(gray)
    
    # Apply Gaussian blur
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Invert so lines become white
    gray = cv2.bitwise_not(gray)
    
    # Binarize the image with adaptive threshold
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Morphology to isolate horizontal lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1))  # Increased kernel width
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    horizontal_lines = cv2.morphologyEx(horizontal_lines, cv2.MORPH_CLOSE, kernel)
    
    # Additional bridging to further connect broken parts
    bridge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))  # Increased from 10
    horizontal_lines = cv2.dilate(horizontal_lines, bridge_kernel, iterations=2)  # Increased iterations
    
    # Hough Transform to detect horizontal line segments
    lines = cv2.HoughLinesP(horizontal_lines, 1, np.pi / 180,
                            threshold=20,  # Reduced from 30
                            minLineLength=5,  # Reduced from 8
                            maxLineGap=800)  # Reduced from 1000
    
    # Create a copy to draw lines on
    output = section_img.copy()
    y_coords_raw = []
    
    # Loop over detected lines and keep those that are near-horizontal
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle < 10:  # Increased from 5 to detect slightly slanted lines
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                y_avg = (y1 + y2) // 2
                y_coords_raw.append(y_avg)
    
    # Filter duplicate/close y-coordinates
    y_coords_raw.sort()
    y_coords_filtered = []
    duplicate_threshold = 8  # Reduced from 10
    
    for y in y_coords_raw:
        if not y_coords_filtered or abs(y - y_coords_filtered[-1]) > duplicate_threshold:
            y_coords_filtered.append(y)
    
    # Draw the filtered horizontal lines
    for y in y_coords_filtered:
        cv2.line(output, (0, y), (output.shape[1], y), (0, 255, 0), 2)
    
    return output, y_coords_filtered

def detect_shaded_areas_connected(section_img, section_name="Section", fill_thresh=0.45):
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Remove noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # Remove small noise
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # Fill small gaps
    
    
    
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    
    detected_areas = []
    for i in range(1, num_labels):  # Skip background (label 0)
        area = stats[i, cv2.CC_STAT_AREA]
        x = int(centroids[i][0])
        y = int(centroids[i][1])
        
        # Stricter size filtering
        if 80 < area < 400:  # Narrowed range to reduce false positives
            # Filter shape
        
            perimeter = cv2.arcLength(cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][i-1], True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.6:  # Only keep roughly circular shapes
                    detected_areas.append((x, y, area))
                    cv2.circle(section_img, (x, y), 10, (0, 255, 0), 2)
    
    return section_img, detected_areas


# ui_utils.py

sidebar_buttons = {}

def set_sidebar_state(state="normal"):
    """Enable or disable all sidebar navigation buttons."""
    for btn in sidebar_buttons.values():
        try:
            btn.configure(state=state)
        except Exception:
            pass
