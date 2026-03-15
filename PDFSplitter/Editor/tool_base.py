# editor/tool_base.py

class BaseTool:
    """
    Abstract base class for all editing tools. A tool is responsible for
    handling mouse events on the Canvas (click, drag, keypress), updating
    overlay state, and eventually committing annotations to the DocumentModel.
    """

    def __init__(self, editor_window, name: str, icon=None):
        """
        editor_window: reference to the EditorWindow (so tool can query the 
                       active Canvas, DocumentModel, etc.)
        name: a string identifier (e.g. "Text", "Highlight")
        icon: a Tk PhotoImage or filepath to show on the toolbar.
        """
        self.editor = editor_window
        self.name = name
        self.icon = icon
        self.active = False

    def activate(self):
        """
        Called when user selects this tool. Should bind mouse/canvas events.
        """
        self.active = True

    def deactivate(self):
        """
        Called when user deselects this tool. Should unbind all events.
        """
        self.active = False

    def on_mouse_down(self, event):
        """
        Called when user presses mouse on the Canvas.  
        Coordinates are event.x, event.y in Canvas space.
        """
        raise NotImplementedError()

    def on_mouse_move(self, event):
        """
        Called when user moves mouse (with button down) if tool cares (e.g. for drawing).
        """
        pass

    def on_mouse_up(self, event):
        """
        Called when mouse button released.
        """
        pass

    def commit(self, page_number: int):
        """
        Write any pending annotation(s) for the current page into the DocumentModel.
        E.g. for a highlight tool, it will store a fitz.HighlightAnnot object in 
        DocumentModel.tool_annotations[page_number].
        Called when user switches pages or clicks “Save.”
        """
        pass
