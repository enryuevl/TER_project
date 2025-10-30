from win32com.client import Dispatch
import win32
import comtypes
import os
import time
import cv2
import shutil
from datetime import datetime

class WIAScanner:
    # WIA Constants
    WIA_PROPERTIES_PAGES = 3096
    WIA_ADF_CURRENT_PAGE = 3098
    WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088
    WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087
    WIA_DPS_PAGES = 3096

    def __init__(self, teacher_name=None, output_dir=None):
        
        scan_root = os.path.join(os.path.expanduser("~"), "Documents", "MyWork", "Scan")

        # ✅ Respect caller's output_dir
        if output_dir is not None and str(output_dir).strip():
            self.output_dir = output_dir
        elif teacher_name:
            self.output_dir = os.path.join(scan_root, teacher_name)   # legacy flat
        else:
            self.output_dir = scan_root

        os.makedirs(self.output_dir, exist_ok=True)

        # Batch parent lives INSIDE the chosen output_dir
        self.incoming_root = os.path.join(self.output_dir, "_incoming")
        os.makedirs(self.incoming_root, exist_ok=True)

        self.batch_dir = None
        self.device = None
        self.connection = None
        self.status_prop = None


    # ---------- batch management ----------
    def create_batch_dir(self):
        """
        Create a new incoming folder for this scan batch and reset batch counter.
        """
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.batch_dir = os.path.join(self.incoming_root, ts)
        os.makedirs(self.batch_dir, exist_ok=True)
        # batch-local counter only (always starts at 1)
        self._batch_counter = 1
        return self.batch_dir

    def _next_batch_filename(self):
        """
        Per-batch filename: scan_001.bmp, scan_002.bmp, ...
        """
        name = f"scan_{self._batch_counter:03d}.bmp"
        self._batch_counter += 1
        return os.path.join(self.batch_dir, name)

    # ---------- wia ----------
    def initialize(self):
        """Initialize WIA and connect to the first available scanner"""
        wia_manager = Dispatch("WIA.DeviceManager")
        devices = wia_manager.DeviceInfos
        if devices.Count == 0:
            raise Exception("No scanner detected.")
        self.device = devices.Item(1)
        return self._get_scanner_info()

    def _get_scanner_info(self):
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
            for prop in self.connection.Properties:
                if prop.PropertyID == self.WIA_DPS_DOCUMENT_HANDLING_SELECT:
                    prop.Value = 1  # Use ADF
                elif prop.PropertyID == 4103:  # WIA_IPS_CUR_INTENT
                    prop.Value = 4  # BW mode
                elif prop.PropertyID == self.WIA_DPS_DOCUMENT_HANDLING_STATUS:
                    self.status_prop = prop
        return self.connection

    def has_more_pages(self):
        try:
            if self.status_prop:
                return self.status_prop.Value == 1
            return True
        except:
            return True

    def scan_page(self):
        """Scan a single page to the current batch folder with per-batch numbering."""
        if not self.batch_dir:
            raise Exception("Batch not created. Call create_batch_dir() before scan_batch().")
        try:
            conn = self.connect()
            scan_item = conn.Items[1]
            image = scan_item.Transfer()
            out_path = self._next_batch_filename()
            image.SaveFile(out_path)
            print(f"📝 Scanned → {os.path.basename(out_path)}")
            return True
        except Exception as e:
            if not self.has_more_pages():
                return False
            print(f"❌ Scan failed: {e}")
            return False

    def scan_batch(self):
        """
        Scan all pages from ADF into a fresh batch folder (per-batch numbering).
        Returns (pages_scanned, batch_dir).
        """
        if not self.device:
            raise Exception("Scanner not initialized. Call initialize() first.")

        if not self.batch_dir:
            self.create_batch_dir()

        pages_scanned = 0
        print("\n📄 Starting batch scan from ADF...")
        while self.has_more_pages():
            ok = self.scan_page()
            if not ok:
                break
            pages_scanned += 1

        print(f"✅ Batch done: {pages_scanned} page(s) → {self.batch_dir}")
        return pages_scanned, self.batch_dir

# (manual test)
if __name__ == "__main__":
    try:
        sc = WIAScanner()
        info = sc.initialize()
        print(f"✅ Scanner detected:\n  Name: {info['name']}\n  Description: {info['description']}")
        sc.create_batch_dir()
        pages, bdir = sc.scan_batch()
        if pages > 0:
            print(f"\n✅ Completed. {pages} pages in {bdir}")
        else:
            print("\n❌ No documents found in ADF.")
    except Exception as e:
        print(f"❌ Error: {e}")
