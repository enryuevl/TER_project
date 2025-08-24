import cv2
import numpy as np
import utils  # Make sure your utils file defines detect_horizontal_lines, detect_vertical_lines, detect_circles
from PIL import Image, ExifTags

def fix_orientation(pil_img):
    try:
        exif = pil_img._getexif()
        if exif is None:
            return pil_img

        # Find the orientation tag
        for tag, value in ExifTags.TAGS.items():
            if value == 'Orientation':
                orientation_tag = tag
                break

        orientation = exif.get(orientation_tag, None)
        if orientation == 3:
            pil_img = pil_img.rotate(180, expand=True)
        elif orientation == 6:
            pil_img = pil_img.rotate(270, expand=True)
        elif orientation == 8:
            pil_img = pil_img.rotate(90, expand=True)
    except Exception as e:
        print("Error fixing orientation:", e)
    return pil_img

def process_sections(img):
    resized = cv2.resize(img, (850, 1550))

    # Define sections dictionary; each section is processed independently.
    sections = {
        "Section 1": resized[459:586, 574:770],
        "Section 2": resized[606:757, 573:770],
        "Section 3": resized[774:936, 573:770],
        "Section 4": resized[955:1117, 573:770],
    }
    

    all_section_scores = {}
    modified_images = {}  # Store the modified sections with highlighted circles

    for sec_name, sec_img in sections.items():
        # Detect horizontal lines to get row boundaries.
        output_h, y_coords = utils.detect_horizontal_lines(sec_img, section_name=sec_name)
        
        # Display horizontal lines detection
        cv2.imshow(f"{sec_name} - Horizontal Lines", output_h)
        cv2.waitKey(100)  # Small delay to see the progression

        # Compute row ranges based on filtered y-coordinates.
        rows = []
        for i in range(len(y_coords) - 1):
            row_range = (int(y_coords[i]), int(y_coords[i+1]))
            rows.append(row_range)

        # Detect vertical lines to get column boundaries.
        output_v, x_coords = utils.detect_vertical_lines(sec_img, section_name=sec_name)
        
        # Display vertical lines detection
        cv2.imshow(f"{sec_name} - Vertical Lines", output_v)
        cv2.waitKey(100)  # Small delay to see the progression

        # Compute column ranges from filtered x-coordinates.
        columns = []
        for i in range(len(x_coords) - 1):
            col_range = (int(x_coords[i]), int(x_coords[i+1]))
            columns.append(col_range)

        # Detect circles in the section.
        output_c, circles = utils.detect_shaded_areas_connected(sec_img, section_name=sec_name)

        # Draw circles on the image (highlighting detected circles)
        for (x, y, area) in circles:
            cv2.circle(sec_img, (x, y), 10, (0, 255, 0), 2)  # Draw green circle with radius 10

        # Store the modified section image
        modified_images[sec_name] = sec_img.copy()

        # For each detected circle, determine which column and row it falls into.
        circle_assignments = []
        for (x, y, area) in circles:
            col_assigned = None
            row_assigned = None

            # Determine column based on x-coordinate.
            for idx, (start, end) in enumerate(columns):
                if start <= x < end:
                    col_assigned = idx + 1  # Columns numbered starting at 1
                    break

            # Determine row based on y-coordinate.
            for idx, (start, end) in enumerate(rows):
                if start <= y < end:
                    row_assigned = idx + 1  # Rows numbered starting at 1
                    break

            if col_assigned is not None and row_assigned is not None:
                circle_assignments.append((row_assigned, col_assigned, x, y, area))
            else:
                print(f"{sec_name} - Shaded area at ({x}, {y}) did not fall within a proper cell range.")

        # Sort assignments by row then by column.
        circle_assignments.sort(key=lambda item: (item[0], item[1]))

        # Filter out duplicate circles in the same cell (only one per cell).
        unique_cells = {}
        for (row, col, x, y, area) in circle_assignments:
            cell_key = (row, col)
            if cell_key not in unique_cells:
                unique_cells[cell_key] = (x, y, area)

        # Compute total score for the section.
        total_columns = len(columns)  # e.g., if there are 6 vertical lines then there are 5 columns.
        section_total_score = 0

        row_scores = {}
        for (row, col), (x, y, area) in sorted(unique_cells.items(), key=lambda item: (item[0][0], item[0][1])):
            score = (total_columns + 1) - col
            row_scores[row] = score
            
            # Draw score with background for better visibility
            text = f"Score: {score}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            
            # Draw background rectangle
            cv2.rectangle(sec_img, (x+15, y-15), (x+15+text_size[0]+10, y+15), (255, 255, 255), -1)
            cv2.rectangle(sec_img, (x+15, y-15), (x+15+text_size[0]+10, y+15), (0, 0, 0), 2)
            
            # Draw score text
            cv2.putText(sec_img, text, (x+20, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        all_section_scores[sec_name] = row_scores
        
        # Print section summary
        print(f"\n{sec_name} Scores:")
        for row, score in sorted(row_scores.items()):
            print(f"  Row {row}: Score {score}")

    # Display all modified sections with highlighted circles
    for sec_name, sec_img in modified_images.items():
        cv2.imshow(f"{sec_name} - Processed", sec_img)
    
    cv2.waitKey(0)  # Wait for key press
    cv2.destroyAllWindows()  # Close all windows

    return all_section_scores

# Draw each unique detected circle
        

    

    
    

# Example usage:
