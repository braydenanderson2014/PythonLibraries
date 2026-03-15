import tkinter as tk
from ttkbootstrap import ttk
import fitz
from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController
from ProgressDialog import QuadrupleProgressDialog
from ProgressDialog import DualProgressDialog
import os
from tkinter import filedialog

class White:
    def __init__(self, root, selection):
        self.root = root
        self.selection = selection
        self.settings = SettingsController(root)
        self.pdf_files = []
        self.threshold = 0.5  # Default threshold for white space detection
        self.files_scanned = 0 # Number of files scanned
        self.pages_scanned = 0 # Number of pages scanned
        self.total_files = 0  # Total number of files to scan
        self.logger = Logger()
        self.logger.info("White", "==========================================================")
        self.logger.info("White", " EVENT: INIT")
        self.logger.info("White", "==========================================================")


    def set_selection(self, selection):
        self.selection = selection

    def _ask_threshold(self) -> bool:
        """
        Modal pop-up that lets the user pick a threshold.
        Returns True if the user pressed *Save*, False on *Cancel*.
        """

        popup = tk.Toplevel(self.root)
        popup.title("Set Blank-Page Threshold")
        popup.geometry("460x250")            # wider & taller
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()                     # modal

        frm = ttk.Frame(popup, padding=20)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frm,
            text="⚠  A very low threshold can mark non-white pages as blank.",
            wraplength=420, foreground="red", font=("Arial", 10, "bold")
        ).pack(fill=tk.X, pady=(0, 12))

        ttk.Label(frm, text="Aggressive  ←  Threshold  →  Non-Aggressive")\
           .pack(anchor="w")

        var = tk.DoubleVar(value=self.threshold)
        ttk.Scale(
            frm, from_=0.1, to=1.0, variable=var,
            orient=tk.HORIZONTAL, length=420
        ).pack(pady=4)

        val_lbl = ttk.Label(frm, text=f"Current : {self.threshold:.2f}")
        val_lbl.pack()

        var.trace_add("write", lambda *_: val_lbl.config(
            text=f"Current : {var.get():.2f}")
        )

        # ----------------------------------------------------------------─
        result = {"ok": False}

        def save():
            self.threshold = round(var.get(), 3)
            self.logger.info("White", f"Threshold set to {self.threshold}")
            result["ok"] = True
            popup.destroy()

        ttk.Frame(frm).pack(pady=14)   # spacer

        btns = ttk.Frame(frm)
        btns.pack()
        ttk.Button(btns, text="Save",   command=save,   width=10).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancel", command=popup.destroy, width=10).pack(side=tk.LEFT, padx=6)

        popup.wait_window()            # ← blocks until closed
        return result["ok"]

    def _is_page_blank(self, page: fitz.Page) -> bool:
        """
        Heuristic blank-page detector.

        • Renders the page at 1/4 size (fast).  
        • Counts how many pixels are ≈ white (all channels ≥ 245).  
        • If white-pixel ratio ≥ self.threshold  → page is considered blank.
          ─ e.g. threshold 0.90 ≈ “90 % of the page is white”.
        """
        try:
            # low-dpi render for speed  (about 18 dpi)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25),
                                   colorspace=fitz.csRGB, alpha=False)
            data = pix.samples             # bytes -- 3 × pixels

            white_bytes = 0
            # count triplets where r,g,b are all > 245
            for i in range(0, len(data), 3):
                if data[i]   >= 245 and \
                   data[i+1] >= 245 and \
                   data[i+2] >= 245:
                    white_bytes += 3

            total_pixels = len(data) // 3
            white_ratio  = white_bytes / len(data)   # we divided by 3 above

            return white_ratio >= self.threshold
        except Exception as e:
            self.logger.error("White", f"Blank-page check failed: {e}")
            # On error treat page as *not* blank so we don’t delete content
            return False
                
    def scan_pdf_for_whitespace(self, show_progress=True):
        """
        Scan the selected PDF files for whitespace and return a list of file paths and their blank pages.

        Args:
            show_progress (bool): Whether to display a progress dialog.

        Returns:
            list[BlankPageInfo]: A list of BlankPageInfo objects containing file paths and blank pages.
        """
        self.logger.info("White", "Scanning PDF files for whitespace")

        # Show the threshold popup to allow the user to set the threshold
        if not self._ask_threshold():
            self.logger.info("White", "User cancelled threshold dialog.")
            return []
        # Initialize progress tracking
        self.files_scanned = 0
        self.pages_scanned = 0
        self.total_files = len(self.selection)
        self.total_pages = 0  # Will be calculated dynamically

        blank_page_info_list = []
        progress = DualProgressDialog(self.root, "Scanning PDF Files") if show_progress else None

        for file_idx, file_path in enumerate(self.selection):
            if progress:
                if progress.is_cancelled():
                    break
                progress.update_overall_progress(file_idx, self.total_files)
                progress.update_overall_status(f"Scanning file {file_idx + 1} of {self.total_files}")
                progress.update_message(f"Scanning {os.path.basename(file_path)}")

            try:
                pdf_document = fitz.open(file_path)
                num_pages = pdf_document.page_count
                self.total_pages += num_pages

                blank_pages = []
                for page_idx in range(num_pages):
                    if progress:
                        if progress.is_cancelled():
                            break
                        progress.update_current_progress(page_idx, num_pages)
                        progress.update_current_status(f"Scanning page {page_idx + 1} of {num_pages}")

                    # Detect blank pages
                    page = pdf_document[page_idx]
                    if self._is_page_blank(page):
                        blank_pages.append(page_idx + 1)  # Page numbers are 1-based

                    # Update class-level progress tracking
                    self.pages_scanned += 1

                blank_page_info_list.append(BlankPageInfo(file_path, blank_pages))
                self.files_scanned += 1

            except Exception as e:
                self.logger.error("White", f"Error scanning {file_path}: {str(e)}")
            finally:
                if progress:
                    progress.reset_current_progress()

        if progress:
            progress.close()

        self.logger.info("White", f"Scanning complete. Found blank pages in {len(blank_page_info_list)} file(s).")
        return blank_page_info_list

    def remove_white_page(self):
        """Scan and remove blank pages from selected PDFs based on the threshold."""
        self.logger.info("White", "Starting removal of white pages")

        # Scan for blank pages
        blank_page_info_list = self.scan_pdf_for_whitespace(show_progress=True)

        if not blank_page_info_list:
            self.logger.info("White", "No blank pages found.")
            return

        progress = DualProgressDialog(self.root, "Removing White Pages")

        for file_idx, blank_info in enumerate(blank_page_info_list):
            file_path = blank_info.get_file_path()
            blank_pages = blank_info.get_blank_pages()

            if progress.is_cancelled():
                break

            if not blank_pages:
                continue

            progress.update_overall_progress(file_idx, len(blank_page_info_list))
            progress.update_overall_status(f"Processing file {file_idx + 1} of {len(blank_page_info_list)}")
            progress.update_message(f"Removing pages from {os.path.basename(file_path)}")

            try:
                pdf_document = fitz.open(file_path)
                output_pdf_path = os.path.splitext(file_path)[0] + "_no_whitespace.pdf"
                new_pdf = fitz.open()

                total_pages = pdf_document.page_count
                for i in range(total_pages):
                    progress.update_current_progress(i, total_pages)
                    progress.update_current_status(f"Copying page {i + 1} of {total_pages}")

                    if (i + 1) not in blank_pages:
                        new_pdf.insert_pdf(pdf_document, from_page=i, to_page=i)

                new_pdf.save(output_pdf_path)
                new_pdf.close()
                pdf_document.close()

                self.logger.info("White", f"Saved cleaned PDF to {output_pdf_path}")
                self.pdf_files.append(output_pdf_path)       # <- NEW
                if hasattr(self, "status_label"):
                    self.status_label.config(
                        text=f"Removed {len(blank_pages)} blank page(s) → "
                              f"{os.path.basename(output_pdf_path)}"
                    )
            except Exception as e:
                self.logger.error("White", f"Failed to remove pages from {file_path}: {e}")

            finally:
                progress.reset_current_progress()

        progress.close()
        self.logger.info("White", "White page removal process complete.")

    # ───── glue for the host programme ──────────────────────────────
    def set_pdf_files(self, pdf_files: list[str]):
        """Receive the master list so we can append cleaned copies."""
        self.pdf_files = pdf_files            # keep reference

    def set_status_label(self, lbl: tk.Label):
        self.status_label = lbl               # optional live updates

    def get_completed_files(self) -> list[str]:
        """
        Return every file the main window should now list:
        originals + any ‘_no_whitespace.pdf’ we generated.
        """
        return self.pdf_files
    
class BlankPageInfo:
    """Class to represent a file and its blank pages."""
    def __init__(self, file_path, blank_pages):
        self.file_path = file_path
        self.blank_pages = blank_pages

    def get_file_path(self):
        return self.file_path
    
    def get_blank_pages(self):
        return self.blank_pages

    def __repr__(self):
        return f"BlankPageInfo(file_path={self.file_path}, blank_pages={self.blank_pages})"