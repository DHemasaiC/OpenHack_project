from flask import Flask, render_template, request
from datetime import datetime
import csv
import os
import shutil

app = Flask(__name__)

LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'

# Only copy original once
if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_devices(devices):
    fieldnames = [
        'DeviceID', 'DeviceName', 'ModelName', 'EquipmentNumber',
        'Owner', 'OwnerPS', 'OwnerPhone', 'OwnerEmail',
        'CurrentUser', 'CurrentUserPS', 'CurrentUserPhone', 'CurrentUserEmail',
        'LastUpdated'
    ]
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
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
        device['CurrentUser'] = request.form['user']
        device['CurrentUserPS'] = request.form['ps']
        device['CurrentUserPhone'] = request.form['phone']
        device['CurrentUserEmail'] = request.form['email']
        device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        write_devices(devices)
        message = f"✅ Ownership transferred to {device['CurrentUser']}"

    return render_template('device.html', device=device, message=message)

if __name__ == '__main__':
    app.run(debug=True)
