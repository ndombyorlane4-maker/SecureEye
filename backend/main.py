import os, json, asyncio
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import bcrypt
import requests
from auth import create_access_token, decode_token
from influx_writer import write_event

load_dotenv()

app = FastAPI(title='Secure-Eye Backend API', version='1.0')

app.add_middleware(CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'])

# ---- GLOBAL MEMORY ----
global_devices = []
global_alerts = []
global_packets = []
global_blocked_ips = set()

# ---- PYDANTIC MODELS ----
class DeviceModel(BaseModel):
    ip: str
    mac: str = "Unknown"
    status: str = "active"
    name: str = "Unknown"

class FlowFeatures(BaseModel):
    src_ip: str
    dst_ip: str
    protocol: str
    length: int
    flags: Optional[str] = None
    timestamp: Optional[str] = None
    packet_count: Optional[int] = 0
    bytes_total: Optional[int] = 0
    avg_packet_size: Optional[float] = 0.0
    flow_duration: Optional[float] = 0.0
    packet_rate: Optional[float] = 0.0
    bytes_per_second: Optional[float] = 0.0
    syn_count: Optional[int] = 0
    ack_count: Optional[int] = 0
    rst_count: Optional[int] = 0
    fin_count: Optional[int] = 0
    flow_id: Optional[str] = None
    features: Optional[List[float]] = None
    packet_size: Optional[int] = None

class ScanDevice(BaseModel):
    ip: str
    mac: str
    manufacturer: str
    device_type: str
    status: str = "online"

# ---- CONFIGURATION ----
# URL du ML API (VM1)
ML_API_URL = os.getenv('ML_API_URL', 'http://172.20.10.6:8001')

# ---- ENDPOINTS ----
@app.get("/")
def read_root():
    return {
        "app": "Secure-Eye Backend",
        "version": "1.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ---- WEBSOCKET MANAGER ----
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        if ws not in self.active:
            self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: str):
        for ws in list(self.active):
            try:
                await ws.send_text(msg)
            except Exception:
                if ws in self.active:
                    self.active.remove(ws)

manager = ConnectionManager()

# ---- AUTH ----
#@app.post('/auth/token')
#async def login(form: OAuth2PasswordRequestForm = Depends()):
#    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
 #   admin_hash = os.getenv('ADMIN_PASSWORD_HASH')

    if not admin_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_PASSWORD_HASH not configured"
        )
    
    password_bytes = form.password.encode('utf-8')
    admin_hash_bytes = admin_hash.encode('utf-8')
    is_valid = bcrypt.checkpw(password_bytes, admin_hash_bytes)
    
    if form.username != admin_user or not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_access_token({'sub': form.username})
    return {'access_token': token, 'token_type': 'bearer'}

# ---- PREDICT ENDPOINT (Proxy vers VM1) ----
@app.post('/predict')
async def predict(flow: FlowFeatures):
    global global_alerts, global_packets
    
    try:
        # Forward les données à VM1 (ML)
        response = requests.post(
            f"{ML_API_URL}/predict",
            json=flow.dict(),
            headers={"Authorization": user},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Stocker localement
            global_packets.insert(0, result)
            global_packets = global_packets[:100]
            
            await manager.broadcast(json.dumps({'type': 'PACKET', **result}))
            
            if result.get('label') == 'ATTACK':
                global_alerts.insert(0, result)
                global_alerts = global_alerts[:50]
                await manager.broadcast(json.dumps({'type': 'ALERT', **result}))
            
            return result
        else:
            return {"error": "ML API error", "status": response.status_code}
            
    except requests.exceptions.ConnectionError:
        return {"error": "ML API unavailable"}
    except Exception as e:
        return {"error": str(e)}

# ---- SCAN RECEIVE ----
@app.post('/api/v1/scan')
async def receive_scan(devices: List[ScanDevice]):
    global global_devices
    converted_devices = []
    for device in devices:
        converted_devices.append({
            'ip': device.ip,
            'mac': device.mac,
            'name': device.manufacturer,
            'status': device.status,
            'type': device.device_type
        })
    global_devices = converted_devices
    await manager.broadcast(json.dumps({
        'type': 'SCAN_UPDATE',
        'devices': global_devices,
        'count': len(global_devices)
    }))
    return {'status': 'success', 'updated_count': len(global_devices)}

# ---- WEBSOCKET ----
@app.websocket('/ws')
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        init_payload = {
            "type": "INIT",
            "machines": list(global_devices),
            "blocked": list(global_blocked_ips),
            "alerts": list(global_alerts)
        }
        await ws.send_text(json.dumps(init_payload))
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)

# ---- DEVICE ENDPOINTS ----
@app.post('/api/report-devices')
async def report_devices(devices: List[DeviceModel]):
    global global_devices
    global_devices = [d.model_dump() for d in devices]
    return {'status': 'success', 'updated_count': len(global_devices)}

@app.get('/devices')
async def get_devices():
    global global_devices
    return {'devices': global_devices, 'total': len(global_devices)}

@app.get('/alerts')
async def get_alerts():
    global global_alerts
    return {'status': 'success', 'data': global_alerts}

@app.get('/stats')
async def get_stats():
    global global_devices, global_alerts
    active_count = len([d for d in global_devices if d['status'] == 'active'])
    offline_count = len([d for d in global_devices if d['status'] != 'active'])
    return {
        'status': 'success',
        'data': {
            'active_devices': active_count,
            'offline_devices': offline_count,
            'attacks_today': len(global_alerts),
            'total_devices': len(global_devices)
        }
    }

@app.get('/machines')
async def get_machines():
    global global_devices
    return {'status': 'success', 'data': global_devices}

@app.get('/blocked')
async def get_blocked():
    global global_blocked_ips
    return {'status': 'success', 'data': list(global_blocked_ips)}

@app.post('/block')
async def block_ip(payload: dict):
    global global_blocked_ips
    ip = payload.get('ip')
    if ip:
        global_blocked_ips.add(ip)
    return {'status': 'success', 'blocked': ip}

@app.delete('/blocked/{ip}')
async def unblock_ip(ip: str):
    global global_blocked_ips
    if ip in global_blocked_ips:
        global_blocked_ips.remove(ip)
    return {'status': 'success', 'unblocked': ip}

# ---- STARTUP ----
if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run('main:app', host='0.0.0.0', port=port, reload=False)
