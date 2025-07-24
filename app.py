from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import csv
import os
import shutil

app = Flask(__name__)

# File paths
LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'
HISTORY_FILE = '/tmp/device_history.csv'

# Copy original CSV to /tmp if not present
if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

# Load device list from CSV
def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

# Save updated devices to CSV
def write_devices(devices):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

# Log transfer to history file
def log_history(device, prev_data):
    fieldnames = ['DeviceID', 'Time',
                  'PreviousPS', 'PreviousPhone', 'PreviousEmail',
                  'NewPS', 'NewPhone', 'NewEmail']

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    with open(HISTORY_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow({
            'DeviceID': device['DeviceID'],
            'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'PreviousPS': prev_data['CurrentPS'],
            'PreviousPhone': prev_data['CurrentPhone'],
            'PreviousEmail': prev_data['CurrentEmail'],
            'NewPS': device['CurrentPS'],
            'NewPhone': device['CurrentPhone'],
            'NewEmail': device['CurrentEmail']
        })

# Load last 10 transfer logs
def load_history(device_id):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        return [row for row in reader if row['DeviceID'] == device_id][-10:]

@app.route('/')
def index():
    return render_template('index.html', devices=load_devices())

@app.route('/device/<device_id>', methods=['GET', 'POST'])
def device_page(device_id):
    devices = load_devices()
    device = next((d for d in devices if d['DeviceID'] == device_id), None)
    if not device:
        return render_template('device.html', device=None)

    message = None
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            # Validate required fields
            new_user = request.form.get('user', '').strip()
            new_ps = request.form.get('ps', '').strip()
            new_phone = request.form.get('phone', '').strip()
            new_email = request.form.get('email', '').strip()

            if not (new_user and new_ps.isdigit() and new_phone.isdigit() and new_email):
                message = '❌ All fields are required and must be valid (PS/Phone must be numbers).'
            else:
                prev_data = device.copy()
                device['CurrentUser'] = new_user
                device['CurrentPS'] = new_ps
                device['CurrentPhone'] = new_phone
                device['CurrentEmail'] = new_email
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                write_devices(devices)
                log_history(device, prev_data)
                message = f"✅ Updated to {new_user}"

        elif action == 'reset':
            if (device['CurrentUser'] == device['Owner'] and
                device['CurrentPS'] == device['OwnerPS'] and
                device['CurrentPhone'] == device['OwnerPhone'] and
                device['CurrentEmail'] == device['OwnerEmail']):
                message = "⚠️ Already owned by the original owner."
            else:
                prev_data = device.copy()
                device['CurrentUser'] = device['Owner']
                device['CurrentPS'] = device['OwnerPS']
                device['CurrentPhone'] = device['OwnerPhone']
                device['CurrentEmail'] = device['OwnerEmail']
                device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                write_devices(devices)
                log_history(device, prev_data)
                message = "✅ Reset to owner"

    history = load_history(device_id)
    return render_template('device.html', device=device, message=message, history=history)

if __name__ == '__main__':
    app.run(debug=True)
