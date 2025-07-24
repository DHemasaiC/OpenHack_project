from flask import Flask, render_template, request
from datetime import datetime
import csv, os, shutil

app = Flask(__name__)
LOCAL_CSV = 'devices.csv'
CSV_FILE = '/tmp/devices.csv'
HISTORY_FILE = '/tmp/device_history.csv'

if not os.path.exists(CSV_FILE):
    shutil.copyfile(LOCAL_CSV, CSV_FILE)

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'DeviceID',
                         'PrevUser', 'PrevPS', 'PrevPhone', 'PrevEmail',
                         'NewUser', 'NewPS', 'NewPhone', 'NewEmail'])

def load_devices():
    with open(CSV_FILE, mode='r', newline='') as file:
        return list(csv.DictReader(file))

def write_devices(devices):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=devices[0].keys())
        writer.writeheader()
        writer.writerows(devices)

def log_history(device, prev_user, new_user):
    with open(HISTORY_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            device['DeviceID'],
            prev_user['name'], prev_user['ps'], prev_user['phone'], prev_user['email'],
            new_user['name'], new_user['ps'], new_user['phone'], new_user['email']
        ])

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
    history = []

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            prev = {
                'name': device['CurrentUser'],
                'ps': device['CurrentUserPS'],
                'phone': device['CurrentUserPhone'],
                'email': device['CurrentUserEmail']
            }

            device['CurrentUser'] = request.form['user']
            device['CurrentUserPS'] = request.form['ps']
            device['CurrentUserPhone'] = request.form['phone']
            device['CurrentUserEmail'] = request.form['email']
            device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            new = {
                'name': device['CurrentUser'],
                'ps': device['CurrentUserPS'],
                'phone': device['CurrentUserPhone'],
                'email': device['CurrentUserEmail']
            }

            log_history(device, prev, new)
            write_devices(devices)
            message = f"✅ Transferred to {device['CurrentUser']}"

        elif action == 'reset':
            prev = {
                'name': device['CurrentUser'],
                'ps': device['CurrentUserPS'],
                'phone': device['CurrentUserPhone'],
                'email': device['CurrentUserEmail']
            }

            device['CurrentUser'] = device['Owner']
            device['CurrentUserPS'] = device['OwnerPS']
            device['CurrentUserPhone'] = device['OwnerPhone']
            device['CurrentUserEmail'] = device['OwnerEmail']
            device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            new = {
                'name': device['CurrentUser'],
                'ps': device['CurrentUserPS'],
                'phone': device['CurrentUserPhone'],
                'email': device['CurrentUserEmail']
            }

            log_history(device, prev, new)
            write_devices(devices)
            message = f"🔄 Reset to original owner: {device['Owner']}"

        elif action == 'history':
            history = load_history(device['DeviceID'])

    return render_template('device.html', device=device, message=message, history=history)

if __name__ == '__main__':
    app.run(debug=True)
