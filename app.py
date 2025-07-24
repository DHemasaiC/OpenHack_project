from flask import Flask, render_template, request
from datetime import datetime
import csv
import os
import shutil

app = Flask(__name__)

LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'
HISTORY_FILE = '/tmp/device_history.csv'

if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'Timestamp', 'DeviceID',
            'PrevPSNumber', 'PrevPhone', 'PrevEmail',
            'NewPSNumber', 'NewPhone', 'NewEmail'
        ])
        writer.writeheader()

def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_devices(devices):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

def log_history(device, new_data):
    with open(HISTORY_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'Timestamp', 'DeviceID',
            'PrevPSNumber', 'PrevPhone', 'PrevEmail',
            'NewPSNumber', 'NewPhone', 'NewEmail'
        ])
        writer.writerow({
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'DeviceID': device['DeviceID'],
            'PrevPSNumber': device['CurrentPS'],
            'PrevPhone': device['CurrentPhone'],
            'PrevEmail': device['CurrentEmail'],
            'NewPSNumber': new_data['ps'],
            'NewPhone': new_data['phone'],
            'NewEmail': new_data['email']
        })

def load_history(device_id):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return [row for row in reader if row['DeviceID'] == device_id][-10:]

@app.route('/')
def index():
    devices = load_devices()
    return render_template('index.html', devices=devices)

@app.route('/device/<device_id>', methods=['GET', 'POST'])
def device_page(device_id):
    devices = load_devices()
    device = next((d for d in devices if d['DeviceID'] == device_id.replace('%20', ' ')), None)

    if not device:
        return render_template('device.html', device=None)

    message = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update':
            # Validate required fields
            name = request.form.get('user', '').strip()
            ps = request.form.get('ps', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()

            if not name or not ps.isdigit() or not phone.isdigit() or not email:
                message = "❌ Please fill in all fields correctly."
            else:
                log_history(device, {'ps': ps, 'phone': phone, 'email': email})
                device['CurrentUser'] = name
                device['CurrentPS'] = ps
                device['CurrentPhone'] = phone
                device['CurrentEmail'] = email
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                message = f"✅ Ownership transferred to PS: {ps}"

        elif action == 'reset':
            if (device['CurrentUser'] == device['Owner'] and
                device['CurrentPS'] == device['OwnerPS'] and
                device['CurrentPhone'] == device['OwnerPhone'] and
                device['CurrentEmail'] == device['OwnerEmail']):
                message = "⚠️ Already under the owner."
            else:
                log_history(device, {
                    'ps': device['OwnerPS'],
                    'phone': device['OwnerPhone'],
                    'email': device['OwnerEmail']
                })
                device['CurrentUser'] = device['Owner']
                device['CurrentPS'] = device['OwnerPS']
                device['CurrentPhone'] = device['OwnerPhone']
                device['CurrentEmail'] = device['OwnerEmail']
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                message = f"🔁 Reset to owner {device['Owner']}"

    history = load_history(device_id.replace('%20', ' '))
    return render_template('device.html', device=device, message=message, history=history)

if __name__ == '__main__':
    app.run(debug=True)
