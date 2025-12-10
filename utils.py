import cv2
import numpy as np
import os, re
import db
import math


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
    """
    Detect filled bubbles in a section image using connected components.

    Returns:
        annotated_section_img, detected_areas

        detected_areas: list of (x, y, area) for each NON-CROSSED bubble.
    """
    # Work on a copy so we can draw circles
    out_img = section_img.copy()

    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)

    # Binary: ink / marks are white (255), background black (0)
    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Clean up noise and fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )

    h, w = binary.shape[:2]
    detected_areas = []

    # Loop over components (skip label 0 = background)
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]

        # Size filter: tuned for your bubbles
        if not (80 < area < 400):
            continue

        x0 = stats[label, cv2.CC_STAT_LEFT]
        y0 = stats[label, cv2.CC_STAT_TOP]
        bw = stats[label, cv2.CC_STAT_WIDTH]
        bh = stats[label, cv2.CC_STAT_HEIGHT]

        cx = int(centroids[label][0])
        cy = int(centroids[label][1])

        # Crop a small ROI around this component (with a tiny padding)
        pad = 2
        x1 = max(x0 - pad, 0)
        y1 = max(y0 - pad, 0)
        x2 = min(x0 + bw + pad, w)
        y2 = min(y0 + bh + pad, h)
        roi = binary[y1:y2, x1:x2]

        # --- 1) Check if this bubble is crossed out ---
        if _has_cross_x(roi):
            # Optional: draw red circle to debug
            cv2.circle(out_img, (cx, cy), 10, (0, 0, 255), 2)
            # Skip this bubble entirely (treated as NOT answered)
            continue

        # --- 2) (Optional) shape check: roughly circular ---
        contours, _ = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            continue

        cnt = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter <= 0:
            continue

        circ_area = cv2.contourArea(cnt)
        circularity = 4 * np.pi * circ_area / (perimeter * perimeter)

        # Keep only roughly circular shapes
        if circularity < 0.6:
            continue

        # This is a valid, non-crossed bubble
        detected_areas.append((cx, cy, area))
        cv2.circle(out_img, (cx, cy), 10, (0, 255, 0), 2)  # green = taken answer

    return out_img, detected_areas

def _has_cross_x(roi_binary: np.ndarray) -> bool:
    """
    Detect whether there is an 'X' (two long diagonals) inside the ROI.

    roi_binary: small binary image (255 = ink/mark, 0 = background) around the bubble.
    """
    # Canny edge detection
    edges = cv2.Canny(roi_binary, 50, 150)

    # Hough line detection
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=18,  # how many edge points needed
        minLineLength=int(0.6 * max(roi_binary.shape)),  # long lines only
        maxLineGap=3,
    )

    if lines is None:
        return False

    pos_diag = 0  # / slope
    neg_diag = 0  # \ slope

    for line in lines:
        x1, y1, x2, y2 = line[0]
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            continue

        angle = abs(math.degrees(math.atan2(dy, dx)))  # 0–180

        # Roughly 45° or 135° = diagonals
        if 25 < angle < 65:
            pos_diag += 1
        elif 115 < angle < 155:
            neg_diag += 1

    # We consider it an X if we have at least one of each diagonal
    return pos_diag >= 1 and neg_diag >= 1


# ui_utils.py

sidebar_buttons = {}

def set_sidebar_state(state="normal"):
    """Enable or disable all sidebar navigation buttons."""
    for btn in sidebar_buttons.values():
        try:
            btn.configure(state=state)
        except Exception:
            pass

# --- Summary export naming helpers ---

def build_summary_filename(teacher: str, ay: str, sem: str) -> str:
    # remove illegal filename chars and trailing dots/spaces
    safe_teacher = re.sub(r'[<>:"/\\|?*]+', '-', (teacher or '')).strip().strip('.')
    return f"{safe_teacher} - Summary_{ay}_{sem}.xlsx"

def get_summary_export_path(teacher: str, ay: str, sem: str, base_dir: str | None = None) -> str:
    if base_dir is None:
        base_dir = os.path.dirname(db.get_default_db_path())
    return os.path.join(base_dir, build_summary_filename(teacher, ay, sem))
