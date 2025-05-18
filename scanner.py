#.\env\Scripts\Activate.ps1 (to activate the virtual environment)

from win32com.client import Dispatch
import win32 
import comtypes
import os
import re
import time
import cv2
import shutil
from name_detection import preprocess_image_for_ocr, detect_text

class WIAScanner:
    # WIA Constants
    WIA_PROPERTIES_PAGES = 3096
    WIA_ADF_CURRENT_PAGE = 3098
    WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088
    WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087
    WIA_DPS_PAGES = 3096
    
    def __init__(self, output_dir=None):
        """Initialize the scanner with optional output directory"""
        if output_dir is None:
            # Default to Documents/MyWork/Scanned if no output dir specified
            documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
            work_folder = os.path.join(documents_folder, "MyWork")
            output_dir = os.path.join(work_folder, "Scanned")
        
        self.output_dir = output_dir
        self.counter_file = os.path.join(output_dir, "counter.txt")
        self.device = None
        self.connection = None
        self.status_prop = None
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def initialize(self):
        """Initialize WIA and connect to the first available scanner"""
        wia_manager = Dispatch("WIA.DeviceManager")
        devices = wia_manager.DeviceInfos

        if devices.Count == 0:
            raise Exception("No scanner detected.")
            
        # Get the first available scanner
        self.device = devices.Item(1)
        return self._get_scanner_info()
    
    def _get_scanner_info(self):
        """Get scanner information"""
        if not self.device:
            return None
            
        return {
            "name": self.device.Properties("Name").Value,
            "description": self.device.Properties("Description").Value
        }
    
    def connect(self):
        """Connect to scanner and configure it"""
        if not self.device:
            raise Exception("Scanner not initialized. Call initialize() first.")
            
        if self.connection is None:
            self.connection = self.device.Connect()
            # Configure ADF settings
            for prop in self.connection.Properties:
                if prop.PropertyID == self.WIA_DPS_DOCUMENT_HANDLING_SELECT:
                    prop.Value = 1  # Use ADF
                    break
                elif prop.PropertyID == 4103:  # WIA_IPS_CUR_INTENT
                    prop.Value = 4  # BW mode
                elif prop.PropertyID == self.WIA_DPS_DOCUMENT_HANDLING_STATUS:
                    self.status_prop = prop  # Cache the status property
        return self.connection

    def has_more_pages(self):
        """Check if there are more pages to scan"""
        try:
            if self.status_prop:
                return self.status_prop.Value == 1
            return True
        except:
            return True
    
    def _detect_name_from_image(self, image_path):
        """Detect name from the scanned image"""
        try:
            # Load and process the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Could not load image: {image_path}")
                return None
            
            # Use the detect_text function directly
            text, words = detect_text(image)
            
            # Clean up the detected text
            if text:
                # Remove special characters and extra whitespace
                cleaned_text = re.sub(r'[^a-zA-Z\s]', '', text.strip())
                if cleaned_text:
                    print(f"✅ Name detected: {cleaned_text}")
                    if words:  # Print confidence scores if available
                        print("Confidence scores:")
                        for word, conf in words:
                            print(f"  {word}: {conf}%")
                    return cleaned_text
            
            print("❌ No valid name detected in the image")
            return None
            
        except Exception as e:
            print(f"Error detecting name: {e}")
            return None
    
    def _organize_file_by_name(self, source_path, detected_name):
        """Organize the scanned file into a folder based on the detected name"""
        if not detected_name:
            return False
            
        try:
            # Create a valid folder name from the detected name
            folder_name = re.sub(r'[^a-zA-Z\s]', '', detected_name.strip())
            folder_name = folder_name.replace(' ', '_').lower()
            
            if not folder_name:
                print("❌ Could not create valid folder name from detected name")
                return False
                
            # Create the name-specific folder
            name_folder = os.path.join(self.output_dir, folder_name)
            os.makedirs(name_folder, exist_ok=True)
            
            # Move the file to the name-specific folder
            filename = os.path.basename(source_path)
            target_path = os.path.join(name_folder, filename)
            shutil.move(source_path, target_path)
            
            print(f"✅ Organized file into folder: {folder_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error organizing file: {e}")
            return False
            
    def scan_page(self, output_filename):
        """Scan a single page and organize it based on detected name"""
        try:
            conn = self.connect()
            scan_item = conn.Items[1]
            image = scan_item.Transfer()
            output_path = os.path.join(self.output_dir, output_filename)
            image.SaveFile(output_path)
            
            print(f"\n📝 Processing scanned document: {output_filename}")
            
            # Detect name and organize file
            print("Detecting name from scanned document...")
            detected_name = self._detect_name_from_image(output_path)
            
            if detected_name:
                self._organize_file_by_name(output_path, detected_name)
            else:
                print("⚠️ Document will remain in main scanned folder")
                
            return True
            
        except Exception as e:
            if not self.has_more_pages():
                return False
            print(f"❌ Scan failed: {e}")
            return False
            
    def scan_batch(self):
        """Scan all pages from ADF"""
        if not self.device:
            raise Exception("Scanner not initialized. Call initialize() first.")
            
        counter = DocumentCounter(self.counter_file)
        pages_scanned = 0
        
        print("\n📄 Starting batch scan from ADF...")
        
        while self.has_more_pages():
            output_file = counter.get_next_filename()
            if not self.scan_page(output_file):
                break
            pages_scanned += 1
        
        counter.save()
        return pages_scanned

class DocumentCounter:
    def __init__(self, counter_file):
        self.counter_file = counter_file
        self.current_count = self._load_counter()
    
    def _load_counter(self):
        try:
            if os.path.exists(self.counter_file):
                with open(self.counter_file, "r") as f:
                    return int(f.read().strip())
        except (ValueError, IOError):
            pass
        return 1
    
    def get_next_filename(self):
        filename = f"scan_{self.current_count:03d}.bmp"  # Using BMP for faster saves
        self.current_count += 1
        return filename
    
    def save(self):
        with open(self.counter_file, "w") as f:
            f.write(str(self.current_count))

# Example usage (only runs if this file is run directly)
if __name__ == "__main__":
    try:
        # Create scanner instance
        scanner = WIAScanner()
        
        # Initialize and get scanner info
        info = scanner.initialize()
        print(f"✅ Scanner detected:")
        print(f"  Name       : {info['name']}")
        print(f"  Description: {info['description']}")
        
        # Scan batch
        pages_scanned = scanner.scan_batch()
        
        if pages_scanned > 0:
            print(f"\n✅ Batch scan completed. {pages_scanned} page{'s' if pages_scanned != 1 else ''} scanned.")
        else:
            print("\n❌ No documents found in ADF.")
            
    except Exception as e:
        print(f"❌ Error: {e}")