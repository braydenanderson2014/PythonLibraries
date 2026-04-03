"""
Professional dark theme styles for PyQt6 GUI.

Colors:
- Background: #1E1E1E (dark gray)
- Surface: #2D2D2D (slightly lighter)
- Accent: #0078D4 (Microsoft blue)
- Text: #E0E0E0 (light gray)
- Success: #28A745 (green)
- Error: #DC3545 (red)
- Warning: #FFC107 (amber)
"""

DARK_STYLESHEET = """
    QMainWindow, QDialog, QWidget {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    
    QMenuBar {
        background-color: #252525;
        color: #E0E0E0;
        border-bottom: 1px solid #3D3D3D;
    }
    
    QMenuBar::item:selected {
        background-color: #0078D4;
    }
    
    QMenu {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3D3D3D;
    }
    
    QMenu::item:selected {
        background-color: #0078D4;
    }
    
    QTabWidget::pane {
        border: 1px solid #3D3D3D;
    }
    
    QTabBar::tab {
        background-color: #252525;
        color: #E0E0E0;
        padding: 8px 20px;
        border: 1px solid #3D3D3D;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: #0078D4;
        color: white;
    }
    
    QTabBar::tab:hover {
        background-color: #0066B2;
    }
    
    QPushButton {
        background-color: #0078D4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #0066B2;
    }
    
    QPushButton:pressed {
        background-color: #005A9E;
    }
    
    QPushButton:disabled {
        background-color: #555555;
        color: #999999;
    }
    
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3D3D3D;
        border-radius: 3px;
        padding: 4px;
        selection-background-color: #0078D4;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #0078D4;
    }
    
    QComboBox::drop-down {
        border: none;
    }
    
    QComboBox::down-arrow {
        image: url(:/icons/down-arrow.png);
    }
    
    QLabel {
        color: #E0E0E0;
    }
    
    QGroupBox {
        color: #E0E0E0;
        border: 1px solid #3D3D3D;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    
    QTableWidget, QTableView, QTreeView {
        background-color: #2D2D2D;
        alternate-background-color: #252525;
        gridline-color: #3D3D3D;
        color: #E0E0E0;
        border: 1px solid #3D3D3D;
    }
    
    QTableWidget::item:selected, QTableView::item:selected, QTreeView::item:selected {
        background-color: #0078D4;
        color: white;
    }
    
    QHeaderView::section {
        background-color: #252525;
        color: #E0E0E0;
        padding: 4px;
        border: none;
        border-right: 1px solid #3D3D3D;
    }
    
    QScrollBar:vertical {
        background-color: #1E1E1E;
        width: 12px;
        margin: 0px 0px 0px 0px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #555555;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #666666;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
    
    QScrollBar:horizontal {
        background-color: #1E1E1E;
        height: 12px;
        margin: 0px 0px 0px 0px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #555555;
        border-radius: 6px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #666666;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
    }
    
    QComboBox QAbstractItemView {
        background-color: #2D2D2D;
        color: #E0E0E0;
        selection-background-color: #0078D4;
        outline: none;
    }
    
    QCheckBox, QRadioButton {
        color: #E0E0E0;
        spacing: 5px;
    }
    
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
    }
    
    QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
        background-color: #2D2D2D;
        border: 1px solid #3D3D3D;
    }
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #0078D4;
        border: 1px solid #0078D4;
    }
    
    QSlider::groove:horizontal {
        border: 1px solid #3D3D3D;
        height: 6px;
        background: #252525;
        margin: 2px 0;
    }
    
    QSlider::handle:horizontal {
        background: #0078D4;
        border: 1px solid #0078D4;
        width: 13px;
        margin: -3px 0;
        border-radius: 6px;
    }
    
    QSlider::handle:horizontal:hover {
        background: #0066B2;
    }
    
    QProgressBar {
        border: 1px solid #3D3D3D;
        border-radius: 4px;
        background-color: #252525;
        color: white;
        text-align: center;
        height: 20px;
    }
    
    QProgressBar::chunk {
        background-color: #28A745;
        border-radius: 3px;
    }
    
    QToolTip {
        background-color: #252525;
        color: #E0E0E0;
        border: 1px solid #3D3D3D;
        border-radius: 3px;
        padding: 4px;
    }
    
    /* Status indicators */
    .status-running {
        background-color: #0078D4;
        color: white;
        border-radius: 3px;
        padding: 2px 8px;
    }
    
    .status-completed {
        background-color: #28A745;
        color: white;
        border-radius: 3px;
        padding: 2px 8px;
    }
    
    .status-error {
        background-color: #DC3545;
        color: white;
        border-radius: 3px;
        padding: 2px 8px;
    }
    
    .status-idle {
        background-color: #555555;
        color: #E0E0E0;
        border-radius: 3px;
        padding: 2px 8px;
    }
"""


def get_color(color_name: str) -> str:
    """Get a color by name."""
    colors = {
        "background": "#1E1E1E",
        "surface": "#2D2D2D",
        "border": "#3D3D3D",
        "text": "#E0E0E0",
        "text_secondary": "#A0A0A0",
        "accent": "#0078D4",
        "accent_hover": "#0066B2",
        "accent_active": "#005A9E",
        "success": "#28A745",
        "error": "#DC3545",
        "warning": "#FFC107",
        "info": "#17A2B8",
    }
    return colors.get(color_name, "#E0E0E0")
