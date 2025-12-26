from PIL import Image
import os

INPUT_DIR = "../media/escudos_raw"
OUTPUT_DIR = "../media/escudos"
MAX_SIZE = (256, 256)  # largura, altura

os.makedirs(OUTPUT_DIR, exist_ok=True)

def resize_with_padding(img, size=(256, 256)):
    img.thumbnail(size, Image.LANCZOS)
    background = Image.new("RGBA", size, (0, 0, 0, 0))
    offset = (
        (size[0] - img.size[0]) // 2,
        (size[1] - img.size[1]) // 2
    )
    background.paste(img, offset)
    return background

for filename in os.listdir(INPUT_DIR):
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    path_in = os.path.join(INPUT_DIR, filename)
    path_out = os.path.join(OUTPUT_DIR, filename)

    img = Image.open(path_in).convert("RGBA")

    # redimensiona mantendo proporção
    img = resize_with_padding(img, MAX_SIZE)
    img.save(path_out, format="PNG")

print("Escudos redimensionados com sucesso!")