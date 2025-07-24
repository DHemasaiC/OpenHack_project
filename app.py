from flask import Flask, render_template, request
from datetime import datetime
import csv
import os
import shutil

app = Flask(__name__)

# Paths
LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'
HISTORY_FILE = '/tmp/device_history.csv'

# Copy original to /tmp if not already
if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

# Load devices
def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

# Save devices
def write_devices(devices):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

# Log history
def log_device_history(device, prev_user):
    headers = [
        'Timestamp', 'DeviceID', 'DeviceName', 'ModelName', 'EquipmentNumber',
        'Previous PS', 'Previous Phone', 'Previous Email',
        'New PS', 'New Phone', 'New Email'
    ]
    row = {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'DeviceID': device['DeviceID'],
        'DeviceName': device['DeviceName'],
        'ModelName': device['ModelName'],
        'EquipmentNumber': device['EquipmentNumber'],
        'Previous PS': prev_user.get('CurrentPS', ''),
        'Previous Phone': prev_user.get('CurrentPhone', ''),
        'Previous Email': prev_user.get('CurrentEmail', ''),
        'New PS': device['CurrentPS'],
        'New Phone': device['CurrentPhone'],
        'New Email': device['CurrentEmail']
    }

    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# Load history
def load_history(device_id):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return [row for row in reader if row['DeviceID'] == device_id][-10:]

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
    history = load_history(device['DeviceID'])

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'reset':
            if (
                device['CurrentUser'] == device['Owner'] and
                device['CurrentPS'] == device['OwnerPS'] and
                device['CurrentPhone'] == device['OwnerPhone'] and
                device['CurrentEmail'] == device['OwnerEmail']
            ):
                message = "⚠️ Already reset to owner."
            else:
                prev_user = device.copy()
                device['CurrentUser'] = device['Owner']
                device['CurrentPS'] = device['OwnerPS']
                device['CurrentPhone'] = device['OwnerPhone']
                device['CurrentEmail'] = device['OwnerEmail']
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                log_device_history(device, prev_user)
                message = "✅ Reset to owner successful."

        elif action == 'transfer':
            new_user = request.form.get('user', '').strip()
            new_ps = request.form.get('ps', '').strip()
            new_phone = request.form.get('phone', '').strip()
            new_email = request.form.get('email', '').strip()

            if not new_ps:
                message = "⚠️ PS Number is required to transfer ownership."
            else:
                prev_user = device.copy()
                device['CurrentUser'] = new_user or device['CurrentUser']
                device['CurrentPS'] = new_ps
                device['CurrentPhone'] = new_phone
                device['CurrentEmail'] = new_email
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                log_device_history(device, prev_user)
                message = f"✅ Ownership transferred to PS: {new_ps}"

        # Refresh history after update
        history = load_history(device['DeviceID'])

    return render_template('device.html', device=device, message=message, history=history)

if __name__ == '__main__':
    app.run(debug=True)
