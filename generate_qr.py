import qrcode

base_url = "http://localhost:5000/device/"

for i in range(1001, 1006):
    img = qrcode.make(f"{base_url}{i}")
    img.save(f"qr_{i}.png")
