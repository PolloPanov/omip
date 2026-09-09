from PIL import Image, ImageDraw

img = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
d = ImageDraw.Draw(img)

d.rounded_rectangle((8, 8, 248, 248), radius=48, fill=(25, 70, 120, 255))
d.line((35, 185, 80, 135, 120, 155, 165, 90, 220, 55), fill=(255, 255, 255, 255), width=14)
d.polygon([(220, 55), (220, 92), (183, 70)], fill=(255, 255, 255, 255))

img.save(
    "omip.ico",
    sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
)

print("Icono OMIP creado: omip.ico")
