# drag_drop_handler.py
"""
Robust drag and drop handler that gracefully handles different environments.
"""

import logging

class DragDropHandler:
    """Handles drag and drop functionality with fallback options."""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = False
        self.dnd_available = False
        self._test_dnd_availability()
    
    def _test_dnd_availability(self):
        """Test if drag and drop functionality is available."""
        try:
            import tkinterdnd2
            from tkinterdnd2 import TkinterDnD, DND_FILES
            
            # Try to create a test window
            test_root = TkinterDnD.Tk()
            test_root.withdraw()  # Hide it
            test_root.destroy()
            
            self.dnd_available = True
            self.logger.info("DragNDrop","Drag and drop functionality is available")
            
        except ImportError:
            self.logger.warning("DragNDrop""tkinterdnd2 not installed - drag and drop disabled")
            self.dnd_available = False
        except Exception as e:
            self.logger.warning("DragNDrop",f"Drag and drop not available: {e}")
            self.dnd_available = False
    
    def create_dnd_window(self, themename="darkly", **kwargs):
        """Create a drag and drop enabled window or fallback to regular window."""
        if self.dnd_available:
            try:
                from tkinterdnd2 import TkinterDnD
                import ttkbootstrap as ttk
                
                # Create DnD window
                root = TkinterDnD.Tk()
                
                # Apply ttkbootstrap theme
                try:
                    style = ttk.Style(theme=themename)
                    self.logger.info("DragNDrop",f"Created DnD window with theme: {themename}")
                except Exception as e:
                    self.logger.warning("DragNDrop",f"Could not apply theme: {e}")
                
                return root, True
                
            except Exception as e:
                self.logger.warning("DragNDrop",f"Failed to create DnD window: {e}")
        
        # Fallback to regular ttkbootstrap window
        try:
            import ttkbootstrap as ttk
            root = ttk.Window(themename=themename, **kwargs)
            self.logger.info("DragNDrop",f"Created regular window with theme: {themename}")
            return root, False
        except Exception as e:
            # Ultimate fallback to plain tkinter
            import tkinter as tk
            root = tk.Tk()
            self.logger.warning("DragNDrop","Using plain tkinter window - theming not available")
            return root, False
    
    def setup_drag_drop(self, widget, drop_callback):
        """Setup drag and drop on a widget."""
        if not self.dnd_available:
            self.logger.info("DragNDrop","Drag and drop not available - skipping setup")
            return False
        
        try:
            from tkinterdnd2 import DND_FILES
            
            # Register the widget for file drops
            if hasattr(widget, 'drop_target_register'):
                widget.drop_target_register(DND_FILES)
            else:
                self.logger.warning("DragNDrop","Widget doesn't support drop_target_register")
                return False
            
            # Bind the drop event
            if hasattr(widget, 'dnd_bind'):
                widget.dnd_bind('<<Drop>>', drop_callback)
            else:
                self.logger.warning("DragNDrop","Widget doesn't support dnd_bind")
                return False
            
            self.enabled = True
            self.logger.info("DragNDrop","Drag and drop setup successful")
            return True
            
        except Exception as e:
            self.logger.warning("DragNDrop",f"Failed to setup drag and drop: {e}")
            return False
    
    def is_enabled(self):
        """Check if drag and drop is enabled."""
        return self.enabled
    
    def is_available(self):
        """Check if drag and drop is available."""
        return self.dnd_available
    
    def get_file_paths(self, event):
        """Extract file paths from a drop event."""
        if not self.dnd_available:
            self.logger.warning("DragNDrop","Drag and drop not available - cannot get file paths")
            return []
        
        try:
            # Extract file paths from the event
            if hasattr(event, 'data'):
                file_paths = event.data
                
                # Parse file paths correctly - tkinterdnd2 wraps file paths with spaces in curly braces
                if isinstance(file_paths, str):
                    import re
                    
                    # Check if the entire string is wrapped in curly braces (single file with spaces)
                    if file_paths.startswith('{') and file_paths.endswith('}') and file_paths.count('{') == 1:
                        # Single file with spaces wrapped in curly braces
                        return [file_paths[1:-1]]
                    else:
                        # Multiple files or files without spaces
                        # Split by spaces, but handle files wrapped in curly braces
                        pattern = r'\{([^}]+)\}|(\S+)'
                        matches = re.findall(pattern, file_paths)
                        
                        result = []
                        for match in matches:
                            # match[0] is the content inside braces, match[1] is standalone file
                            file_path = match[0] if match[0] else match[1]
                            if file_path.strip():
                                result.append(file_path.strip())
                        
                        return result
                else:
                    return [str(file_paths)]
            else:
                self.logger.warning("DragNDrop","Event does not contain 'data' attribute")
                return []
        except Exception as e:
            self.logger.error("DragNDrop",f"Error extracting file paths: {e}")
            return []
