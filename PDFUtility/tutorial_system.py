"""
Interactive Tutorial System for PDF Utility
Provides first-run guided tours that highlight UI elements and explain features.
"""

import os
import json
import sys
import math
import traceback
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFrame, QApplication, QGraphicsDropShadowEffect, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPolygon, QPainterPath
from PDFLogger import Logger
class TutorialOverlay(QWidget):
    """Overlay widget that highlights specific areas and shows tutorial content"""
    
    next_step = pyqtSignal()
    skip_tutorial = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()  # Add logger instance
        self.target_widget = None
        self.highlight_rect = QRect()
        self.tutorial_text = ""
        self.step_number = 0
        self.total_steps = 0
        self.highlight_style = "dashed_border"  # dashed_border, solid_border, glow, pulse
        self.arrow_direction = "auto"  # auto, left, right, top, bottom, none
        self.arrow_offset = 0  # Offset from center of target
        self.animation_timer = QTimer()
        self.animation_frame = 0
        self.setup_ui()
        self.setup_animations()
        
    def setup_animations(self):
        """Setup animation timers for visual effects"""
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(50)  # 20 FPS for smooth animations
        
    def setup_ui(self):
        """Setup the overlay UI"""
        # Make overlay transparent and fill parent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Tutorial content box
        self.content_frame = QFrame(self)
        self.content_frame.setFixedWidth(350)
        self.content_frame.setMinimumHeight(200)  # Ensure minimum height
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 250);
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(3, 3)
        self.content_frame.setGraphicsEffect(shadow)
        
        # Content layout
        content_layout = QVBoxLayout(self.content_frame)
        
        # Step indicator
        self.step_label = QLabel()
        self.step_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 12px;")
        content_layout.addWidget(self.step_label)
        
        # Tutorial text
        self.text_label = QTextEdit()
        self.text_label.setReadOnly(True)
        self.text_label.setMaximumHeight(120)
        self.text_label.setMinimumHeight(80)  # Ensure minimum height
        self.text_label.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        content_layout.addWidget(self.text_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.skip_button = QPushButton("Skip Tutorial")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.skip_button.clicked.connect(self.skip_tutorial.emit)
        button_layout.addWidget(self.skip_button)
        
        button_layout.addStretch()
        
        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.next_button.clicked.connect(self.next_step.emit)
        button_layout.addWidget(self.next_button)
        
        content_layout.addLayout(button_layout)
        
    def update_animation(self):
        """Update animation frame for visual effects"""
        self.animation_frame = (self.animation_frame + 1) % 60  # 3 second cycle at 20 FPS
        self.update()  # Trigger repaint for animation effects
        
    def set_tutorial_step(self, target_widget, text, step_num, total_steps, button_text="Next", 
                         highlight_style="dashed_border", arrow_direction="auto", arrow_offset=0):
        """Set up a tutorial step with enhanced visual options"""
        self.logger.debug("TutorialManager", f"set_tutorial_step called with target_widget: {target_widget}")
        
        self.target_widget = target_widget
        self.tutorial_text = text
        self.step_number = step_num
        self.total_steps = total_steps
        self.highlight_style = highlight_style
        self.arrow_direction = arrow_direction
        self.arrow_offset = arrow_offset
        
        # Store parameters for potential retry
        self._retry_params = {
            'text': text,
            'step_num': step_num,
            'total_steps': total_steps,
            'button_text': button_text,
            'highlight_style': highlight_style,
            'arrow_direction': arrow_direction,
            'arrow_offset': arrow_offset
        }
        
        # Update UI
        self.step_label.setText(f"Step {step_num} of {total_steps}")
        self.text_label.setHtml(text)
        self.next_button.setText(button_text)
        
        # Debug the target widget before processing
        self.logger.debug("TutorialManager", f"Target widget before visibility check: {target_widget}")
        self.logger.debug("TutorialManager", f"Target widget type: {type(target_widget) if target_widget is not None else 'None'}")
        self.logger.debug("TutorialManager", f"Target widget is None check: {target_widget is None}")
        self.logger.debug("TutorialManager", f"Target widget bool check: {bool(target_widget) if target_widget is not None else 'False'}")
        
        # Check if it's a deleted PyQt object
        if target_widget is not None:
            try:
                # Try to access a basic PyQt property
                _ = target_widget.objectName()
                self.logger.debug("TutorialManager", f"Target widget is valid PyQt object")
                widget_is_valid = True
            except RuntimeError as e:
                self.logger.error("TutorialManager", f"Target widget is deleted PyQt object: {e}")
                widget_is_valid = False
                target_widget = None  # Clear the invalid reference
            except Exception as e:
                self.logger.error("TutorialManager", f"Target widget access error: {e}")
                widget_is_valid = False
        else:
            widget_is_valid = False
        
        # Check if the widget is visible - the manager should have already handled visibility logic
        is_widget_visible = target_widget.isVisible() if target_widget is not None and widget_is_valid else False
        
        # Calculate highlight rectangle
        if target_widget is not None and widget_is_valid and is_widget_visible:
            self.logger.debug("TutorialManager", f"Target widget is effectively visible: {target_widget}")
            try:
                parent_widget = target_widget.parent()
                self.logger.debug("TutorialManager", f"Target widget parent: {parent_widget}")
            except (TypeError, AttributeError):
                self.logger.debug("TutorialManager", "Target widget parent access failed")
                parent_widget = None
            
            self.logger.debug("TutorialManager", f"Overlay parent: {self.parent()}")
            self.logger.debug("TutorialManager", f"Overlay size: {self.size()}")
            
            # Get widget geometry in its parent coordinates
            widget_rect = target_widget.geometry()
            self.logger.debug("TutorialManager", f"Widget rect in parent coords: {widget_rect}")
            
            # Convert to global coordinates, then to overlay coordinates
            global_top_left = target_widget.mapToGlobal(target_widget.rect().topLeft())
            global_bottom_right = target_widget.mapToGlobal(target_widget.rect().bottomRight())
            self.logger.debug("TutorialManager", f"Global coords: {global_top_left} to {global_bottom_right}")
            
            # Map to overlay coordinates
            overlay_top_left = self.mapFromGlobal(global_top_left)
            overlay_bottom_right = self.mapFromGlobal(global_bottom_right)
            self.logger.debug("TutorialManager", f"Overlay coords: {overlay_top_left} to {overlay_bottom_right}")
            
            # Create rectangle in overlay coordinates
            self.highlight_rect = QRect(overlay_top_left, overlay_bottom_right)
            self.logger.debug("TutorialManager", f"Final highlight rect: {self.highlight_rect}")
            
        elif target_widget is not None and widget_is_valid and not is_widget_visible:
            # Widget exists but is not visible - since the manager should have already handled this,
            # we'll just log it and continue without highlighting
            self.logger.warning("TutorialManager", f"Target widget is not visible, tutorial will continue without highlighting: {target_widget}")
            self.highlight_rect = QRect()
            self.logger.debug("TutorialManager", "Set empty highlight rect - widget not visible")
        else:
            if target_widget is None or not widget_is_valid:
                self.logger.warning("TutorialManager", f"Target widget is invalid - widget exists: {target_widget is not None}, valid: {widget_is_valid if 'widget_is_valid' in locals() else 'Unknown'}")
            self.highlight_rect = QRect()
            self.logger.debug("TutorialManager", "Set empty highlight rect")
        
        # Position content box
        self.position_content_box()
        
        # Ensure proper sizing
        self.content_frame.adjustSize()
        
        # Show with animation
        self.show()
        self.animate_in()
        
    def position_content_box(self):
        """Position the content box optimally relative to highlight area"""
        if not self.parent():
            return
            
        parent_rect = self.parent().rect()
        
        if self.highlight_rect.isValid():
            # Try to position to the right of highlight
            x = self.highlight_rect.right() + 20
            y = self.highlight_rect.top()
            
            # If too far right, position to the left
            if x + self.content_frame.width() > parent_rect.width():
                x = self.highlight_rect.left() - self.content_frame.width() - 20
            
            # If still doesn't fit, center horizontally
            if x < 0:
                x = (parent_rect.width() - self.content_frame.width()) // 2
            
            # Adjust vertical position if needed
            if y + self.content_frame.height() > parent_rect.height():
                y = parent_rect.height() - self.content_frame.height() - 20
            
            if y < 0:
                y = 20
                
        else:
            # Center if no highlight area
            x = (parent_rect.width() - self.content_frame.width()) // 2
            y = (parent_rect.height() - self.content_frame.height()) // 2
        
        self.content_frame.move(x, y)
    
    def animate_in(self):
        """Animate the tutorial box appearing"""
        self.content_frame.setProperty("geometry", QRect(
            self.content_frame.x(), 
            self.content_frame.y() - 20,
            self.content_frame.width(),
            self.content_frame.height()
        ))
        
        self.animation = QPropertyAnimation(self.content_frame, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.content_frame.geometry())
        self.animation.setEndValue(QRect(
            self.content_frame.x(),
            self.content_frame.y() + 20,
            self.content_frame.width(),
            self.content_frame.height()
        ))
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
    
    def retry_highlight_calculation(self, target_widget):
        """Retry highlighting calculation after making widget visible"""
        if target_widget is not None and target_widget.isVisible() and hasattr(self, '_retry_params'):
            self.logger.debug("TutorialManager", f"Retrying highlight calculation for now-visible widget: {target_widget}")
            params = self._retry_params
            self.set_tutorial_step(
                target_widget,
                params['text'],
                params['step_num'],
                params['total_steps'],
                params['button_text'],
                params['highlight_style'],
                params['arrow_direction'],
                params['arrow_offset']
            )
        else:
            self.logger.warning("TutorialManager", f"Widget still not visible after retry: {target_widget}")
            if not hasattr(self, '_retry_params'):
                self.logger.warning("TutorialManager", "No retry parameters stored")

    def _is_widget_in_tab(self, widget, tab_widget):
        """Check if widget is a descendant of tab_widget"""
        current = widget
        while current is not None:
            if current == tab_widget:
                return True
            try:
                current = current.parent()
            except (TypeError, AttributeError):
                current = None
        return False

    def paintEvent(self, event):
        """Paint the overlay with highlight and arrows"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill entire overlay with semi-transparent dark
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        # Debug highlight rect
        self.logger.debug("TutorialManager", f"paintEvent called - highlight_rect valid: {self.highlight_rect.isValid()}")
        if self.highlight_rect.isValid():
            self.logger.debug("TutorialManager", f"Drawing highlight at: {self.highlight_rect}")
        
        # Draw highlight area if valid
        if self.highlight_rect.isValid():
            self.draw_highlight(painter)
            
        # Draw arrow if needed
        if self.arrow_direction != "none" and self.highlight_rect.isValid():
            self.draw_arrow(painter)
    
    def draw_highlight(self, painter):
        """Draw the highlight around the target widget"""
        # Create highlight area with border
        margin = 8
        highlight_rect = self.highlight_rect.adjusted(-margin, -margin, margin, margin)
        
        # Clear the highlight area
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(highlight_rect, Qt.GlobalColor.transparent)
        
        # Reset composition mode
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Draw highlight based on style
        if self.highlight_style == "dashed_border":
            self.draw_dashed_border_highlight(painter, highlight_rect)
        elif self.highlight_style == "solid_border":
            self.draw_solid_border_highlight(painter, highlight_rect)
        elif self.highlight_style == "glow":
            self.draw_glow_highlight(painter, highlight_rect)
        elif self.highlight_style == "pulse":
            self.draw_pulse_highlight(painter, highlight_rect)
    
    def draw_dashed_border_highlight(self, painter, rect):
        """Draw dashed border highlight"""
        pen = QPen(QColor(52, 152, 219), 3)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 5, 5)
    
    def draw_solid_border_highlight(self, painter, rect):
        """Draw solid border highlight"""
        pen = QPen(QColor(52, 152, 219), 4)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(52, 152, 219, 30)))  # Semi-transparent fill
        painter.drawRoundedRect(rect, 5, 5)
    
    def draw_glow_highlight(self, painter, rect):
        """Draw glowing highlight effect"""
        # Draw multiple rings for glow effect
        for i in range(5):
            alpha = 60 - (i * 10)
            width = 2 + i
            glow_rect = rect.adjusted(-i, -i, i, i)
            
            pen = QPen(QColor(52, 152, 219, alpha), width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(glow_rect, 5 + i, 5 + i)
    
    def draw_pulse_highlight(self, painter, rect):
        """Draw pulsing highlight effect"""
        # Calculate pulse intensity based on animation frame
        pulse_intensity = (math.sin(self.animation_frame * 0.2) + 1) / 2  # 0 to 1
        
        # Base color with pulsing alpha
        base_alpha = int(40 + (pulse_intensity * 60))  # 40 to 100
        border_alpha = int(150 + (pulse_intensity * 105))  # 150 to 255
        
        # Draw pulsing border
        pen = QPen(QColor(52, 152, 219, border_alpha), 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(52, 152, 219, base_alpha)))
        painter.drawRoundedRect(rect, 5, 5)
    
    def draw_arrow(self, painter):
        """Draw arrow pointing to the highlighted element"""
        if not self.highlight_rect.isValid():
            return
            
        # Determine arrow direction
        arrow_dir = self.determine_arrow_direction()
        if arrow_dir == "none":
            return
            
        # Calculate arrow position and properties
        arrow_start, arrow_end = self.calculate_arrow_positions(arrow_dir)
        
        # Draw the arrow
        self.draw_animated_arrow(painter, arrow_start, arrow_end)
    
    def determine_arrow_direction(self):
        """Determine the best arrow direction"""
        if self.arrow_direction != "auto":
            return self.arrow_direction
            
        # Auto-determine based on content box and highlight positions
        content_center = self.content_frame.geometry().center()
        highlight_center = self.highlight_rect.center()
        
        dx = highlight_center.x() - content_center.x()
        dy = highlight_center.y() - content_center.y()
        
        # Choose direction based on largest difference
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "bottom" if dy > 0 else "top"
    
    def calculate_arrow_positions(self, direction):
        """Calculate start and end positions for the arrow"""
        content_rect = self.content_frame.geometry()
        highlight_center = self.highlight_rect.center()
        
        # Add offset to arrow positioning
        if direction in ["left", "right"]:
            offset_point = QPointF(0, self.arrow_offset)
        else:
            offset_point = QPointF(self.arrow_offset, 0)
        
        if direction == "right":
            start = QPointF(content_rect.right(), content_rect.center().y()) + offset_point
            end = QPointF(self.highlight_rect.left() - 10, highlight_center.y()) + offset_point
        elif direction == "left":
            start = QPointF(content_rect.left(), content_rect.center().y()) + offset_point
            end = QPointF(self.highlight_rect.right() + 10, highlight_center.y()) + offset_point
        elif direction == "bottom":
            start = QPointF(content_rect.center().x(), content_rect.bottom()) + offset_point
            end = QPointF(highlight_center.x(), self.highlight_rect.top() - 10) + offset_point
        elif direction == "top":
            start = QPointF(content_rect.center().x(), content_rect.top()) + offset_point
            end = QPointF(highlight_center.x(), self.highlight_rect.bottom() + 10) + offset_point
        else:
            return QPointF(), QPointF()
        
        return start, end
    
    def draw_animated_arrow(self, painter, start, end):
        """Draw an animated arrow from start to end point"""
        if start.isNull() or end.isNull():
            return
            
        # Calculate arrow properties
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 20:  # Too short to draw meaningful arrow
            return
            
        # Normalize direction
        unit_x = dx / length
        unit_y = dy / length
        
        # Animation effect - make arrow "breathe"
        pulse = (math.sin(self.animation_frame * 0.3) + 1) / 2  # 0 to 1
        animated_length = length * (0.8 + 0.2 * pulse)  # 80% to 100% of original length
        
        # Calculate animated end point
        animated_end = QPointF(
            start.x() + unit_x * animated_length,
            start.y() + unit_y * animated_length
        )
        
        # Arrow styling
        arrow_color = QColor(255, 193, 7)  # Bright yellow/orange for visibility
        arrow_alpha = int(200 + (pulse * 55))  # 200 to 255
        arrow_color.setAlpha(arrow_alpha)
        
        # Draw main arrow line
        pen = QPen(arrow_color, 4)
        painter.setPen(pen)
        painter.drawLine(start, animated_end)
        
        # Draw arrowhead
        arrowhead_size = 15
        
        # Calculate arrowhead points
        arrowhead_point1 = QPointF(
            animated_end.x() - arrowhead_size * unit_x - arrowhead_size * 0.5 * unit_y,
            animated_end.y() - arrowhead_size * unit_y + arrowhead_size * 0.5 * unit_x
        )
        arrowhead_point2 = QPointF(
            animated_end.x() - arrowhead_size * unit_x + arrowhead_size * 0.5 * unit_y,
            animated_end.y() - arrowhead_size * unit_y - arrowhead_size * 0.5 * unit_x
        )
        
        # Draw filled arrowhead
        arrowhead = QPolygon([
            animated_end.toPoint(),
            arrowhead_point1.toPoint(),
            arrowhead_point2.toPoint()
        ])
        
        painter.setBrush(QBrush(arrow_color))
        painter.setPen(QPen(arrow_color, 2))
        painter.drawPolygon(arrowhead)
    
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        self.position_content_box()

class TutorialManager:
    """Manages tutorial state and progression"""
    
    def __init__(self, parent_window, settings_controller=None):
        self.logger = Logger()
        self.logger.debug("TutorialManager", "TutorialManager initializing")
        self.parent_window = parent_window
        self.settings_controller = settings_controller
        self.overlay = None
        self.current_tutorial = None
        self.current_step = 0
        self.tutorial_definitions = {}
        self.load_tutorial_definitions()
        
        # Tutorial queue and priority system
        self.tutorial_queue = []
        self.tutorial_priorities = {}  # Will be populated from JSON files
        
    def create_tutorial_step(self, target, text, button_text="Next", highlight_style="dashed_border", 
                           arrow_direction="auto", arrow_offset=0):
        """Create a tutorial step with enhanced visual options"""
        return {
            "target": target,
            "text": text,
            "button_text": button_text,
            "highlight_style": highlight_style,
            "arrow_direction": arrow_direction,
            "arrow_offset": arrow_offset
        }
    
    def create_pointing_step(self, target, text, arrow_direction="auto", button_text="Next"):
        """Create a tutorial step with a prominent pointing arrow"""
        return self.create_tutorial_step(
            target, text, button_text, 
            highlight_style="solid_border", 
            arrow_direction=arrow_direction
        )
    
    def create_glowing_step(self, target, text, button_text="Next"):
        """Create a tutorial step with a glowing highlight effect"""
        return self.create_tutorial_step(
            target, text, button_text, 
            highlight_style="glow", 
            arrow_direction="auto"
        )
    
    def create_pulsing_step(self, target, text, button_text="Next"):
        """Create a tutorial step with a pulsing highlight effect"""
        return self.create_tutorial_step(
            target, text, button_text, 
            highlight_style="pulse", 
            arrow_direction="auto"
        )
    
    def show_quick_tip(self, target_widget, text, duration=3000, highlight_style="glow"):
        """Show a quick tip without full tutorial progression"""
        if not self.is_tutorial_enabled():
            return
            
        # Create temporary overlay
        temp_overlay = TutorialOverlay(self.parent_window)
        temp_overlay.resize(self.parent_window.size())
        
        # Set up the tip
        temp_overlay.set_tutorial_step(
            target_widget, text, 1, 1, "Got it!", highlight_style, "auto", 0
        )
        
        # Auto-hide after duration
        QTimer.singleShot(duration, temp_overlay.deleteLater)
        self.tutorial_definitions = {}
        self.load_tutorial_definitions()
        
    def get_tutorial_setting(self, setting_name, default_value=True):
        """Get tutorial setting from settings controller"""
        if self.settings_controller:
            return self.settings_controller.get_setting("tutorials", setting_name, default_value)
        return default_value
    
    def set_tutorial_setting(self, setting_name, value):
        """Set tutorial setting in settings controller"""
        if self.settings_controller:
            self.settings_controller.set_setting("tutorials", setting_name, value)
            self.settings_controller.save_settings()
    
    def is_tutorial_enabled(self):
        """Check if tutorials are enabled globally"""
        return self.get_tutorial_setting("enabled", True)
    
    def should_show_first_run_tutorials(self):
        """Check if first-run tutorials should be shown"""
        return self.get_tutorial_setting("show_first_run", True)
    
    def should_auto_start_tutorials(self):
        """Check if tutorials should auto-start"""
        return self.get_tutorial_setting("auto_start", True)
    
    def load_tutorial_definitions(self):
        """Load tutorial step definitions dynamically from JSON files"""
        self.tutorial_definitions = {}
        self.tutorial_priorities = {}  # Reset priorities to load from JSON
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tutorials_dir = os.path.join(script_dir, "Tutorials")
        
        if not os.path.exists(tutorials_dir):
            self.logger.warning("TutorialManager", f"Warning: Tutorials directory not found at {tutorials_dir}")
            return
        
        # Load all JSON files from the Tutorials directory
        try:
            for filename in os.listdir(tutorials_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(tutorials_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            tutorial_data = json.load(f)
                        
                        # Extract the tutorial name, steps, and priority
                        tutorial_name = tutorial_data.get('name')
                        tutorial_steps = tutorial_data.get('steps', [])
                        tutorial_priority = tutorial_data.get('priority', 50)  # Default priority 50
                        
                        if tutorial_name and tutorial_steps:
                            self.tutorial_definitions[tutorial_name] = tutorial_steps
                            self.tutorial_priorities[tutorial_name] = tutorial_priority
                            self.logger.debug("TutorialManager", f"Loaded tutorial: {tutorial_name} ({len(tutorial_steps)} steps, priority: {tutorial_priority})")
                        else:
                            self.logger.warning("TutorialManager", f"Warning: Invalid tutorial format in {filename}")

                    except json.JSONDecodeError as e:
                        self.logger.error("TutorialManager", f"Error parsing JSON in {filename}: {e}")
                    except Exception as e:
                        self.logger.error("TutorialManager", f"Error loading tutorial {filename}: {e}")

        except Exception as e:
            self.logger.error("TutorialManager", f"Error scanning tutorials directory: {e}")

        self.logger.info("TutorialManager", f"Loaded {len(self.tutorial_definitions)} tutorials from JSON files")

    def add_tutorial_from_dict(self, tutorial_data):
        """Add a tutorial from a dictionary (for dynamic creation)"""
        tutorial_name = tutorial_data.get('name')
        tutorial_steps = tutorial_data.get('steps', [])
        
        if tutorial_name and tutorial_steps:
            self.tutorial_definitions[tutorial_name] = tutorial_steps
            return True
        return False
    
    def save_tutorial_to_json(self, tutorial_name, filepath=None):
        """Save a tutorial to a JSON file"""
        if tutorial_name not in self.tutorial_definitions:
            return False
        
        if filepath is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tutorials_dir = os.path.join(script_dir, "Tutorials")
            filepath = os.path.join(tutorials_dir, f"{tutorial_name}.json")
        
        tutorial_data = {
            "name": tutorial_name,
            "title": tutorial_name.replace('_', ' ').title(),
            "description": f"Tutorial for {tutorial_name}",
            "steps": self.tutorial_definitions[tutorial_name]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(tutorial_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error("TutorialManager", f"Error saving tutorial {tutorial_name}: {e}")
            return False
    
    def reload_tutorials(self):
        """Reload tutorials from JSON files (useful for development/testing)"""
        self.load_tutorial_definitions()
    
    def get_available_tutorials(self):
        """Get list of available tutorial names"""
        return list(self.tutorial_definitions.keys())
    
    def get_tutorial_info(self, tutorial_name):
        """Get information about a specific tutorial"""
        if tutorial_name not in self.tutorial_definitions:
            return None
        
        steps = self.tutorial_definitions[tutorial_name]
        return {
            "name": tutorial_name,
            "step_count": len(steps),
            "steps": steps
        }
    
    def validate_tutorial_json(self, filepath):
        """Validate a tutorial JSON file format"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            if 'name' not in data:
                return False, "Missing 'name' field"
            if 'steps' not in data:
                return False, "Missing 'steps' field"
            if not isinstance(data['steps'], list):
                return False, "'steps' must be a list"
            
            # Validate each step
            for i, step in enumerate(data['steps']):
                if not isinstance(step, dict):
                    return False, f"Step {i} must be a dictionary"
                if 'target' not in step:
                    return False, f"Step {i} missing 'target' field"
                if 'text' not in step:
                    return False, f"Step {i} missing 'text' field"
            
            return True, "Valid tutorial format"
            
        except json.JSONDecodeError as e:
            return False, f"JSON parsing error: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    
    def should_show_tutorial(self, tutorial_name):
        """Check if tutorial should be shown based on settings"""
        # Check if tutorials are globally enabled
        if not self.is_tutorial_enabled():
            return False
        
        # Check specific tutorial completion status
        completed_tutorials = self.get_tutorial_setting("completed", {})
        if isinstance(completed_tutorials, dict):
            return not completed_tutorials.get(tutorial_name, False)
        
        return True  # Default to showing if no record
    
    def mark_tutorial_completed(self, tutorial_name):
        """Mark a tutorial as completed"""
        try:
            completed_tutorials = self.get_tutorial_setting("completed", {})
            if not isinstance(completed_tutorials, dict):
                completed_tutorials = {}
            
            completed_tutorials[tutorial_name] = True
            self.set_tutorial_setting("completed", completed_tutorials)
        except Exception as e:
            self.logger.error("TutorialManager", f"Error saving tutorial completion: {e}")
    
    def reset_tutorial_completion(self, tutorial_name=None):
        """Reset tutorial completion status"""
        if tutorial_name:
            # Reset specific tutorial
            completed_tutorials = self.get_tutorial_setting("completed", {})
            if isinstance(completed_tutorials, dict) and tutorial_name in completed_tutorials:
                del completed_tutorials[tutorial_name]
                self.set_tutorial_setting("completed", completed_tutorials)
        else:
            # Reset all tutorials
            self.set_tutorial_setting("completed", {})
    
    def add_to_tutorial_queue(self, tutorial_name):
        """Add tutorial to queue with priority ordering"""
        if tutorial_name in [item['name'] for item in self.tutorial_queue]:
            # Tutorial already in queue
            return False
            
        priority = self.tutorial_priorities.get(tutorial_name, 50)  # Default priority
        tutorial_item = {"name": tutorial_name, "priority": priority}
        
        # Insert in priority order (lower number = higher priority)
        inserted = False
        for i, item in enumerate(self.tutorial_queue):
            if priority < item["priority"]:
                self.tutorial_queue.insert(i, tutorial_item)
                inserted = True
                break
        
        if not inserted:
            self.tutorial_queue.append(tutorial_item)
            
        self.logger.debug("TutorialManager", f"Added '{tutorial_name}' to queue with priority {priority}. Queue: {[item['name'] for item in self.tutorial_queue]}")
        return True
    
    def process_tutorial_queue(self):
        """Process the next tutorial in the queue"""
        if not self.tutorial_queue or self.current_tutorial is not None:
            return False
            
        # Get highest priority tutorial from queue
        tutorial_item = self.tutorial_queue.pop(0)
        tutorial_name = tutorial_item["name"]
        
        self.logger.debug("TutorialManager", f"Processing tutorial from queue: '{tutorial_name}'")
        return self.start_tutorial_directly(tutorial_name)
    
    def start_tutorial_directly(self, tutorial_name):
        """Start tutorial directly without queue checks (internal use)"""
        if tutorial_name not in self.tutorial_definitions:
            self.logger.warning("TutorialManager", f"Tutorial '{tutorial_name}' not found in definitions")
            return False
        
        self.logger.debug("TutorialManager", f"Starting tutorial '{tutorial_name}' directly")
        self.current_tutorial = tutorial_name
        self.current_step = 0
        
        # Create overlay
        self.overlay = TutorialOverlay(self.parent_window)
        self.overlay.resize(self.parent_window.size())
        self.overlay.next_step.connect(self.next_step)
        self.overlay.skip_tutorial.connect(self.skip_tutorial)
        
        # Start first step
        self.logger.debug("TutorialManager", "Calling show_current_step()")
        self.show_current_step()
        return True
    
    # Widget-specific tutorial starter methods
    def start_split_tutorial(self):
        """Start tutorial for PDF splitter widget"""
        return self.start_tutorial("split_widget")
    
    def start_merge_tutorial(self):
        """Start tutorial for PDF merger widget"""
        return self.start_tutorial("merge_widget")
    
    def start_image_converter_tutorial(self):
        """Start tutorial for image converter widget"""
        return self.start_tutorial("image_converter")
    
    def start_white_space_tutorial(self):
        """Start tutorial for white space removal widget"""
        return self.start_tutorial("white_space_widget")
    
    def start_tts_tutorial(self):
        """Start tutorial for text-to-speech widget"""
        return self.start_tutorial("tts_widget")
    
    def start_search_tutorial(self):
        """Start tutorial for file search widget"""
        return self.start_tutorial("search_widget")
    
    def show_widget_tutorial_if_first_time(self, widget_name):
        """Show tutorial for a widget if it's the first time accessing it"""
        if (self.is_tutorial_enabled() and 
            self.get_tutorial_setting("show_on_tab_switch", True) and
            self.should_show_tutorial(widget_name)):
            return self.start_tutorial(widget_name)
        return False
    
    def enable_tutorials(self):
        """Enable tutorial system"""
        self.set_tutorial_setting("enabled", True)
    
    def disable_tutorials(self):
        """Disable tutorial system"""
        self.set_tutorial_setting("enabled", False)
    
    def set_auto_start(self, enabled):
        """Set whether tutorials auto-start for new users"""
        self.set_tutorial_setting("auto_start", enabled)
    
    def set_show_first_run(self, enabled):
        """Set whether to show first-run tutorials"""
        self.set_tutorial_setting("show_first_run", enabled)
    
    def start_tutorial(self, tutorial_name, force=False):
        """Start a tutorial if it hasn't been completed, or add to queue if another is active"""
        self.logger.debug("TutorialManager", f"start_tutorial called with tutorial_name: '{tutorial_name}', force: {force}")
        
        # Check if tutorials are globally enabled (unless forced)
        if not force and not self.is_tutorial_enabled():
            self.logger.debug("TutorialManager", "Tutorial not enabled, skipping")
            return False
            
        # Check if this specific tutorial should be shown
        if not force and not self.should_show_tutorial(tutorial_name):
            self.logger.debug("TutorialManager", f"Tutorial '{tutorial_name}' should not be shown")
            return False
        
        # Main application tutorial gets special priority
        if tutorial_name == "main_application":
            if self.current_tutorial is not None:
                # Add current tutorial back to queue and clear it to start main tutorial
                self.logger.debug("TutorialManager", f"Main application tutorial preempting '{self.current_tutorial}'")
                current_tutorial_name = self.current_tutorial
                
                # Clean up current tutorial without marking as completed
                if self.overlay:
                    self.overlay.hide()
                    self.overlay.deleteLater()
                    self.overlay = None
                self.current_tutorial = None
                self.current_step = 0
                
                # Add the interrupted tutorial to front of queue
                self.add_to_tutorial_queue(current_tutorial_name)
                
            return self.start_tutorial_directly(tutorial_name)
        
        # If another tutorial is active, add to queue instead
        if not force and self.current_tutorial is not None:
            self.logger.debug("TutorialManager", f"Another tutorial '{self.current_tutorial}' is already active, adding '{tutorial_name}' to queue")
            return self.add_to_tutorial_queue(tutorial_name)
        
        # Start tutorial directly
        return self.start_tutorial_directly(tutorial_name)
    
    def auto_start_main_tutorial(self):
        """Auto-start main tutorial if conditions are met"""
        if (self.is_tutorial_enabled() and 
            self.should_auto_start_tutorials() and 
            self.should_show_first_run_tutorials() and
            self.should_show_tutorial("main_application")):
            # Main application tutorial always takes priority - start immediately
            return self.start_tutorial("main_application", force=False)
        return False
    
    def show_current_step(self):
        """Show the current tutorial step"""
        self.logger.debug("TutorialManager", f"show_current_step called - current_tutorial: {self.current_tutorial}, overlay: {self.overlay}")
        
        if not self.current_tutorial or not self.overlay:
            return
        
        steps = self.tutorial_definitions[self.current_tutorial]
        if self.current_step >= len(steps):
            self.complete_tutorial()
            return
        
        step = steps[self.current_step]
        self.logger.debug("TutorialManager", f"Processing step {self.current_step + 1}: {step}")
        
        # Find target widget
        target_widget = None
        target_name = step.get("target")
        self.logger.debug("TutorialManager", f"Looking for target widget: '{target_name}'")
        
        if target_name:
            target_widget = self.find_widget_by_name(target_name)
            self.logger.debug("TutorialManager", f"Target widget found: {target_widget}")
            
            # Check if widget is effectively visible and try to make it visible if needed
            if target_widget is not None:
                if not self._is_widget_effectively_visible(target_widget):
                    self.logger.debug("TutorialManager", f"Target widget not visible, attempting to make visible: {target_widget}")
                    # The _is_widget_effectively_visible method will try to switch tabs if needed
                    # Try once more after potential tab switch
                    if not self._is_widget_effectively_visible(target_widget):
                        self.logger.warning("TutorialManager", f"Unable to make target widget visible: {target_widget}")
                else:
                    self.logger.debug("TutorialManager", f"Target widget is visible: {target_widget}")
        
        # Get visual style options
        highlight_style = step.get("highlight_style", "dashed_border")
        arrow_direction = step.get("arrow_direction", "auto")
        arrow_offset = step.get("arrow_offset", 0)
        
        self.logger.debug("TutorialManager", f"Setting tutorial step with target: {target_widget}, style: {highlight_style}")
        
        # Show step with enhanced visuals
        self.overlay.set_tutorial_step(
            target_widget,
            step["text"],
            self.current_step + 1,
            len(steps),
            step.get("button_text", "Next"),
            highlight_style,
            arrow_direction,
            arrow_offset
        )
    
    def find_widget_by_name(self, name):
        """Find a widget by its object name or common attribute"""
        self.logger.debug("TutorialManager", f"find_widget_by_name called with name: '{name}'")
        
        # Try to find widget by object name first
        widget = self.parent_window.findChild(QWidget, name)
        if widget is not None:
            self.logger.debug("TutorialManager", f"Found widget '{name}' by object name: {widget}")
            return widget
        else:
            self.logger.debug("TutorialManager", f"Widget '{name}' not found by object name, trying alternatives")
        
        # Handle special cases for main application widgets
        if name == "menuBar":
            return self.parent_window.menuBar()
        elif name == "statusBar":
            # Check if statusBar is a method or attribute
            if hasattr(self.parent_window, 'statusBar'):
                status_bar = getattr(self.parent_window, 'statusBar')
                if callable(status_bar):
                    return status_bar()
                else:
                    return status_bar
            return self.parent_window.statusBar()
        elif name == "tabs" and hasattr(self.parent_window, 'tabs'):
            return self.parent_window.tabs
        
        # Try common attribute names on main window
        if hasattr(self.parent_window, name):
            attr = getattr(self.parent_window, name)
            if isinstance(attr, QWidget):
                self.logger.debug("TutorialManager", f"Found widget '{name}' as main window attribute: {attr}")
                return attr
        
        # Try to find in current tab if it's a tab widget
        if hasattr(self.parent_window, 'tabs'):
            current_widget = self.parent_window.tabs.currentWidget()
            if current_widget is not None and hasattr(current_widget, name):
                attr = getattr(current_widget, name)
                if isinstance(attr, QWidget):
                    return attr
        
        # If still not found, try to search all tabs for the widget
        # This is important for file lists that are in different tab widgets
        # First check the current active tab, then check all tabs
        if hasattr(self.parent_window, 'tabs'):
            # First try the current tab
            current_tab_index = self.parent_window.tabs.currentIndex()
            current_tab_widget = self.parent_window.tabs.currentWidget()
            
            # Check current tab first for better performance and accuracy
            if current_tab_widget is not None:
                # Try to find by attribute name
                if hasattr(current_tab_widget, name):
                    attr = getattr(current_tab_widget, name)
                    if isinstance(attr, QWidget):
                        self.logger.debug("TutorialManager", f"Found widget '{name}' in current tab as attribute: {type(attr).__name__}")
                        return attr
                
                # Try to find by object name
                widget = current_tab_widget.findChild(QWidget, name)
                if widget is not None:
                    self.logger.debug("TutorialManager", f"Found widget '{name}' in current tab by object name: {widget}")
                    return widget
            
            # If not found in current tab, search all tabs
            for i in range(self.parent_window.tabs.count()):
                # Skip the current tab since we already checked it
                if i == current_tab_index:
                    continue
                    
                tab_widget = self.parent_window.tabs.widget(i)
                if tab_widget is not None and hasattr(tab_widget, name):
                    attr = getattr(tab_widget, name)
                    if isinstance(attr, QWidget):
                        # Debug print to help with troubleshooting
                        self.logger.debug("TutorialManager", f"Found widget '{name}' in tab {i} as attribute: {type(attr).__name__}")
                        self.logger.debug("TutorialManager", f"Widget visibility: {attr.isVisible()}")
                        self.logger.debug("TutorialManager", f"Widget geometry: {attr.geometry()}")
                        parent_widget = attr.parent() if hasattr(attr, 'parent') and attr.parent else None
                        self.logger.debug("TutorialManager", f"Widget parent: {parent_widget}")
                        return attr
                
                # Also try to find by object name within this tab (non-current tabs)
                if tab_widget is not None:
                    widget = tab_widget.findChild(QWidget, name)
                    if widget is not None:
                        self.logger.debug("TutorialManager", f"Found widget '{name}' in tab {i} by object name: {widget}")
                        self.logger.debug("TutorialManager", f"Widget visibility: {widget.isVisible()}")
                        self.logger.debug("TutorialManager", f"Widget geometry: {widget.geometry()}")
                        parent_widget = widget.parent() if hasattr(widget, 'parent') and widget.parent else None
                        self.logger.debug("TutorialManager", f"Widget parent: {parent_widget}")
                        return widget
            
            # Final fallback: search for specific widget types across all tabs
            # This handles widgets that might not have proper object names set
            widget_type_fallbacks = {
                "pdf_list": "PDFListWidget",
                "file_list": "QListWidget"
            }
            
            if name in widget_type_fallbacks:
                expected_type = widget_type_fallbacks[name]
                for i in range(self.parent_window.tabs.count()):
                    tab_widget = self.parent_window.tabs.widget(i)
                    if tab_widget is not None:
                        all_widgets = tab_widget.findChildren(QWidget)
                        for child_widget in all_widgets:
                            widget_type_str = str(type(child_widget))
                            if expected_type in widget_type_str:
                                self.logger.debug("TutorialManager", f"Found {expected_type} in tab {i}: {child_widget}")
                                self.logger.debug("TutorialManager", f"{expected_type} object name: {child_widget.objectName()}")
                                self.logger.debug("TutorialManager", f"{expected_type} visibility: {child_widget.isVisible()}")
                                self.logger.debug("TutorialManager", f"{expected_type} geometry: {child_widget.geometry()}")
                                parent_widget = child_widget.parent() if hasattr(child_widget, 'parent') and child_widget.parent else None
                                self.logger.debug("TutorialManager", f"{expected_type} parent: {parent_widget}")
                                # Only return if the objectName matches exactly (avoid empty objectName matches)
                                if child_widget.objectName() == name:
                                    return child_widget
                                # If no exact match found but this is the current tab, return the widget if visible
                                elif i == current_tab_index and child_widget.isVisible():
                                    self.logger.debug("TutorialManager", f"Using {expected_type} from current tab as fallback")
                                    return child_widget
        
        # Debug print for unsuccessful searches
        self.logger.warning("TutorialManager", f"Widget '{name}' not found anywhere")
        return None
    
    def _is_widget_effectively_visible(self, widget):
        """Check if widget is effectively visible, even in inactive tabs"""
        if widget is None:
            return False
            
        try:
            # First check basic PyQt visibility
            if widget.isVisible():
                self.logger.debug("TutorialManager", f"Widget is visible via isVisible(): {widget}")
                return True
            
            self.logger.debug("TutorialManager", f"Widget not visible via isVisible(), checking alternatives: {widget}")
            
            # If not visible according to PyQt, check if it's in an inactive tab
            # but the tab itself is part of a visible tab widget
            
            # Check if widget has geometry (is laid out)
            if widget.geometry().isEmpty():
                self.logger.debug("TutorialManager", f"Widget has empty geometry: {widget}")
                return False
            
            # Check if widget is hidden explicitly
            if widget.isHidden():
                self.logger.debug("TutorialManager", f"Widget is explicitly hidden: {widget}")
                return False
            
            # For widgets in tabs, check if the parent tab widget is visible
            # and if so, make the widget's tab active
            if hasattr(self.parent_window, 'tabs'):
                self.logger.debug("TutorialManager", f"Checking tabs for widget: {widget}")
                self.logger.debug("TutorialManager", f"Tab widget visible: {self.parent_window.tabs.isVisible()}")
                self.logger.debug("TutorialManager", f"Total tabs: {self.parent_window.tabs.count()}")
                self.logger.debug("TutorialManager", f"Current tab index: {self.parent_window.tabs.currentIndex()}")
                
                for i in range(self.parent_window.tabs.count()):
                    tab_widget = self.parent_window.tabs.widget(i)
                    self.logger.debug("TutorialManager", f"Checking tab {i}: {tab_widget}")
                    
                    if tab_widget is not None:
                        is_descendant = self._widget_is_descendant_of(widget, tab_widget)
                        self.logger.debug("TutorialManager", f"Widget IS descendant of tab {i}: {is_descendant}")
                        
                        if is_descendant:
                            # Widget is in a tab - check if tab widget itself is visible
                            if self.parent_window.tabs.isVisible():
                                self.logger.debug("TutorialManager", f"Widget found in tab {i}, switching to make visible")
                                # Switch to this tab to make the widget visible
                                old_index = self.parent_window.tabs.currentIndex()
                                self.parent_window.tabs.setCurrentIndex(i)
                                self.logger.debug("TutorialManager", f"Switched from tab {old_index} to tab {i}")
                                
                                # Force a layout update - make sure currentWidget() is not None
                                current_widget = self.parent_window.tabs.currentWidget()
                                if current_widget is not None:
                                    current_widget.update()
                                    self.logger.debug("TutorialManager", f"Updated current widget: {current_widget}")
                                else:
                                    self.logger.warning("TutorialManager", f"currentWidget() returned None after switching to tab {i}")
                                
                                # Check again after switching
                                is_visible_now = widget.isVisible()
                                self.logger.debug("TutorialManager", f"Widget visibility after tab switch: {is_visible_now}")
                                return is_visible_now
                            else:
                                self.logger.debug("TutorialManager", f"Tab widget is not visible")
                                return False
                        else:
                            # Widget is not a descendant - check if it might be a direct child of the tab
                            # This handles cases where the widget hierarchy isn't properly set up
                            try:
                                # Try to find the widget within this tab using findChild
                                found_widget = tab_widget.findChild(type(widget), widget.objectName())
                                if found_widget == widget:
                                    self.logger.debug("TutorialManager", f"Widget found as direct child of tab {i} via findChild")
                                    # Switch to this tab
                                    if self.parent_window.tabs.isVisible():
                                        old_index = self.parent_window.tabs.currentIndex()
                                        self.parent_window.tabs.setCurrentIndex(i)
                                        self.logger.debug("TutorialManager", f"Switched from tab {old_index} to tab {i} (direct child)")
                                        
                                        # Update the tab
                                        current_widget = self.parent_window.tabs.currentWidget()
                                        if current_widget is not None:
                                            current_widget.update()
                                        
                                        # Check visibility again
                                        is_visible_now = widget.isVisible()
                                        self.logger.debug("TutorialManager", f"Widget visibility after tab switch (direct child): {is_visible_now}")
                                        return is_visible_now
                            except Exception as e:
                                self.logger.debug("TutorialManager", f"Error checking direct child in tab {i}: {e}")
                    else:
                        self.logger.debug("TutorialManager", f"Tab {i} widget is None")
            
            # Special case: if we're looking for pdf_list and didn't find it, 
            # it's probably in the merger tab (tab 1), so switch there and try again
            if hasattr(self.parent_window, 'tabs') and widget.objectName() == "pdf_list":
                self.logger.debug("TutorialManager", f"Special handling for pdf_list - switching to merger tab")
                merger_tab_index = 1  # Usually the second tab is the merger
                if merger_tab_index < self.parent_window.tabs.count():
                    old_index = self.parent_window.tabs.currentIndex()
                    self.parent_window.tabs.setCurrentIndex(merger_tab_index)
                    self.logger.debug("TutorialManager", f"Switched from tab {old_index} to merger tab {merger_tab_index}")
                    
                    # Force update
                    current_widget = self.parent_window.tabs.currentWidget()
                    if current_widget is not None:
                        current_widget.update()
                        
                        # Give a moment for the layout to settle
                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()
                        
                        # Check if widget is now visible
                        if widget.isVisible():
                            self.logger.debug("TutorialManager", f"pdf_list is now visible after switching to merger tab")
                            return True
                        else:
                            self.logger.debug("TutorialManager", f"pdf_list still not visible after switching to merger tab")
            
            # If all else fails, use a more permissive check
            # Widget might be considered visible if it has a valid geometry and parent
            try:
                widget_parent = widget.parent() if callable(getattr(widget, 'parent', None)) else getattr(widget, 'parent', None)
                if widget_parent is not None:
                    parent_visible = True
                    try:
                        parent_visible = widget_parent.isVisible()
                    except:
                        pass
                    
                    if parent_visible and not widget.geometry().isEmpty():
                        self.logger.debug("TutorialManager", f"Widget considered effectively visible due to parent visibility and valid geometry")
                        return True
            except Exception as e:
                self.logger.debug("TutorialManager", f"Error accessing widget parent: {e}")
                pass
            
            self.logger.debug("TutorialManager", f"Widget not effectively visible: {widget}")
            return False
            
        except Exception as e:
            self.logger.error("TutorialManager", f"Error checking widget visibility: {e}")
            import traceback
            self.logger.error("TutorialManager", f"Traceback: {traceback.format_exc()}")
            return False
            
    def _widget_is_descendant_of(self, widget, ancestor):
        """Check if widget is a descendant of ancestor"""
        self.logger.debug("TutorialManager", f"_widget_is_descendant_of: checking if {widget} is descendant of {ancestor}")
        current = widget
        depth = 0
        while current is not None and depth < 20:  # Prevent infinite loops
            self.logger.debug("TutorialManager", f"  Depth {depth}: checking {current}")
            if current == ancestor:
                self.logger.debug("TutorialManager", f"  Found ancestor at depth {depth}!")
                return True
            try:
                # Use safe parent access
                next_parent = current.parent() if callable(getattr(current, 'parent', None)) else getattr(current, 'parent', None)
                self.logger.debug("TutorialManager", f"  Parent of {current}: {next_parent}")
                current = next_parent
            except (TypeError, AttributeError) as e:
                self.logger.debug("TutorialManager", f"  Parent access failed at depth {depth}: {e}")
                current = None
            depth += 1
        
        self.logger.debug("TutorialManager", f"_widget_is_descendant_of: {widget} is NOT descendant of {ancestor}")
        return False
    
    def next_step(self):
        """Move to next tutorial step"""
        self.current_step += 1
        self.show_current_step()
    
    def skip_tutorial(self):
        """Skip the current tutorial"""
        self.complete_tutorial()
    
    def complete_tutorial(self):
        """Complete the current tutorial"""
        if self.current_tutorial:
            self.mark_tutorial_completed(self.current_tutorial)
        
        if self.overlay:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
        
        self.current_tutorial = None
        self.current_step = 0
        
        # Process next tutorial in queue
        self.logger.debug("TutorialManager", f"Tutorial completed. Queue length: {len(self.tutorial_queue)}")
        QTimer.singleShot(500, self.process_tutorial_queue)  # Small delay for cleanup
    
    def reset_tutorials(self):
        """Reset all tutorials (for testing)"""
        self.reset_tutorial_completion()

# Global tutorial manager instance
_tutorial_manager = None

def get_tutorial_manager(parent_window, settings_controller=None):
    """Get or create global tutorial manager"""
    global _tutorial_manager
    if _tutorial_manager is None:
        _tutorial_manager = TutorialManager(parent_window, settings_controller)
    return _tutorial_manager

def start_tutorial(tutorial_name, parent_window, force=False, settings_controller=None):
    """Convenience function to start a tutorial"""
    manager = get_tutorial_manager(parent_window, settings_controller)
    return manager.start_tutorial(tutorial_name, force)

def auto_start_main_tutorial(parent_window, settings_controller=None):
    """Convenience function to auto-start main tutorial"""
    manager = get_tutorial_manager(parent_window, settings_controller)
    return manager.auto_start_main_tutorial()

def reset_all_tutorials(settings_controller=None):
    """Reset all tutorials (for testing)"""
    global _tutorial_manager
    if _tutorial_manager:
        _tutorial_manager.reset_tutorials()
