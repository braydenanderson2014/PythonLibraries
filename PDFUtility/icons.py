#!/usr/bin/env python3
# icons.py - Custom icon generation for the PDF Utility application

import math
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import QSize, Qt

def create_gear_icon(size=32, color=QColor(220, 220, 220)):
    """Create a gear icon for settings"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Set up pen and brush
    pen = QPen(color.darker(120))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.setBrush(QBrush(color))
    
    # Calculate dimensions
    outer_radius = size * 0.4
    inner_radius = size * 0.25
    center_x = size / 2
    center_y = size / 2
    num_teeth = 8
    
    # Draw the base circle
    painter.drawEllipse(int(center_x - inner_radius), int(center_y - inner_radius),
                       int(inner_radius * 2), int(inner_radius * 2))
    
    # Draw teeth
    tooth_width = size * 0.1
    
    for i in range(num_teeth):
        angle = i * (360.0 / num_teeth)
        rad = angle * 3.14159 / 180.0
        
        # Use sin and cos directly for tooth positions
        x = center_x + outer_radius * math.cos(rad)
        y = center_y + outer_radius * math.sin(rad)
        
        # Draw tooth as rectangle
        painter.drawRect(int(x - tooth_width/2), int(y - tooth_width/2), 
                        int(tooth_width), int(tooth_width))
    
    # Draw center hole
    center_hole = size * 0.08
    painter.setBrush(Qt.GlobalColor.transparent)
    painter.drawEllipse(int(center_x - center_hole), int(center_y - center_hole),
                       int(center_hole * 2), int(center_hole * 2))
    
    painter.end()
    return QIcon(pixmap)

def create_icons():
    """Create all custom icons used in the application"""
    icons = {}
    icons['settings'] = create_gear_icon()
    return icons
