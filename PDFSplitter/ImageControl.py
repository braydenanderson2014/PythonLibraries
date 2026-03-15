import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from PIL import Image
from PDFUtility.PDFLogger import Logger
from tkinter import filedialog
from tkinter import messagebox
import ttkbootstrap as ttk
from ProgressDialog import ProgressDialog
from SettingsController import SettingsController
import fitz  # PyMuPDF for PDF handling
from AnimatedProgressDialog import AnimatedProgressDialog
import threading
class ImageControl:

    def __init__(self, root, selection):
        self.selection = selection
        self.settings = SettingsController(root)
        self.animation_controller = AnimatedProgressDialog(root, "Converting Images to PDF", "Please wait pdf's are being converted")
        self.root = root
        self.pdf_files = []
        self.logger = Logger()
        self.logger.info("ImageControl", "==========================================================")
        self.logger.info("ImageControl", " EVENT: INIT")
        self.logger.info("ImageControl", "==========================================================")
        
    def set_selection(self, selection):
        self.selection = selection

    def convert_image_to_pdf(self, image_files: list[str]|None = None):
        """Convert selected image files to PDF with progress tracking (batch mode)"""
        self.logger.info("ImageControl", "Converting PDF's to Images")
        if image_files is None:
            image_files = filedialog.askopenfilenames(
                title="Select Images to Convert",
                filetypes=[
                    ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                    ("PNG Files", "*.png"),
                    ("JPEG Files", "*.jpg *.jpeg"),
                    ("All Files", "*.*")
                ]
            )
    
        if not image_files:
            self.logger.info("ImageControl", "No images selected for conversion")
            return []
    
        # Create ProgressDialog
        progress = ProgressDialog(
            self.root,  # Assuming `self.root` is the parent Tkinter window
            title="Converting Images to PDF",
            message=f"Converting {len(image_files)} image(s) to PDF..."
        )
    
        converted_files = []
        errors = []
    
        try:
            for i, image_path in enumerate(image_files):
                if progress.is_cancelled():
                    self.logger.info("ImageControl", "Image conversion cancelled by user")
                    break
                try:
                    image = Image.open(image_path)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    output_dir = self.settings.get_setting("output_directory")
                    pdf_path = os.path.join(output_dir, os.path.splitext(os.path.basename(image_path))[0] + '.pdf')
                    image.save(pdf_path, 'PDF', resolution=100.0)
                    self.pdf_files.append(pdf_path)
                    converted_files.append(pdf_path)
                except Exception as e:
                    self.logger.error("ImageControl", f"Error converting {os.path.basename(image_path)}: {str(e)}")
                    errors.append(f"{os.path.basename(image_path)}: {str(e)}")
                progress.update_progress(i + 1, len(image_files))
                progress.update_status(f"Processing: {os.path.basename(image_path)}")
            if not progress.is_cancelled():
                progress.update_message("Conversion complete!")
                progress.update_status("All images processed.")
            else:
                progress.update_message("Conversion cancelled.")
                progress.update_status("Operation was cancelled by the user.")
        finally:
            progress.close()
    
        # Show a single summary message
        if not progress.is_cancelled():
            msg = f"Converted {len(converted_files)} image(s) to PDF."
            if errors:
                msg += f"\n{len(errors)} error(s) occurred:\n" + "\n".join(errors)
            messagebox.showinfo("Batch Conversion Result", msg)
            self.logger.info("ImageControl", msg)
        return converted_files
    
    def start_converting_to_img(self, pdf_path=None):
        """Start the conversion of PDF files to images in a separate thread."""
        self.animation_controller.start_animation("Converting PDFs to Images", "Please wait while PDFs are being converted to images...")
        self.logger.info("ImageControl", "Starting conversion of PDF to images")
        thread = threading.Thread(target=self.pdf_to_img, args=(pdf_path,), daemon=True)
        thread.start()

    def pdf_to_img(self, pdf_path=None):
        # Function to convert pdf to image (batch mode)
        pdf_files_to_convert = []
        if pdf_path and len(pdf_path) > 0:
            pdf_files_to_convert = [pdf_path]
            self.logger.info("ImageControl", f"Converting provided PDF path: {pdf_path}")
        else:
            selection = self.selection
            if hasattr(selection, 'size') and callable(selection.size):
                sel_size = selection.size()
            else:
                sel_size = len(selection) if selection is not None else 0
            if sel_size < 1:
                self.logger.info("ImageControl","No PDF selected for conversion")
                messagebox.showerror("Error", "No PDF selected for conversion")
                return
            if hasattr(selection, 'get') and callable(selection.get):
                for i in range(sel_size):
                    pdf_files_to_convert.append(selection.get(i))
            else:
                pdf_files_to_convert.extend(selection)
            self.logger.info("ImageControl", f"Converting {len(pdf_files_to_convert)} selected PDF(s)")
        batch_errors = []
        batch_success = 0
        for current_pdf_path in pdf_files_to_convert:
            self.logger.info("ImageControl",f"Converting {current_pdf_path} to image")
            try:
                if not isinstance(current_pdf_path, str):
                    self.logger.error("ImageControl", f"Invalid PDF path: {current_pdf_path} (type: {type(current_pdf_path)})")
                    batch_errors.append(f"Invalid PDF path: {current_pdf_path}")
                    continue
                if not os.path.exists(current_pdf_path):
                    self.logger.error("ImageControl", f"PDF file does not exist: {current_pdf_path}")
                    batch_errors.append(f"PDF file does not exist: {current_pdf_path}")
                    continue
                self.animation_controller.set_message_safe(f"Converting {os.path.basename(current_pdf_path)} to images...")
                pdf_document = fitz.open(current_pdf_path)
                output_dir = self.settings.get_setting("output_path")
                if not output_dir:
                    output_dir = self.settings.get_setting("output_directory")
                if not output_dir:
                    output_dir = os.path.dirname(current_pdf_path)
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(current_pdf_path))[0]
                converted_images = []
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    if len(pdf_document) == 1:
                        image_path = os.path.join(output_dir, f"{base_name}.png")
                    else:
                        image_path = os.path.join(output_dir, f"{base_name}_page_{page_num + 1}.png")
                    pix.save(image_path)
                    converted_images.append(image_path)
                    self.logger.info("ImageControl", f"Saved page {page_num + 1} as {image_path}")
                pdf_document.close()
                self.logger.info("ImageControl",f"Converted {current_pdf_path} to {len(converted_images)} image(s)")
                batch_success += 1
            except Exception as e:
                self.logger.error("ImageControl",f"Error converting {current_pdf_path} to image: {str(e)}")
                batch_errors.append(f"{current_pdf_path}: {str(e)}")
        # Show a single summary message
        self.animation_controller.stop_animation()
        msg = f"Converted {batch_success} PDF(s) to images."
        if batch_errors:
            msg += f"\n{len(batch_errors)} error(s) occurred:\n" + "\n".join(batch_errors)
        messagebox.showinfo("Batch PDF to Image Result", msg)
        self.logger.info("ImageControl", msg)
        return


