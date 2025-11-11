#!/usr/bin/env python3
"""
Simple script to generate PWA icons using PIL
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
os.makedirs('src/assets/icons', exist_ok=True)

# Sizes for PWA icons
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for size in sizes:
    # Create a new image with a gradient background
    img = Image.new('RGB', (size, size), color='#3f51b5')
    draw = ImageDraw.Draw(img)

    # Draw a shield shape (simple version)
    # Background circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#5c6bc0', outline='#ffffff', width=max(2, size//64))

    # Draw "TD" text in center
    try:
        # Try to use a font
        font_size = size // 3
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()

    text = "TD"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]

    # Draw text with shadow
    draw.text((x+2, y+2), text, fill='#000000', font=font)  # shadow
    draw.text((x, y), text, fill='#ffffff', font=font)  # main text

    # Save
    filename = f'src/assets/icons/icon-{size}x{size}.png'
    img.save(filename, 'PNG')
    print(f'Created {filename}')

print(f'\nAll {len(sizes)} icons created successfully!')
