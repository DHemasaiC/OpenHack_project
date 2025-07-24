from flask import Flask, render_template, request
from datetime import datetime, timedelta
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
    with open(HISTORY_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'DeviceID', 'Timestamp', 'OldUser', 'OldPS', 'NewUser', 'NewPS'
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

def log_history(device, new):
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    with open(HISTORY_FILE, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'DeviceID', 'Timestamp', 'OldUser', 'OldPS', 'NewUser', 'NewPS'
        ])
        writer.writerow({
            'DeviceID': device['DeviceID'],
            'Timestamp': ist_time.strftime('%Y-%m-%d %H:%M:%S'),
            'OldUser': device['CurrentUser'],
            'OldPS': device['CurrentPS'],
            'NewUser': new['user'],
            'NewPS': new['ps']
        })

def load_history(device_id):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r', newline='') as file:
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
    history = load_history(device_id)

    if request.method == 'POST':
        if 'reset' in request.form:
            if device['CurrentUser'] == device['Owner'] and device['CurrentPS'] == device['OwnerPS']:
                message = "Already under the owner."
            else:
                log_history(device, {
                    'user': device['Owner'],
                    'ps': device['OwnerPS']
                })
                device['CurrentUser'] = device['Owner']
                device['CurrentPS'] = device['OwnerPS']
                device['CurrentPhone'] = device['OwnerPhone']
                device['CurrentEmail'] = device['OwnerEmail']
                ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
                device['LastUpdated'] = ist_time.strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                message = "Reverted to owner."
        else:
            user = request.form['user'].strip()
            ps = request.form['ps'].strip()
            phone = request.form['phone'].strip()
            email = request.form['email'].strip()

            if not (user and ps.isdigit() and phone.isdigit() and email):
                message = "All fields are required with valid formats."
            else:
                log_history(device, {'user': user, 'ps': ps})
                device['CurrentUser'] = user
                device['CurrentPS'] = ps
                device['CurrentPhone'] = phone
                device['CurrentEmail'] = email
                ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
                device['LastUpdated'] = ist_time.strftime('%Y-%m-%d %H:%M:%S')
                write_devices(devices)
                message = f"✅ Ownership transferred to {user}"

    return render_template('device.html', device=device, message=message, history=history)

if __name__ == '__main__':
    app.run(debug=True)
