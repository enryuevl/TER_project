import cv2
import numpy as np
import pytesseract
import os
from PIL import Image

# Set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image_for_ocr(image):
    """Preprocess the image to improve OCR accuracy"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Apply dilation to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    gray = cv2.dilate(gray, kernel, iterations=1)
    
    return gray

def detect_text(image):
    """
    Detect text in the name section of the form
    Args:
        image: OpenCV image (numpy array) to process
    Returns:
        tuple: (detected_text, detected_words_with_confidence)
    """
    try:
        # Resize image to standard size
        resized = cv2.resize(image, (850, 1550))

        # Extract the name section
        sections = resized[212:231, 208:473]
        if sections is None:
            print("Error: Could not extract name section from image")
            return None, None
        
        # Resize section for better OCR
        height, width = sections.shape[:2]
        name_section = cv2.resize(sections, (width*2, height*2))
        
        # Preprocess the image
        preprocessed = preprocess_image_for_ocr(name_section)
        
        # Perform OCR with custom configuration
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(preprocessed, config=custom_config)
        
        # Get detailed information about text regions
        data = pytesseract.image_to_data(preprocessed, output_type=pytesseract.Output.DICT)
        
        # Process detected text regions
        detected_words = []
        for i, word in enumerate(data['text']):
            if word.strip():  # Only process non-empty words
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                # Store word and its confidence
                detected_words.append((word, conf))
        
        return text.strip(), detected_words
        
    except Exception as e:
        print(f"Error during text detection: {e}")
        return None, None

