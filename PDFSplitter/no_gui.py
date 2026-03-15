from PDFUtility.PDFLogger import Logger
from tqdm import tqdm
from White import White
from Conversion import Conversion
from ImageControl import ImageControl
from MarkdownParser import MarkdownParser
from PlaybackControlDialog import PlaybackControlDialog
from SettingsController import SettingsController
from SplitController import SplitController
from MergeController import MergeController
from Utility import Utility

class no_gui:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        self.logger.info("no_gui", "==========================================================")
        self.logger.info("no_gui", " EVENT: INIT")
        self.logger.info("no_gui", "==========================================================")
        self.white = White(self.root)
        self.conversion = Conversion(self.root)
        self.image_control = ImageControl(self.root)
        self.markdown_parser = MarkdownParser(self.root)
        self.settings_controller = SettingsController(self.root)
        self.split_controller = SplitController(self.root)
        self.merge_controller = MergeController(self.root)
        self.utility = Utility(self.root)

    def main(self):
        self.logger.info("no_gui", f"Welcome to PDF Splitter version {self.settings_controller["system_version"]}")
        self.logger.info("no_gui", "==========================================================")
        self.logger.info("no_gui", "1. Add PDF's to program")
        self.logger.info("no_gui", "2. Scan folder for PDF's")
        self.logger.info("no_gui", "3. Convert Menu")
        self.logger.info("no_gui", "4. Settings")
        self.logger.info("no_gui", "5. Playback Control")
        self.logger.info("no_gui", "6. PDF Control Menu")


    def pdf_control_menu(self):
        self.logger.info("no_gui", "==========================================================")
        self.logger.info("no_gui", " PDF Control Menu")
        self.logger.info("no_gui", "==========================================================")
        self.logger.info("no_gui", "1. Split PDF")
        self.logger.info("no_gui", "2. Merge PDF")
        self.logger.info("no_gui", "3. Convert to Image")
        self.logger.info("no_gui", "4. Convert Image to PDF")
        self.logger.info("no_gui", "5. Scan For White/Blank Pages")
        self.logger.info("no_gui", "6. Remove White/Blank Pages")