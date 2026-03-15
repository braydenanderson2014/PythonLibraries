import importlib
import json
from pathlib import Path
from typing import Dict, Any

from .base import BaseRenderer
from .renderers_registry import RENDERER_MODULES

class PluginManager:
    """
    Manages renderer plugins in a PyInstaller-compatible way.
    Uses explicit registry instead of dynamic discovery.
    """
    
    def __init__(self, editor):
        self.editor = editor
        self._loaded_renderers = {}
        
    def load_all_renderers(self) -> Dict[str, Any]:
        """
        Load all registered renderers and return registry.
        Returns: {extension: (RendererClass, metadata)}
        """
        registry = {}
        # Track all renderers by extension to handle priorities
        extension_renderers = {}
        
        for module_name in RENDERER_MODULES:
            try:
                # Import the renderer module
                module = importlib.import_module(module_name)
                renderer_class = getattr(module, "Renderer")
                
                # Load metadata from settings.json
                metadata = self._load_renderer_metadata(module_name)
                
                # Store the renderer class and metadata for later prioritization
                priority = metadata.get("priority", 10)  # Default to low priority
                
                # Register for all supported extensions
                extensions = metadata.get("extensions", 
                           metadata.get("supported_extensions", []))
                
                for ext in extensions:
                    ext = ext.lower()
                    # Track this renderer for the extension
                    if ext not in extension_renderers:
                        extension_renderers[ext] = []
                    extension_renderers[ext].append((renderer_class, metadata, priority))
                    
                self._loaded_renderers[module_name] = {
                    'class': renderer_class,
                    'metadata': metadata
                }
                
                self.editor.logger.info(
                    "PluginManager", 
                    f"Loaded renderer: {metadata.get('name', module_name)} (priority: {priority})"
                )
                
            except Exception as e:
                self.editor.logger.warning(
                    "PluginManager",
                    f"Failed to load renderer {module_name}: {e}"
                )
        
        # Now select the highest priority renderer for each extension
        for ext, renderers in extension_renderers.items():
            # Sort by priority (lower number = higher priority)
            sorted_renderers = sorted(renderers, key=lambda x: x[2])
            if sorted_renderers:
                # Get the highest priority renderer (first in sorted list)
                renderer_class, metadata, priority = sorted_renderers[0]
                registry[ext] = (renderer_class, metadata)
                self.editor.logger.info(
                    "PluginManager",
                    f"Using {metadata.get('name', 'unnamed')} as the renderer for {ext} (priority: {priority})"
                )
                
        return registry
    
    def _load_renderer_metadata(self, module_name: str) -> Dict[str, Any]:
        """Load settings.json for a renderer module."""
        # Convert module path to settings.json path
        # e.g., "editor.renderers.pdf_renderer.renderer" -> "pdf_renderer"
        parts = module_name.split('.')
        renderer_name = parts[-2]  # Get the renderer folder name
        
        # Build path to settings.json
        settings_path = Path(__file__).parent / renderer_name / "settings.json"
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.editor.logger.warning(
                "PluginManager",
                f"Could not load settings for {renderer_name}: {e}"
            )
            return {
                "name": renderer_name,
                "extensions": [],
                "description": f"Renderer for {renderer_name}"
            }
    
    def get_renderer_info(self, module_name: str) -> Dict[str, Any]:
        """Get information about a loaded renderer."""
        return self._loaded_renderers.get(module_name, {})
    
    def list_loaded_renderers(self) -> Dict[str, Dict[str, Any]]:
        """Return all loaded renderers with their metadata."""
        return self._loaded_renderers.copy()