"""
Attachment Manager - Handles file attachments for transactions
"""

import os
import shutil
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from assets.Logger import Logger

logger = Logger()
try:
    from .app_paths import ATTACHMENTS_DIR
except ImportError:
    from app_paths import ATTACHMENTS_DIR

class AttachmentManager:
    """Manages file attachments for transactions"""
    
    def __init__(self, attachments_dir=None):
        self.attachments_dir = attachments_dir or ATTACHMENTS_DIR
        # Ensure attachments directory exists
        os.makedirs(self.attachments_dir, exist_ok=True)
        logger.info("AttachmentManager", f"Attachments directory: {self.attachments_dir}")
    
    def add_attachment(self, source_path, transaction_id=None):
        """
        Add an attachment by copying the file to the attachments directory.
        
        Args:
            source_path: Path to the source file
            transaction_id: Optional transaction identifier for organizing files
            
        Returns:
            dict: Attachment metadata
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Get file info
        filename = os.path.basename(source_path)
        file_size = os.path.getsize(source_path)
        file_type = mimetypes.guess_type(source_path)[0] or 'application/octet-stream'
        
        # Generate unique filename using hash + timestamp to avoid collisions
        file_hash = self._get_file_hash(source_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{file_hash}_{timestamp}{ext}"
        
        # Destination path
        dest_path = os.path.join(self.attachments_dir, unique_filename)
        
        # Copy file
        shutil.copy2(source_path, dest_path)
        
        # Return attachment metadata
        return {
            'filename': filename,  # Original filename
            'stored_filename': unique_filename,  # Unique stored filename
            'path': dest_path,  # Full path
            'relative_path': os.path.join('resources/attachments', unique_filename),  # Relative path
            'type': file_type,
            'size': file_size,
            'uploaded_date': datetime.now().isoformat(),
            'transaction_id': transaction_id
        }
    
    def delete_attachment(self, attachment_data):
        """
        Delete an attachment file.
        
        Args:
            attachment_data: Attachment metadata dict
            
        Returns:
            bool: True if successfully deleted
        """
        file_path = attachment_data.get('path')
        if not file_path:
            # Try to construct path from stored_filename
            stored_filename = attachment_data.get('stored_filename')
            if stored_filename:
                file_path = os.path.join(self.attachments_dir, stored_filename)
        
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                logger.error("AttachmentManager", f"Failed to delete attachment: {e}")
                return False
        logger.warning("AttachmentManager", f"Attachment file not found for deletion: {file_path}")
        return False
    
    def get_attachment_path(self, attachment_data):
        """
        Get the full path to an attachment file.
        
        Args:
            attachment_data: Attachment metadata dict
            
        Returns:
            str: Full path to the file, or None if not found
        """
        # Try path field first
        file_path = attachment_data.get('path')
        if file_path and os.path.exists(file_path):
            logger.info("AttachmentManager", f"Found attachment at path: {file_path}")
            return file_path
        
        # Try constructing from stored_filename
        stored_filename = attachment_data.get('stored_filename')
        if stored_filename:
            file_path = os.path.join(self.attachments_dir, stored_filename)
            if os.path.exists(file_path):
                logger.info("AttachmentManager", f"Found attachment at path: {file_path}")
                return file_path
        
        # Try constructing from relative_path
        relative_path = attachment_data.get('relative_path')
        if relative_path:
            file_path = os.path.join(os.path.dirname(__file__), '..', relative_path)
            if os.path.exists(file_path):
                logger.info("AttachmentManager", f"Found attachment at path: {file_path}")
                return file_path
        logger.warning("AttachmentManager", "Attachment file not found")
        return None
    
    def attachment_exists(self, attachment_data):
        """Check if an attachment file exists"""
        attachment = self.get_attachment_path(attachment_data)
        logger.info("AttachmentManager", f"Attachment exists: {attachment is not None}")
        return attachment is not None
    
    def get_file_icon(self, file_type):
        """
        Get an appropriate icon/emoji for a file type.
        
        Args:
            file_type: MIME type of the file
            
        Returns:
            str: Unicode icon/emoji
        """
        if not file_type:
            return '📄'
        
        if file_type.startswith('image/'):
            return '🖼️'
        elif file_type == 'application/pdf':
            return '📕'
        elif file_type.startswith('text/'):
            return '📝'
        elif file_type.startswith('video/'):
            return '🎥'
        elif file_type.startswith('audio/'):
            return '🎵'
        elif 'spreadsheet' in file_type or 'excel' in file_type:
            return '📊'
        elif 'document' in file_type or 'word' in file_type:
            return '📄'
        elif 'zip' in file_type or 'archive' in file_type:
            return '📦'
        else:
            return '📎'
        
    
    def format_file_size(self, size_bytes):
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
            logger.info("AttachmentManager", f"Formatted file size: {size_bytes:.1f} {unit}")
        return f"{size_bytes:.1f} TB"
    
    def _get_file_hash(self, file_path, algorithm='md5'):
        """
        Calculate hash of a file for unique identification.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: md5)
            
        Returns:
            str: Hexadecimal hash string (first 12 characters)
        """
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        file_hash = hash_obj.hexdigest()[:12]  # Use first 12 chars for shorter filenames
        logger.info("AttachmentManager", f"Calculated {algorithm} hash: {file_hash} for file: {file_path}")
        return file_hash
    def is_supported_image(self, file_type):
        """Check if file type is a supported image format"""
        supported_images = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
        
        result = file_type in supported_images
        logger.info("AttachmentManager", f"Is supported image: {result} for file type: {file_type}")
        return result
    
    def is_supported_pdf(self, file_type):
        """Check if file type is PDF"""
        result = file_type == 'application/pdf'
        logger.info("AttachmentManager", f"Is supported PDF: {result} for file type: {file_type}")
        return result
    
    def cleanup_orphaned_files(self, active_attachments):
        """
        Remove attachment files that are no longer referenced by any transaction.
        
        Args:
            active_attachments: List of all attachment metadata dicts currently in use
        """
        # Get all stored filenames currently in use
        active_filenames = set()
        for attachment in active_attachments:
            stored_filename = attachment.get('stored_filename')
            if stored_filename:
                active_filenames.add(stored_filename)
        
        # Check all files in attachments directory
        deleted_count = 0
        if os.path.exists(self.attachments_dir):
            for filename in os.listdir(self.attachments_dir):
                if filename not in active_filenames:
                    file_path = os.path.join(self.attachments_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info("AttachmentManager", f"Removed orphaned attachment: {filename}")
                    except Exception as e:
                        logger.warning("AttachmentManager", f"Could not remove orphaned file {filename}: {e}")
            logger.info("AttachmentManager", f"Total orphaned attachments removed: {deleted_count}")
        return deleted_count
