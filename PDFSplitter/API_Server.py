from PDFUtility.PDFLogger import Logger
from tqdm import tqdm
from flask import Flask, request, jsonify
from White import White
from Conversion import Conversion
from ImageControl import ImageControl
from MarkdownParser import MarkdownParser
from PlaybackControlDialog import PlaybackControlDialog
from SettingsController import SettingsController
from SplitController import SplitController
from MergeController import MergeController
from Utility import Utility
class APIServer:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        self.logger.info("APIServer", "==========================================================")
        self.logger.info("APIServer", " EVENT: INIT")
        self.logger.info("APIServer", "==========================================================")
        self.app = Flask(__name__)
        self.api_key = "your_api_key_here"
        self.setup_routes()
        self.white = White()
        self.conversion = Conversion()
        self.image_control = ImageControl()
        self.markdown_parser = MarkdownParser()
        self.settings_controller = SettingsController(self.root)
        self.split_controller = SplitController(self.root)
        self.merge_controller = MergeController(self.root)
        self.utility = Utility(self.root)


    def setup_routes(self):
        pass
        

    