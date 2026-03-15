import os
from pathlib import Path
from ImageControl import ImageControl

class AutoConvert:
    def __init__(self, root):
        self.root = root
        self.image_controller = ImageControl(root, None)  # Initialize ImageControl
        self.input_dir = "input"  # Folder to monitor
        self.converted_dir = "converted"  # Folder for processed files
        self.unsupported_dir = "unsupported"  # Folder for unsupported files
        self.supported_types = {".jpg", ".jpeg", ".png"}  # Supported file extensions
        self.flag = False  # Flag to indicate new files are processed

        # Ensure directories exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.converted_dir, exist_ok=True)
        os.makedirs(self.unsupported_dir, exist_ok=True)

        # Start the server
        self.start_server()

    def start_server(self):
        """Start the server to monitor the input directory."""
        self.check_for_new_files()
        self.root.after(1000, self.start_server)  # Check every 1 second

    def check_for_new_files(self):
        """Check the input directory for new files."""
        for file_name in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, file_name)
            if os.path.isfile(file_path):
                file_ext = Path(file_name).suffix.lower()

                if file_ext in self.supported_types:
                    self.convert_file(file_path)
                else:
                    self.handle_unsupported_file(file_path)

    def convert_file(self, file_path):
        """Convert supported files using ImageControl and move them to the converted directory."""
        try:
            # Use ImageControl to convert the image
            converted_files = self.image_controller.convert_image_to_pdf([file_path])
            if converted_files:
                # Move the converted file to the converted directory
                for converted_file in converted_files:
                    shutil.move(converted_file, self.converted_dir)

                # Remove the original file
                os.remove(file_path)
                self.flag = True  # Set the flag to indicate processing
        except Exception as e:
            self.image_controller.logger.error("AutoConvert", f"Error converting file {file_path}: {e}")

    def handle_unsupported_file(self, file_path):
        """Handle unsupported files by creating a .txt file."""
        file_name = os.path.basename(file_path)
        txt_file_name = f"{file_name}_NOT_SUPPORTED.txt"
        txt_file_path = os.path.join(self.unsupported_dir, txt_file_name)

        # Create a .txt file indicating the file is unsupported
        with open(txt_file_path, "w") as txt_file:
            txt_file.write(f"The file '{file_name}' is not supported for conversion.")

        # Monitor the file for removal
        self.root.after(1000, self.cleanup_unsupported_file, file_path, txt_file_path)

    def cleanup_unsupported_file(self, file_path, txt_file_path):
        """Delete the .txt file if the unsupported file is removed."""
        if not os.path.exists(file_path) and os.path.exists(txt_file_path):
            os.remove(txt_file_path)