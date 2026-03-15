# placeholder_ad.py
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_placeholder_ad(width=130, height=500):
    """Create a placeholder advertisement image"""
    # Create new image with white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Add border
    draw.rectangle([0, 0, width-1, height-1], outline='lightgray')
    
    # Try to use a system font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    # Add text
    text = "Advertisement\nSpace"
    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill='gray')
    
    return img

def setup_placeholder_ads():
    """Create the ads directory and placeholder ad"""
    ads_dir = Path(__file__).parent / 'ads'
    ads_dir.mkdir(exist_ok=True)
    
    # Create placeholder ad if it doesn't exist
    ad_path = ads_dir / 'placeholder_ad.png'
    if not ad_path.exists():
        ad = create_placeholder_ad()
        ad.save(ad_path)