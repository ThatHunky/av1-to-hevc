#!/usr/bin/env python3
"""
Simple icon generator for AV1 to HEVC Converter
Creates a basic icon without requiring external image files
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # Create a 256x256 image
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (blue to dark blue)
    for y in range(size):
        # Gradient from light blue to dark blue
        r = 0
        g = int(100 - (y / size * 50))
        b = int(255 - (y / size * 100))
        draw.rectangle([0, y, size, y+1], fill=(r, g, b, 255))
    
    # Draw a rounded rectangle border
    padding = 20
    draw.rounded_rectangle(
        [padding, padding, size-padding, size-padding],
        radius=20,
        outline=(255, 255, 255, 255),
        width=4
    )
    
    # Try to use a better font, fall back to default if not available
    try:
        # Try common Windows fonts
        for font_name in ['Arial.ttf', 'Helvetica.ttf', 'Calibri.ttf']:
            try:
                font_large = ImageFont.truetype(font_name, 60)
                font_small = ImageFont.truetype(font_name, 30)
                break
            except:
                continue
        else:
            raise Exception("No truetype fonts found")
    except:
        # Use default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw the text
    text_color = (255, 255, 255, 255)
    
    # Draw "AV1" at the top
    av1_text = "AV1"
    bbox = draw.textbbox((0, 0), av1_text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = 60
    draw.text((x, y), av1_text, fill=text_color, font=font_large)
    
    # Draw arrow in the middle
    arrow_y = size // 2
    arrow_x1 = size // 3
    arrow_x2 = 2 * size // 3
    arrow_size = 20
    
    # Draw arrow line
    draw.line([(arrow_x1, arrow_y), (arrow_x2, arrow_y)], fill=text_color, width=4)
    
    # Draw arrow head
    draw.polygon([
        (arrow_x2, arrow_y),
        (arrow_x2 - arrow_size, arrow_y - arrow_size//2),
        (arrow_x2 - arrow_size, arrow_y + arrow_size//2)
    ], fill=text_color)
    
    # Draw "HEVC" at the bottom
    hevc_text = "HEVC"
    bbox = draw.textbbox((0, 0), hevc_text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = size - 100
    draw.text((x, y), hevc_text, fill=text_color, font=font_large)
    
    # Save as ICO with multiple sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save('icon.ico', format='ICO', sizes=icon_sizes)
    
    print("✓ Created icon.ico successfully!")
    
    # Also save as PNG for reference
    img.save('icon.png', format='PNG')
    print("✓ Also saved as icon.png for reference")
    
except ImportError:
    print("✗ Pillow not installed. Please install with: pip install pillow")
    print("  Skipping icon creation.")
except Exception as e:
    print(f"✗ Error creating icon: {e}")
    print("  Continuing without icon...") 