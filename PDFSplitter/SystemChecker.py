import os
from SettingsController import SettingsController
from PDFUtility.PDFLogger import Logger
from pathlib import Path
import tempfile
class SystemChecker:
    def __init__(self, root):
        self.settings_controller = SettingsController(root)
        self.settings = self.settings_controller.load_settings()
        self.logger = Logger()

    def check_for_path_errors(self):
        path = self.settings.get("log_dir")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["log_dir"] = str(Path.home() / "Documents" / "PDFUtility" / "Logs")

        path = self.settings.get("temporary_file_location")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["temporary_file_location"] = tempfile.gettempdir()

        path  = self.settings.get("output_directory")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["output_directory"] = str(Path.home() / "Documents" / "PDFUtility" / "Output")

        path = self.settings.get("split_directory")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["split_directory"] = str(Path.home() / "Documents" / "PDFUtility" / "Split")

        path = self.settings.get("merge_directory")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["merge_directory"] = str(Path.home() / "Documents" / "PDFUtility" / "Merge")

        path = self.settings.get("convert_directory")
        if not os.path.exists(path):
            self.logger.info("SYSTEM", f"Path error: {path} does not exist.")
            self.settings["convert_directory"] = str(Path.home() / "Documents" / "PDFUtility" / "Convert")

        self.logger.info("SYSTEM", "All paths are valid.")
        self.settings_controller.save_runtime_settings()