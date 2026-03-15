# editor/toolbar_manager.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable
import os

class ToolbarManager:
    """
    Professional toolbar that handles bootstrapping renderer-specific tools.
    Provides a clean, professional interface for tool management.
    """
    
    def __init__(self, parent_window, logger=None):
        self.parent = parent_window
        self.logger = logger
        self.toolbar_frame = None
        self.current_tools = {}
        self.tool_buttons = {}
        self.active_tool = None  # Now stores string tool name instead of BaseTool object
        self.renderer_toolbar_sections = {}
        
        self._create_toolbar()
    
    def _create_toolbar(self):
        """Create the main toolbar frame with professional styling."""
        self.toolbar_frame = ttk.Frame(self.parent, padding=(5, 2))
        self.toolbar_frame.pack(side="top", fill="x")
        
        # Create separator for visual appeal
        separator = ttk.Separator(self.toolbar_frame, orient='horizontal')
        separator.pack(fill='x', pady=(0, 2))
        
        # Main toolbar content frame
        self.toolbar_content = ttk.Frame(self.toolbar_frame)
        self.toolbar_content.pack(fill='x', expand=True)
        
        # Left side for renderer tools
        self.tools_frame = ttk.Frame(self.toolbar_content)
        self.tools_frame.pack(side='left', fill='x', expand=True)
        
        # Right side for global actions
        self.actions_frame = ttk.Frame(self.toolbar_content)
        self.actions_frame.pack(side='right')
        
        # Add global action buttons
        self._create_global_actions()
    
    def _create_global_actions(self):
        """Create global action buttons (save, etc.)."""
        # Save button
        save_btn = ttk.Button(
            self.actions_frame, 
            text="💾 Save", 
            command=self._on_save,
            width=8
        )
        save_btn.pack(side='right', padx=(2, 0))
        
        # Save As button  
        save_as_btn = ttk.Button(
            self.actions_frame,
            text="💾 Save As",
            command=self._on_save_as,
            width=10
        )
        save_as_btn.pack(side='right', padx=(2, 0))
    
    def load_renderer_tools(self, renderer, tab_id: str):
        """
        Load tools specific to a renderer and add them to the toolbar.
        This is called when a tab with a specific renderer becomes active.
        """
        # Clear existing renderer tools
        self._clear_renderer_tools()
        
        # Get tools from renderer (use class method)
        tools = renderer.tools() if hasattr(renderer, 'tools') else []
        
        if not tools:
            if self.logger:
                self.logger.info("ToolbarManager", f"No tools available for renderer {type(renderer).__name__}")
            return
        
        # Create tool section label
        if tools:
            label = ttk.Label(
                self.tools_frame, 
                text=f"{type(renderer).__name__} Tools:",
                font=('TkDefaultFont', 9, 'bold')
            )
            label.pack(side='left', padx=(0, 5))
            self.renderer_toolbar_sections['label'] = label
        
        # Add each tool as a button (tools are string names, not objects)
        for tool_name in tools:
            self._add_tool_button(tool_name, renderer, tab_id)
        
        # Add separator if we have tools
        if tools:
            sep = ttk.Separator(self.tools_frame, orient='vertical')
            sep.pack(side='left', fill='y', padx=5)
            self.renderer_toolbar_sections['separator'] = sep
    
    def _add_tool_button(self, tool_name: str, renderer, tab_id: str):
        """Add a professional-looking tool button."""
        # Create button with icon and text
        button_text = f"🔧 {tool_name}"
        
        btn = ttk.Button(
            self.tools_frame,
            text=button_text,
            command=lambda: self._activate_tool(tool_name, renderer, tab_id),
            width=len(button_text) + 2
        )
        btn.pack(side='left', padx=1)
        
        # Store button reference
        self.tool_buttons[tool_name] = btn
        
        # Add tooltip for tool
        self._add_tooltip(btn, f"Activate {tool_name} tool")
    
    def _add_tooltip(self, widget, text):
        """Add a tooltip to a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                tooltip, 
                text=text, 
                background='lightyellow', 
                relief='solid', 
                borderwidth=1,
                font=('TkDefaultFont', 9)
            )
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def _activate_tool(self, tool_name: str, renderer, tab_id: str):
        """Activate a tool and update button states."""
        # Deactivate current tool
        if self.active_tool:
            # Reset previous button state
            if self.active_tool in self.tool_buttons:
                self.tool_buttons[self.active_tool].state(['!pressed'])
        
        # Activate new tool
        self.active_tool = tool_name
        
        # Update button state
        if tool_name in self.tool_buttons:
            self.tool_buttons[tool_name].state(['pressed'])
        
        # Call renderer-specific tool activation
        if hasattr(renderer, f'activate_{tool_name.lower()}_tool'):
            getattr(renderer, f'activate_{tool_name.lower()}_tool')(tab_id)
        else:
            # Generic tool activation
            self.logger.info("ToolbarManager", f"Activated tool: {tool_name}")
            messagebox.showinfo("Tool Activated", f"{tool_name} tool activated for this tab.")
    
    def _clear_renderer_tools(self):
        """Clear all renderer-specific tools from toolbar."""
        # Deactivate current tool
        if self.active_tool:
            self.active_tool = None
        
        # Remove all tool buttons
        for button in self.tool_buttons.values():
            button.destroy()
        self.tool_buttons.clear()
        
        # Remove renderer sections
        for widget in self.renderer_toolbar_sections.values():
            widget.destroy()
        self.renderer_toolbar_sections.clear()
    
    def _on_save(self):
        """Handle save action."""
        if hasattr(self.parent, 'tab_manager'):
            tab_id = self.parent.tab_manager.get_current_tab_id()
            if tab_id:
                self.parent.filetypes.save(tab_id)
    
    def _on_save_as(self):
        """Handle save as action."""
        if hasattr(self.parent, 'tab_manager'):
            from tkinter import filedialog
            tab_id = self.parent.tab_manager.get_current_tab_id()
            if tab_id:
                file_path = filedialog.asksaveasfilename(
                    title="Save As",
                    filetypes=self.parent.filetypes.get_open_filetypes()
                )
                if file_path:
                    self.parent.filetypes.save_as(tab_id, file_path)
    
    def get_toolbar_frame(self):
        """Get the toolbar frame for layout purposes."""
        return self.toolbar_frame
    
    def update_for_tab(self, tab_id: str):
        """Update toolbar when tab changes."""
        if hasattr(self.parent, 'tab_manager'):
            tab_info = self.parent.tab_manager.tabs.get(tab_id)
            if tab_info and 'renderer_instance' in tab_info:
                renderer = tab_info['renderer_instance']
                self.load_renderer_tools(renderer, tab_id)
            else:
                self._clear_renderer_tools()
