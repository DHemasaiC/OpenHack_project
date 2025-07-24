from flask import Flask, render_template, request
from datetime import datetime
import csv
import os
import shutil

app = Flask(__name__)

# 🔁 Use /tmp path for write access on Render
LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'

# 🧠 Copy original CSV to /tmp only if it doesn’t exist
if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

# 🔄 Load devices into memory
def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

# 💾 Save updated devices
def write_devices(devices):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/device/<device_id>', methods=['GET', 'POST'])
def device_page(device_id):
    devices = load_devices()
    device = next((d for d in devices if d['DeviceID'] == device_id.replace('%20', ' ')), None)

    if not device:
        return render_template('device.html', device=None)

    message = None
    if request.method == 'POST':
        device['Current User'] = request.form['user']
        device['PS Number'] = request.form['ps']
        device['Phone'] = request.form['phone']
        device['Email'] = request.form['email']
        device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        write_devices(devices)
        message = f"✅ Ownership transferred to {device['Current User']}"

    return render_template('device.html', device=device, message=message)

if __name__ == '__main__':
    app.run(debug=True)
