from PIL import Image, ImageDraw

size = 256
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Blue gradient circle
for y in range(size):
    for x in range(size):
        dx, dy = x - size//2, y - size//2
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < size//2 - 5:
            r = int(30 + 50 * (1 - dist/(size//2)))
            g = int(100 + 80 * (1 - dist/(size//2)))
            b = int(220 + 35 * (1 - dist/(size//2)))
            img.putpixel((x, y), (r, g, b, 255))

# White circle border
draw.ellipse([5, 5, size-5, size-5], outline=(255,255,255,80), width=3)

# Checkmark
cx, cy = size//2, size//2
check = [(cx-40, cy-5), (cx-12, cy+25), (cx+45, cy-22)]
draw.line([check[0], check[1]], fill=(50, 200, 50, 255), width=10)
draw.line([check[1], check[2]], fill=(50, 200, 50, 255), width=10)

# Bell
bell_cx, bell_cy = cx + 55, cy - 45
draw.polygon([
    (bell_cx-20, bell_cy-25),
    (bell_cx+20, bell_cy-25),
    (bell_cx+23, bell_cy+15),
    (bell_cx+15, bell_cy+20),
    (bell_cx-15, bell_cy+20),
    (bell_cx-23, bell_cy+15),
], fill=(255, 255, 255, 200))
draw.ellipse([bell_cx-14, bell_cy+16, bell_cx+14, bell_cy+32], fill=(255, 255, 255, 200))
draw.ellipse([bell_cx-6, bell_cy-35, bell_cx+6, bell_cy-23], fill=(255, 255, 255, 200))

# Save
output_dir = "/mnt/c/Users/sribn/Desktop/daily_reminder"
img.save(f"{output_dir}/app_icon.png")
print("PNG saved")

# Create ICO
img_256 = img.resize((256, 256), Image.LANCZOS)
img_128 = img.resize((128, 128), Image.LANCZOS)
img_64 = img.resize((64, 64), Image.LANCZOS)
img_32 = img.resize((32, 32), Image.LANCZOS)
img_16 = img.resize((16, 16), Image.LANCZOS)
img_256.save(f"{output_dir}/app_icon.ico", format="ICO", sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
print("ICO saved!")
