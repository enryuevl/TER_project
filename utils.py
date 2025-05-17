import cv2
import numpy as np

def detect_circles(section_img, section_name="Section"):
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 1)

    #pls dont fucking touch this
    circles = cv2.HoughCircles(
        blurred, 
        cv2.HOUGH_GRADIENT, 
        dp=1.5, 
        param1=100, 
        minDist=10,
        param2=30,
        minRadius=5,
        maxRadius=14
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
    
    # Invert to make lines white
    gray = cv2.bitwise_not(gray)
    
    # Binarize image
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Morphology to isolate vertical lines using a tall, narrow kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Hough Transform to detect vertical line segments 
    # pls dont fucking touch this
    lines = cv2.HoughLinesP(vertical_lines, 1, np.pi / 180,
                            threshold=6, minLineLength=20, maxLineGap=300)
    
    # Copy the section image to draw the lines on
    output = section_img.copy()
    x_coords_raw = []
    
    # If any lines are detected, process them
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle > 85:  # near vertical
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                x_avg = (x1 + x2) // 2
                x_coords_raw.append(x_avg)
    
    # Sort the x-coordinates and filter duplicates (close ones)
    x_coords_raw.sort()
    x_coords_filtered = []
    duplicate_threshold = 10  # pixel gap between unique lines
    
    for x in x_coords_raw:
        if not x_coords_filtered or abs(x - x_coords_filtered[-1]) > duplicate_threshold:
            x_coords_filtered.append(x)
    
    # Optionally, draw the filtered vertical lines on the image and print their positions
    for x in x_coords_filtered:
        cv2.line(output, (x, 0), (x, output.shape[0]), (0, 255, 0), 2)
        
    
   
    
    
    return output, x_coords_filtered

def detect_horizontal_lines(section_img, section_name="Section"):
    """
    Detect horizontal lines in the given section image.
    Returns:
      - output: the section image with drawn horizontal lines,
      - y_coords_filtered: a list of the filtered y-coordinates for the detected lines,
      - rows: a list of tuples representing the y range for each row.
              For example, if there are 6 horizontal lines detected, there will be 5 row ranges.
    """
    # Convert image to grayscale
    gray = cv2.cvtColor(section_img, cv2.COLOR_BGR2GRAY)
    
    # Optional: smooth the image
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Invert so lines become white
    gray = cv2.bitwise_not(gray)
    
    # Binarize the image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Morphology to isolate horizontal lines:
    # Use a wide kernel to connect across bubbles
    # pls dont fucking touch this
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    horizontal_lines = cv2.morphologyEx(horizontal_lines, cv2.MORPH_CLOSE, kernel)
    
    # Additional bridging to further connect broken parts
    # pls dont fucking touch this
    bridge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 1))
    horizontal_lines = cv2.dilate(horizontal_lines, bridge_kernel, iterations=1)
    
    # Hough Transform to detect horizontal line segments
    # pls dont fucking touch this
    lines = cv2.HoughLinesP(horizontal_lines, 1.5, np.pi / 180,
                            threshold=30, minLineLength=8, maxLineGap=1000)
    
    # Create a copy to draw lines on
    output = section_img.copy()
    y_coords_raw = []
    
    # Loop over detected lines and keep those that are near-horizontal
    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle < 5:  # near horizontal
                # Draw the detected line
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Get the average y coordinate of the line
                y_avg = (y1 + y2) // 2
                y_coords_raw.append(y_avg)
    
    # Filter duplicate/close y-coordinates
    y_coords_raw.sort()
    y_coords_filtered = []
    duplicate_threshold = 10  # pixels
    
    for y in y_coords_raw:
        if not y_coords_filtered or abs(y - y_coords_filtered[-1]) > duplicate_threshold:
            y_coords_filtered.append(y)
    
    # Optionally, draw the filtered horizontal lines (full width) and print their y positions
    for y in y_coords_filtered:
        cv2.line(output, (0, y), (output.shape[1], y), (0, 255, 0), 2)
        
    
    # Calculate row ranges based on filtered y-coordinates.
    # For example, if there are 6 horizontal lines, you get 5 row ranges.
    
    
    return output, y_coords_filtered