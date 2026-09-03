import qrcode

url = "https://checklaimpro.de/qr/"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("checklaimpro_qr.png")

print("QR code saved as checklaimpro_qr.png")
