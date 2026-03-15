import os
import tkinter as tk
import re
from markdown import markdown
from html.parser import HTMLParser
from PDFUtility.PDFLogger import Logger

class MarkdownParser(HTMLParser):
    """ A simple HTML to Tkinter Text parser for handling markdown formatting. """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.current_tags = []
        self.logger = Logger()
        self.logger.info("MARKDOWN","=================================================================")
        self.logger.info("MARKDOWN"," EVENT: INIT")
        self.logger.info("MARKDOWN","=================================================================")

    def handle_starttag(self, tag, attrs):
        if tag == 'strong' or tag == 'b':
            self.logger.info("MARKDOWN"," Appending bold to current tag")
            self.current_tags.append('bold')
        elif tag == 'em' or tag == 'i':
            self.logger.info("MARKDOWN"," Appending italics to current tag")
            self.current_tags.append('italic')

    def handle_endtag(self, tag):
        if tag == 'strong' or tag == 'b':
            self.logger.info("MARKDOWN"," Appending bold to end tag")
            self.current_tags.remove('bold')
        elif tag == 'em' or tag == 'i':
            self.logger.info("MARKDOWN"," Appending italics to end tag")
            self.current_tags.remove('italic')

    def handle_data(self, data):
        self.logger.info("MARKDOWN"," Handling data -> updating UI")
        self.text_widget.insert(tk.END, data, self.current_tags)