# test_batch_scan.py

import os
import cv2
import pythoncom

from scanner import WIAScanner
import main_code       # uses your process_sections
import utils           # for line/circle detection


# ============================================================
# DESKEW HELPER
# ============================================================

def deskew_image(img_bgr, debug=False):
    """
    Automatically deskew the scanned page so that horizontal/vertical
    lines become truly horizontal/vertical.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray_inv = cv2.bitwise_not(gray)

    # Otsu threshold
    _, thresh = cv2.threshold(
        gray_inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )

    coords = cv2.findNonZero(thresh)
    if coords is None:
        if debug:
            print("[deskew] No foreground pixels found, skipping.")
        return img_bgr  # nothing detected, just return original

    coords = coords.reshape(-1, 2)
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    # Correct OpenCV angle quirk
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if debug:
        print(f"[deskew] angle detected: {angle:.2f}°")

    (h, w) = img_bgr.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        img_bgr, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


# ============================================================
# FIND MARKS NOT IN ANY ROW / COLUMN
# ============================================================

def find_unmatched_marks(img):
    """
    Re-runs the grid detection per section and reports any shaded marks
    that do NOT fall into a detected row/column cell.
    Returns: { "Section 1": [(x,y), ...], ... }
    """
    # Use the same resizing and crops as process_sections
    resized = cv2.resize(img, (850, 1550))

    sections = {
        "Section 1": resized[461:613, 579:790],
        "Section 2": resized[631:784, 579:790],
        "Section 3": resized[800:964, 579:790],
        "Section 4": resized[981:1146, 579:790],
    }

    unmatched_by_section = {}

    for sec_name, sec_img in sections.items():
        # Same detection pipeline as in your scoring logic
        _, y_coords = utils.detect_horizontal_lines(sec_img, section_name=sec_name)
        _, x_coords = utils.detect_vertical_lines(sec_img, section_name=sec_name)
        _, circles  = utils.detect_shaded_areas_connected(sec_img, section_name=sec_name)

        # Build row/column intervals
        rows = [(int(y_coords[i]), int(y_coords[i+1])) for i in range(len(y_coords)-1)]
        cols = [(int(x_coords[i]), int(x_coords[i+1])) for i in range(len(x_coords)-1)]

        unmatched = []

        for (x, y, area) in circles:
            col_assigned, row_assigned = None, None

            # Column assignment
            for idx, (start, end) in enumerate(cols):
                if start <= x < end:
                    col_assigned = idx + 1
                    break

            # Row assignment
            for idx, (start, end) in enumerate(rows):
                if start <= y < end:
                    row_assigned = idx + 1
                    break

            # If either row or column was not found, flag this mark
            if col_assigned is None or row_assigned is None:
                unmatched.append((int(x), int(y)))

        unmatched_by_section[sec_name] = unmatched

    return unmatched_by_section


# ============================================================
# VISUAL DEBUG: SHOW LINES + CIRCLES PER SECTION
# ============================================================

def show_debug_overlays(full_img, window_prefix="Page"):
    """
    Shows debug windows:
      - One for each section with grid lines + circles drawn.
    Uses the same crops as process_sections.
    """
    resized = cv2.resize(full_img, (850, 1550))

    sections = {
        "Section 1": resized[461:613, 579:790],
        "Section 2": resized[631:784, 579:790],
        "Section 3": resized[800:964, 579:790],
        "Section 4": resized[981:1146, 579:790],
    }

    for sec_name, sec_img in sections.items():
        vis = sec_img.copy()

        # detect lines & circles again just for visualization
        _, y_coords = utils.detect_horizontal_lines(vis, section_name=sec_name)
        _, x_coords = utils.detect_vertical_lines(vis, section_name=sec_name)
        _, circles  = utils.detect_shaded_areas_connected(vis, section_name=sec_name)

        h, w = vis.shape[:2]

        # Draw horizontal lines (blue)
        for y in y_coords:
            y = int(y)
            cv2.line(vis, (0, y), (w - 1, y), (255, 0, 0), 1)

        # Draw vertical lines (red)
        for x in x_coords:
            x = int(x)
            cv2.line(vis, (x, 0), (x, h - 1), (0, 0, 255), 1)

        # Draw circles (green)
        for (cx, cy, area) in circles:
            cv2.circle(vis, (int(cx), int(cy)), 8, (0, 255, 0), 2)

        cv2.imshow(f"{window_prefix} - {sec_name}", vis)


# ============================================================
# PER-PAGE ANALYSIS
# ============================================================

def analyze_page(image_path):
    print("\n" + "=" * 80)
    print(f"Analyzing: {os.path.basename(image_path)}")
    print("=" * 80)

    img = cv2.imread(image_path)
    if img is None:
        print("❌ Could not read image (cv2.imread returned None).")
        return

    

    # 1) Get scores using your existing function (this also draws circles on the cropped sections)
    all_scores, annotated = main_code.process_sections(img)

    # 2) Debug: find marks that didn't map into any cell
    unmatched = find_unmatched_marks(img)

    # Expected rows per section (same as your QC: 5 rows each)
    expected_rows = {
        "Section 1": 5,
        "Section 2": 5,
        "Section 3": 5,
        "Section 4": 5,
    }

    # ---------- Print scores + missing rows ----------
    for sec_name in ["Section 1", "Section 2", "Section 3", "Section 4"]:
        row_scores = all_scores.get(sec_name, {})

        print(f"\n[{sec_name}]")
        if not row_scores:
            print("  → No scores detected in this section.")
        else:
            for row in range(1, expected_rows[sec_name] + 1):
                if row in row_scores:
                    print(f"  Row {row}: Score = {row_scores[row]}")
                else:
                    print(f"  Row {row}: **MISSING** (no score detected)")

        # Print unmatched marks (marks not inside any row/column)
        bad_marks = unmatched.get(sec_name, [])
        if bad_marks:
            print(f"  ⚠ {len(bad_marks)} mark(s) not within any detected cell:")
            for (x, y) in bad_marks:
                print(f"     - mark at (x={x}, y={y})")
        else:
            print("  ✅ All detected marks were inside some row/column cell.")

    # ---------- VISUAL DEBUG WINDOWS ----------
    base_name = os.path.basename(image_path)

    # Full annotated page from process_sections (already has green circles)
    cv2.imshow(f"{base_name} - FULL ANNOTATED", annotated)

    # Per-section debug (lines + circles)
    show_debug_overlays(img, window_prefix=base_name)

    print("\n[DEBUG] Close the images or press any key in an image window to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ============================================================
# MAIN: SCAN A BATCH THEN ANALYZE
# ============================================================

def main():
    pythoncom.CoInitialize()
    try:
        # --- Setup scanner ---
        scanner = WIAScanner()
        info = scanner.initialize()
        print("✅ Scanner detected:")
        print(f"   Name       : {info['name']}")
        print(f"   Description: {info['description']}")

        # Create a fresh batch folder with per-batch numbering
        batch_dir = scanner.create_batch_dir()
        print(f"\nIncoming batch folder: {batch_dir}")

        # --- Scan batch (this WILL save temporary BMP files in batch_dir) ---
        pages, batch_dir = scanner.scan_batch()
        print(f"\n📄 Pages scanned: {pages}")
        if pages == 0:
            print("No documents found in ADF. Exiting.")
            return

        # --- Analyze each scanned page without saving any PKL/Excel ---
        for entry in sorted(os.scandir(batch_dir), key=lambda e: e.name):
            if not entry.name.lower().endswith(".bmp"):
                continue
            analyze_page(entry.path)

        # OPTIONAL: clean up batch images afterwards
        # import shutil
        # shutil.rmtree(batch_dir)

    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
