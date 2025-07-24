from flask import Flask, render_template, request, redirect
import csv
from datetime import datetime

app = Flask(__name__)
CSV_FILE = 'devices.csv'

def read_devices():
    with open(CSV_FILE, newline='') as f:
        return list(csv.DictReader(f))

def write_devices(data):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/device')
def device_redirect():
    device_id = request.args.get('device_id')
    return redirect(f"/device/{device_id}")

@app.route('/device/<device_id>', methods=['GET', 'POST'])
def device(device_id):
    devices = read_devices()
    device = next((d for d in devices if d['DeviceID'] == device_id), None)

    if not device:
        return "Device not found", 404

    message = None

    if request.method == 'POST':
        device['CurrentUser'] = request.form['user']
        device['PSNumber'] = request.form['ps']
        device['Phone'] = request.form['phone']
        device['Email'] = request.form['email']
        device['LastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        write_devices(devices)
        message = f"✅ Device ownership transferred to {device['CurrentUser']}."

    return render_template('device.html', device=device, message=message)
