import os
import threading
import subprocess
import time
import platform
import shutil
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController
from ProgressDialog import ProgressDialog

class Conversion:
    def __init__(self, root, selection):
        self.root = root
        self.selection = selection
        self.settings = SettingsController(root)
        self.logger = Logger()
        self.logger.info("Conversion", "==========================================================")
        self.logger.info("Conversion", " EVENT: INIT")
        self.logger.info("Conversion", "==========================================================")

    def set_selection(self, selection):
        self.selection = selection

    def get_libreoffice_command(self):
        """Get the LibreOffice command based on the current platform"""
        system = platform.system().lower()
        
        # Common LibreOffice executable names to try
        if system == "windows":
            # Windows paths and executable names
            possible_commands = [
                "soffice.exe",
                "soffice",
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
        elif system == "darwin":  # macOS
            possible_commands = [
                "soffice",
                "/Applications/LibreOffice.app/Contents/MacOS/soffice"
            ]
        else:  # Linux and other Unix-like systems
            possible_commands = [
                "soffice",
                "libreoffice",
                "/usr/bin/soffice",
                "/usr/local/bin/soffice",
                "/opt/libreoffice/program/soffice"
            ]
        
        # Try each command to see which one works
        for cmd in possible_commands:
            if shutil.which(cmd) or os.path.exists(cmd):
                self.logger.info("Conversion", f"Found LibreOffice command: {cmd}")
                return cmd
        
        # If none found, return the default
        self.logger.warning("Conversion", "LibreOffice command not found, using default 'soffice'")
        return "soffice"

    def is_libreoffice_installed(self):
        self.logger.info("Conversion", "Checking if LibreOffice is installed")
        try:
            cmd = self.get_libreoffice_command()
            result = subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def monitor_libreoffice_installation(self):
        def check_loop():
            while not self.is_libreoffice_installed():
                self.logger.info("Conversion", "LibreOffice not found. Retrying in 10 seconds...")
                time.sleep(10)
            self.logger.info("Conversion", "LibreOffice has been installed.")
            self.settings.settings["is_libre_installed"] = "true"
            self.settings.save_runtime_settings()

        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()

    def convert_to_pdf(self):
        self.logger.info("Conversion", "Starting conversion to PDF")
        output_paths = []

        if not self.is_libreoffice_installed():
            self.logger.error("Conversion", "LibreOffice is not installed or not found")
            messagebox.showerror("Error", "LibreOffice is required for conversion but was not found on your system.")
            return output_paths

        use_progress = len(self.selection) > 4
        progress = ProgressDialog(self.root, "Converting to PDF") if use_progress else None

        libreoffice_cmd = self.get_libreoffice_command()

        for idx, file_path in enumerate(self.selection):
            if progress:
                if progress.is_cancelled():
                    break
                progress.update_progress(idx, len(self.selection))
                progress.update_message(f"Converting {os.path.basename(file_path)}")

            try:
                output_dir = self.settings.get_setting("output_directory")
                os.makedirs(output_dir, exist_ok=True)
                
                cmd = [
                    libreoffice_cmd,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", output_dir,
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.error("Conversion", f"LibreOffice conversion failed for {file_path}: {result.stderr}")
                    continue

                output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                if os.path.exists(output_path):
                    output_paths.append(output_path)
                    self.logger.info("Conversion", f"Successfully converted {file_path} to {output_path}")
                else:
                    self.logger.warning("Conversion", f"Expected output file not found: {output_path}")
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Conversion", f"Conversion timeout for {file_path}")
            except Exception as e:
                self.logger.error("Conversion", f"Error converting {file_path}: {str(e)}")

        if progress:
            progress.close()

        return output_paths

    def convert_to_docx(self):
        self.logger.info("Conversion", "Starting conversion to DOCX")

        if not self.is_libreoffice_installed():
            self.logger.error("Conversion", "LibreOffice is not installed or not found")
            messagebox.showerror("Error", "LibreOffice is required for conversion but was not found on your system.")
            return

        use_progress = len(self.selection) > 4
        progress = ProgressDialog(self.root, "Converting to DOCX") if use_progress else None

        libreoffice_cmd = self.get_libreoffice_command()

        for idx, file_path in enumerate(self.selection):
            if progress:
                if progress.is_cancelled():
                    break
                progress.update_progress(idx, len(self.selection))
                progress.update_message(f"Converting {os.path.basename(file_path)}")

            try:
                output_dir = self.settings.get_setting("output_directory")
                os.makedirs(output_dir, exist_ok=True)
                
                cmd = [
                    libreoffice_cmd,
                    "--headless",
                    "--convert-to", "docx",
                    "--outdir", output_dir,
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.error("Conversion", f"LibreOffice conversion failed for {file_path}: {result.stderr}")
                    continue

                output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".docx"
                output_path = os.path.join(output_dir, output_filename)
                
                if os.path.exists(output_path):
                    self.logger.info("Conversion", f"Successfully converted {file_path} to {output_path}")
                else:
                    self.logger.warning("Conversion", f"Expected output file not found: {output_path}")
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Conversion", f"Conversion timeout for {file_path}")
            except Exception as e:
                self.logger.error("Conversion", f"Error converting {file_path}: {str(e)}")

        if progress:
            progress.close()

    def convert_to_pptx(self):
        self.logger.info("Conversion", "Starting conversion to PPTX")

        if not self.is_libreoffice_installed():
            self.logger.error("Conversion", "LibreOffice is not installed or not found")
            messagebox.showerror("Error", "LibreOffice is required for conversion but was not found on your system.")
            return

        use_progress = len(self.selection) > 4
        progress = ProgressDialog(self.root, "Converting to PPTX") if use_progress else None

        libreoffice_cmd = self.get_libreoffice_command()

        for idx, file_path in enumerate(self.selection):
            if progress:
                if progress.is_cancelled():
                    break
                progress.update_progress(idx, len(self.selection))
                progress.update_message(f"Converting {os.path.basename(file_path)}")

            try:
                output_dir = self.settings.get_setting("output_directory")
                os.makedirs(output_dir, exist_ok=True)
                
                cmd = [
                    libreoffice_cmd,
                    "--headless",
                    "--convert-to", "pptx",
                    "--outdir", output_dir,
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.error("Conversion", f"LibreOffice conversion failed for {file_path}: {result.stderr}")
                    continue

                output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".pptx"
                output_path = os.path.join(output_dir, output_filename)
                
                if os.path.exists(output_path):
                    self.logger.info("Conversion", f"Successfully converted {file_path} to {output_path}")
                else:
                    self.logger.warning("Conversion", f"Expected output file not found: {output_path}")
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Conversion", f"Conversion timeout for {file_path}")
            except Exception as e:
                self.logger.error("Conversion", f"Error converting {file_path}: {str(e)}")

        if progress:
            progress.close()
