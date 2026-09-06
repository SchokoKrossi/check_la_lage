import qrcode
from PIL import Image, ImageDraw, ImageFont

url = "https://checklaimpro.de/qr/s/"
output_path = "checklaimpro_qr.png"

# --- Generate the QR code ---
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

# --- Add a text caption under the QR code so people can see the target URL ---
caption_height = 40
canvas = Image.new("RGB", (qr_img.width, qr_img.height + caption_height), "white")
canvas.paste(qr_img, (0, 0))

draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", 20)
except OSError:
    font = ImageFont.load_default()

text_bbox = draw.textbbox((0, 0), url, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_x = (canvas.width - text_width) // 2
draw.text((text_x, qr_img.height + 8), url, fill="black", font=font)

canvas.save(output_path)
print(f"QR code saved as {output_path}")

# --- Verify the QR code actually decodes back to the expected URL ---
try:
    from pyzbar.pyzbar import decode

    decoded = decode(Image.open(output_path))
    if decoded:
        decoded_text = decoded[0].data.decode("utf-8")
        match = "OK" if decoded_text == url else "MISMATCH"
        print(f"Decoded content: {decoded_text} [{match}]")
    else:
        print("Could not decode QR code from the saved image.")
except ImportError:
    print("Install 'pyzbar' (pip install pyzbar) to auto-verify the QR code content.")
