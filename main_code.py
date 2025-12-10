import cv2
import numpy as np
import utils  # Make sure your utils file defines detect_horizontal_lines, detect_vertical_lines, detect_circles
from PIL import Image, ExifTags

def fix_orientation(pil_img):
    try:
        if not hasattr(pil_img, "_getexif"):
            return pil_img  # Skip if no EXIF data (e.g., BMP)

        exif = pil_img._getexif()
        if exif is None:
            return pil_img

        orientation_tag = next(
            (tag for tag, value in ExifTags.TAGS.items() if value == 'Orientation'),
            None
        )

        if orientation_tag and orientation_tag in exif:
            orientation = exif[orientation_tag]
            if orientation == 3:
                pil_img = pil_img.rotate(180, expand=True)
            elif orientation == 6:
                pil_img = pil_img.rotate(270, expand=True)
            elif orientation == 8:
                pil_img = pil_img.rotate(90, expand=True)
    except Exception as e:
        print("Error fixing orientation:", e)
    return pil_img


def process_sections(img, mode: str = "new"):
    
    resized = cv2.resize(img, (850, 1550))

    # 👉 NEW layout (your current one)
    new_sections = {
        "Section 1": resized[459:634, 571:844],
        "Section 2": resized[615:801, 571:844],
        "Section 3": resized[782:967, 571:844],
        "Section 4": resized[949:1129, 571:844],
    }

    # 👉 OLD layout (uncommented legacy coordinates)
    old_sections = {
        "Section 1": resized[461:613, 579:790],
        "Section 2": resized[631:784, 579:790],
        "Section 3": resized[802:964, 579:790],
        "Section 4": resized[981:1146, 579:790],
    }

    mode = (mode or "new").lower().strip()
    if mode == "old":
        sections = old_sections
    else:
        sections = new_sections

    all_section_scores = {}

    for sec_name, sec_img in sections.items():
        # Detect horizontal + vertical lines
        _, y_coords = utils.detect_horizontal_lines(sec_img, section_name=sec_name)
        _, x_coords = utils.detect_vertical_lines(sec_img, section_name=sec_name)

        # Compute row and column boundaries
        rows = [(int(y_coords[i]), int(y_coords[i+1])) for i in range(len(y_coords)-1)]
        columns = [(int(x_coords[i]), int(x_coords[i+1])) for i in range(len(x_coords)-1)]

        # Detect circles
        _, circles = utils.detect_shaded_areas_connected(sec_img, section_name=sec_name)

        unique_cells = {}
        circle_assignments = []

        for (x, y, area) in circles:
            col_assigned, row_assigned = None, None

            # which column?
            for idx, (start, end) in enumerate(columns):
                if start <= x < end:
                    col_assigned = idx + 1
                    break

            # which row?
            for idx, (start, end) in enumerate(rows):
                if start <= y < end:
                    row_assigned = idx + 1
                    break

            if col_assigned and row_assigned:
                circle_assignments.append((row_assigned, col_assigned, x, y, area))

        circle_assignments.sort(key=lambda item: (item[0], item[1]))

        for (row, col, x, y, area) in circle_assignments:
            if (row, col) not in unique_cells:
                unique_cells[(row, col)] = (x, y, area)

        total_columns = len(columns)
        row_scores = {}
        for (row, col), (x, y, area) in unique_cells.items():
            score = (total_columns + 1) - col
            row_scores[row] = score

            # Draw highlights on the section for preview
            cv2.circle(sec_img, (x, y), 10, (0, 255, 0), 2)
            text = f"Score: {score}"
            cv2.putText(
                sec_img, text, (x + 20, y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2
            )

        all_section_scores[sec_name] = row_scores

    # Return both scores and annotated full page (resized)
    return all_section_scores, resized


# Draw each unique detected circle
        

    

    
    

# Example usage:
