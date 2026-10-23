"""
Generate PWA icons from existing image
Requires: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes needed for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Colors
BACKGROUND_COLOR = (102, 126, 234)  # #667eea
TEXT_COLOR = (255, 255, 255)

def create_icon(size, output_path):
    """Create a simple icon with text"""
    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Add a circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(118, 75, 162), outline=TEXT_COLOR, width=max(2, size//50))
    
    # Add text
    text = "ST"
    try:
        # Try to use a nice font
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Get text size and center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Draw text with shadow for better visibility
    shadow_offset = max(1, size // 100)
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)
    
    # Save image
    img.save(output_path, 'PNG', optimize=True)
    print(f"✓ Created {output_path} ({size}x{size})")

def main():
    print("\n" + "="*60)
    print(" 🎨 PWA ICON GENERATOR ".center(60))
    print("="*60 + "\n")
    
    # Create images directory if it doesn't exist
    images_dir = os.path.join('static', 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # Use the Stock Tracker artwork rather than the old solid-color placeholder.
    existing_icon = os.path.join(images_dir, 'icon-512x512.png')
    
    if os.path.exists(existing_icon):
        print(f"📷 Found existing icon: {existing_icon}")
        try:
            base_img = Image.open(existing_icon)
            print(f"   Size: {base_img.size}")
            
            # Generate all sizes from existing image
            for size in ICON_SIZES:
                output_path = os.path.join(images_dir, f'icon-{size}x{size}.png')
                resized = base_img.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(output_path, 'PNG', optimize=True)
                print(f"✓ Created {output_path} ({size}x{size})")
            
            print("\n✅ All icons generated from existing image!")
            
        except Exception as e:
            print(f"⚠ Error using existing image: {e}")
            print("   Generating new icons instead...\n")
            generate_new_icons(images_dir)
    else:
        print("📷 No existing icon found, generating new icons...\n")
        generate_new_icons(images_dir)
    
    print("\n" + "="*60)
    print(" ✅ PWA ICONS GENERATION COMPLETE ".center(60))
    print("="*60)
    print(f"\n📁 Icons saved to: {images_dir}")
    print(f"📊 Generated {len(ICON_SIZES)} icon sizes")
    print("\n💡 Next steps:")
    print("   1. Run: python manage.py collectstatic --noinput")
    print("   2. Test PWA on mobile device")
    print("   3. Check manifest.json is accessible")
    print("\n")

def generate_new_icons(images_dir):
    """Generate new icons from scratch"""
    for size in ICON_SIZES:
        output_path = os.path.join(images_dir, f'icon-{size}x{size}.png')
        create_icon(size, output_path)
    
    print("\n✅ All icons generated!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Generation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure Pillow is installed: pip install Pillow")
