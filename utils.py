import cv2
import numpy as np

def detect_circles(section_img, section_name="Section"):
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    # Increase blur size for better circle detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)

    #pls dont fucking touch this
    circles = cv2.HoughCircles(
        blurred, 
        cv2.HOUGH_GRADIENT, 
        dp=1.5, 
        param1=90, 
        minDist=20,
        param2=24,
        minRadius=5,
        maxRadius=14# Increased maximum radius
    )

    detected = []
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for x, y, r in circles[0, :]:
            cv2.circle(section_img, (x, y), r, (0, 255, 0), 1)
            cv2.circle(section_img, (x, y), 2, (0, 255, 0), 3)
            
            detected.append((x, y, r))
    else:
        print("No circles detected.")

    return section_img, detected

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