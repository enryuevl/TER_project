import os
import sys
import cv2
import numpy as np
from PIL import Image
import pythoncom

from scanner import WIAScanner
from main_code import fix_orientation, process_sections

# Define sections dictionary; each section is processed independently.
'''sections = {
        "Section 1": resized[461:613, 579:790],
        "Section 2": resized[631:784, 579:790],
        "Section 3": resized[802:964, 579:790],
        "Section 4": resized[981:1146, 579:790],
    }'''


def print_scores(page_index, filename, all_section_scores):
    """Pretty-print the OMR results for one page."""
    print(f"\n==============================")
    print(f" PAGE {page_index}: {filename}")
    print(f"==============================")

    if not all_section_scores:
        print("No marks detected on this page.")
        return

    for section_name, row_scores in all_section_scores.items():
        print(f"\n{section_name}:")
        if not row_scores:
            print("  (no rows detected)")
            continue

        for row_idx in sorted(row_scores.keys()):
            print(f"  Row {row_idx}: Score {row_scores[row_idx]}")


def process_batch_folder(batch_dir):
    """
    For every scanned image in the given batch folder:
    - load image
    - fix orientation
    - run process_sections (from main_code)
    - save annotated image
    - print scores to terminal
    """
    valid_exts = (".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff")
    entries = sorted(
        [f for f in os.listdir(batch_dir) if f.lower().endswith(valid_exts)]
    )

    if not entries:
        print(f"[INFO] No image files found in batch folder: {batch_dir}")
        return

    for idx, fname in enumerate(entries, start=1):
        img_path = os.path.join(batch_dir, fname)
        print(f"\n[INFO] Processing: {img_path}")

        # Load via PIL so EXIF orientation can be handled
        try:
            pil_img = Image.open(img_path)
        except Exception as e:
            print(f"[ERROR] Failed to open image {fname}: {e}")
            continue

        pil_img = fix_orientation(pil_img)

        # PIL (RGB/grayscale) -> OpenCV BGR
        np_img = np.array(pil_img)
        if np_img.ndim == 2:
            np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2BGR)
        else:
            np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

        # Run your main OMR logic
        try:
            all_section_scores, annotated = process_sections(np_img)
        except Exception as e:
            print(f"[ERROR] OMR processing failed for {fname}: {e}")
            continue

        # Save annotated image next to originals
        annotated_name = f"annotated_{idx:03d}.png"
        annotated_path = os.path.join(batch_dir, annotated_name)
        try:
            cv2.imwrite(annotated_path, annotated)
            print(f"[INFO] Annotated image saved → {annotated_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save annotated image: {e}")

        # Print scores to terminal
        print_scores(idx, fname, all_section_scores)


def main():
    """
    CLI test runner:
    - connects to the WIA scanner
    - scans a batch
    - processes each scanned page
    - saves annotated images
    - prints results to the terminal
    """

    # Optional: teacher name as argument, just to reuse your folder structure
    # Usage: python main_code_scan_test.py "Teacher Name"
    if len(sys.argv) > 1:
        teacher_name = sys.argv[1]
    else:
        teacher_name = "CLI_Test"

    print(f"[INFO] Using teacher_name = {teacher_name!r}")

    # COM init for WIA
    pythoncom.CoInitialize()
    try:
        # Scanner root: Documents\MyWork\Scan\<teacher_name>\_incoming\<batch>
        scanner = WIAScanner(teacher_name=teacher_name)
        info = scanner.initialize()
        print(f"✅ Scanner detected:")
        print(f"   Name       : {info['name']}")
        print(f"   Description: {info['description']}")

        # Create new batch folder and scan
        scanner.create_batch_dir()
        pages_scanned, batch_dir = scanner.scan_batch()

        if pages_scanned <= 0:
            print("\n❌ No documents found in ADF or scanning aborted.")
            return

        print(f"\n✅ Scan completed: {pages_scanned} page(s) in {batch_dir}")

        # Now run your main_code processing on that batch folder
        process_batch_folder(batch_dir)

    except Exception as e:
        print(f"\n❌ Fatal error during scanning or processing: {e}")

    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
