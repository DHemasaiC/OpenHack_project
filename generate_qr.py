import qrcode

base_url = "https://openhack-project.onrender.com/device/"

device_ids = [
    "93 13 5D 14",
    "A2 B4 C3 D1",
    "78 45 90 AB",
    "62 93 3C 47",
    "52 92 5A 29"
]

for device_id in device_ids:
    encoded_id = device_id.replace(" ", "%20")  # URL encode spaces
    full_url = base_url + encoded_id
    print(f"Generating QR for: {full_url}")
    img = qrcode.make(full_url)
    img.save(f"qr_{device_id.replace(' ', '_')}.png")

print("✅ All QR codes generated successfully.")
