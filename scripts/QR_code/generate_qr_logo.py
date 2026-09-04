import sys
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image

repo_root = Path(__file__).resolve().parents[2]

transparent = "--transparent" in sys.argv
args = [a for a in sys.argv[1:] if a != "--transparent"]

url = args[0] if len(args) > 0 else "https://checklaimpro.de/qr/"
output_path = Path(args[1]) if len(args) > 1 else Path(__file__).resolve().parent / "images" / "checklaimpro_qr.png"
logo_path = repo_root / "images" / "logo.png"

qr = qrcode.QRCode(
    version=1,
    error_correction=ERROR_CORRECT_H,  # highest error correction, needed to survive the logo overlay
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
qr_width, qr_height = qr_img.size

logo = Image.open(logo_path).convert("RGBA")

# Logo (plus its black backdrop) should cover roughly 25% of the QR code width.
patch_size = qr_width // 4
padding = patch_size // 10  # margin of black showing around the logo

logo.thumbnail((patch_size - 2 * padding, patch_size - 2 * padding), Image.LANCZOS)

backdrop = Image.new("RGBA", (patch_size, patch_size), (0, 0, 0, 255))
logo_pos = (
    (patch_size - logo.width) // 2,
    (patch_size - logo.height) // 2,
)
backdrop.paste(logo, logo_pos, logo)

patch_pos = (
    (qr_width - patch_size) // 2,
    (qr_height - patch_size) // 2,
)
qr_img.paste(backdrop, patch_pos)

if transparent:
    pixels = qr_img.load()
    for y in range(qr_height):
        for x in range(qr_width):
            r, g, b, a = pixels[x, y]
            if r > 200 and g > 200 and b > 200:
                pixels[x, y] = (255, 255, 255, 0)

qr_img.save(output_path)
print(f"QR code with logo saved as {output_path}")
