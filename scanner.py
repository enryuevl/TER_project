# python -m venv .venv (create virtual environment)
#.\env\Scripts\Activate.ps1 (to activate the virtual environment)

from win32com.client import Dispatch
import win32 
import comtypes
import os
import re
import time
import cv2
import shutil

class WIAScanner:
    # WIA Constants
    WIA_PROPERTIES_PAGES = 3096
    WIA_ADF_CURRENT_PAGE = 3098
    WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088
    WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087
    WIA_DPS_PAGES = 3096
    
   
    def __init__(self, teacher_name=None, output_dir=None):
        # existing code...
        if output_dir:
            self.output_dir = output_dir
        else:
            documents_folder = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Scan")
            self.output_dir = os.path.join(documents_folder, teacher_name) if teacher_name else documents_folder

        self.counter_file = os.path.join(self.output_dir, "counter.txt")
        os.makedirs(self.output_dir, exist_ok=True)

        self.device = None
        self.connection = None
        self.status_prop = None

        # NEW: a safe, readable prefix based on teacher_name
        self.teacher_prefix = None
        if teacher_name:
            self.teacher_prefix = re.sub(r'[^A-Za-z0-9]+', '_', teacher_name).strip('_')
        
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
    
    def scan_page(self, output_filename):
        try:
            conn = self.connect()
            scan_item = conn.Items[1]
            image = scan_item.Transfer()
            output_path = os.path.join(self.output_dir, output_filename)
            image.SaveFile(output_path)
            print(f"\n📝 Processing scanned document: {output_filename}")
            return True
        except Exception as e:
            # If feeder empty → stop scanning
            if "no documents left" in str(e).lower():
                return False
            print(f"❌ Scan failed: {e}")
            return False

            
    def scan_batch(self):
        """Scan all pages from ADF"""
        if not self.device:
            raise Exception("Scanner not initialized. Call initialize() first.")

        # If you want to pass a custom start index, you can do it here (None = auto-derive)
        counter = DocumentCounter(
            output_dir=self.output_dir,
            counter_file=self.counter_file,
            start_index=None,
            prefix=self.teacher_prefix  # comment this if you want plain "001.bmp"
        )

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
    def __init__(self, output_dir, counter_file, start_index=None, prefix=None):
        self.output_dir = output_dir
        self.counter_file = counter_file
        self.prefix = prefix  # e.g., "Juan_Dela_Cruz"
        self.current_count = self._load_counter(start_index)

    def _load_counter(self, start_index):
        # 1) Try counter.txt
        try:
            if os.path.exists(self.counter_file):
                with open(self.counter_file, "r") as f:
                    val = int(f.read().strip())
                    return max(1, val)
        except (ValueError, IOError):
            pass

        # 2) Derive from existing BMP names in folder if counter.txt isn’t usable
        max_n = 0
        try:
            for entry in os.scandir(self.output_dir):
                if not entry.name.lower().endswith(".bmp"):
                    continue
                # Match trailing number before .bmp; works for "12.bmp" or "Teacher_012.bmp"
                m = re.search(r'(\d+)\.bmp$', entry.name, flags=re.IGNORECASE)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        except Exception:
            pass

        if start_index is not None:
            # If caller passed a start index, respect it but never go backwards
            return max(max_n + 1, int(start_index))
        return max_n + 1

    def get_next_filename(self):
        # Use zero-padded numbering; include prefix if provided
        if self.prefix:
            filename = f"{self.current_count:03d}.bmp"
        else:
            filename = f"{self.current_count:03d}.bmp"
        self.current_count += 1
        return filename

    def save(self):
        # Write atomically to avoid corruption
        tmp = self.counter_file + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(self.current_count))
        os.replace(tmp, self.counter_file)


# (only runs if this file is run directly)
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