#!/usr/bin/env python3
"""
Icon Creator for Rent Tracker Application

This script helps create an icon file for the Rent Tracker application.
It can convert PNG/JPEG images to ICO format or create a simple default icon.
"""

import os
import sys

def create_simple_icon():
    """Create a simple text-based icon description"""
    icon_info = """
🏠 RENT TRACKER ICON GUIDE 🏠

To add a custom icon to your Rent Tracker application:

1. CREATE OR FIND AN IMAGE:
   - Size: 32x32, 48x48, or 64x64 pixels (square)
   - Format: PNG, JPEG, or BMP
   - Theme suggestions:
     * House/apartment building
     * Dollar sign with house
     * Calendar with money symbol
     * Key icon
     * Rent/property management symbol

2. CONVERT TO ICO FORMAT:

   Option A - Online Converters:
   - Visit: favicon.io, convertio.co, or ico-converter.com
   - Upload your image
   - Download as .ico file
   - Rename to "rent_tracker.ico"

   Option B - Using GIMP (Free):
   - Open your image in GIMP
   - File → Export As
   - Change extension to .ico
   - Choose appropriate sizes (32x32 recommended)

   Option C - Using ImageMagick (Command Line):
   - Install ImageMagick
   - Run: magick convert your_image.png -resize 32x32 rent_tracker.ico

   Option D - Using Python PIL (if available):
   - Run this script with: python create_icon.py --generate

3. SAVE THE ICON:
   - Place the .ico file in the same folder as Rent_Tracker.py
   - Name it "rent_tracker.ico" or "icon.ico"
   - The application will automatically detect and use it

4. FOR PYINSTALLER:
   Add to your build command:
   pyinstaller --icon=rent_tracker.ico --name "Rent Tracker" Rent_Tracker.py

CURRENT STATUS: No icon file found. Using emoji fallback in title bar.
"""
    print(icon_info)

def try_create_pil_icon():
    """Try to create a simple icon using PIL if available"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a 32x32 image
        size = (32, 32)
        image = Image.new('RGBA', size, (0, 0, 0, 0))  # Transparent background
        draw = ImageDraw.Draw(image)
        
        # Draw a simple house shape
        # House base (rectangle)
        draw.rectangle([6, 16, 26, 30], fill='brown', outline='black')
        
        # Roof (triangle)
        draw.polygon([(16, 6), (4, 16), (28, 16)], fill='red', outline='black')
        
        # Door
        draw.rectangle([12, 20, 18, 30], fill='darkbrown', outline='black')
        
        # Windows
        draw.rectangle([8, 18, 12, 22], fill='lightblue', outline='black')
        draw.rectangle([20, 18, 24, 22], fill='lightblue', outline='black')
        
        # Save as ICO
        icon_path = 'rent_tracker.ico'
        image.save(icon_path, format='ICO', sizes=[(32, 32)])
        
        print(f"✅ Created simple house icon: {icon_path}")
        print("The Rent Tracker application will now use this icon!")
        return True
        
    except ImportError:
        print("❌ PIL (Pillow) not available. Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ Error creating icon: {e}")
        return False

def main():
    """Main function"""
    print("🏠 Rent Tracker Icon Creator 🏠\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--generate':
        print("Attempting to generate a simple icon...")
        if try_create_pil_icon():
            return
    
    # Check for existing icons
    icon_files = ['rent_tracker.ico', 'icon.ico']
    found_icons = [f for f in icon_files if os.path.exists(f)]
    
    if found_icons:
        print(f"✅ Found existing icon files: {', '.join(found_icons)}")
        print("The Rent Tracker application should use these automatically.")
    else:
        print("ℹ️  No icon files found.")
        create_simple_icon()
        
        # Ask if user wants to try generating one
        try:
            response = input("\nWould you like to try generating a simple icon? (y/n): ").lower()
            if response in ['y', 'yes']:
                try_create_pil_icon()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")

if __name__ == '__main__':
    main()
