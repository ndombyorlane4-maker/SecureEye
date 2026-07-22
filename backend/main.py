import os, json, requests
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient

load_dotenv()

app = FastAPI(title='Secure-Eye Backend API', version='1.0')

app.add_middleware(CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'])

# ---- CONFIGURATION ----
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', '')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'secureeye')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'network_metrics')
ML_API_URL = os.getenv('ML_API_URL', 'http://172.20.10.6:8001')

# ---- INFLUXDB CLIENT ----
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = influx_client.query_api()

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

# ---- WEBSOCKET MANAGER ----
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: str):
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except:
                pass

manager = ConnectionManager()

# ---- HELPER FUNCTIONS ----
def get_devices_from_influx():
    flux = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_flow")
      |> filter(fn: (r) => exists r.src)
      |> group(columns: ["src"])
      |> count()
    '''
    try:
        result = query_api.query(flux)
        devices = []
        seen = set()
        for table in result:
            for record in table.records:
                ip = str(record.values.get('src', ''))
                if ip and ip not in seen:
                    seen.add(ip)
                    devices.append({
                        'ip': ip,
                        'mac': 'Unknown',
                        'status': 'active',
                        'name': 'Device'
                    })
        return devices
    except Exception as e:
        print(f"❌ Error reading devices: {e}")
        return []
def get_alerts_from_influx():
    flux = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "network_flow")
      |> filter(fn: (r) => r.label == "ATTACK")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 50)
    '''
    try:
        result = query_api.query(flux)
        alerts = []
        for table in result:
            for record in table.records:
                alerts.append({
                    'src': record.values.get('src', 'unknown'),
                    'dst': record.values.get('dst', 'unknown'),
                    'label': record.values.get('label', 'ATTACK'),
                    'confidence': record.get_value(),
                    'time': record.get_time().isoformat() if record.get_time() else ''
                })
        return alerts
    except Exception as e:
        print(f"❌ Error reading alerts: {e}")
        return []

def get_stats_from_influx():
    devices = get_devices_from_influx()
    alerts = get_alerts_from_influx()
    return {
        'active_devices': len(devices),
        'offline_devices': 0,
        'attacks_today': len(alerts),
        'total_devices': len(devices)
    }

# ---- PREDICT ENDPOINT ----
@app.post('/predict')
async def predict(flow: FlowFeatures):
    try:
        response = requests.post(f"{ML_API_URL}/predict", json=flow.dict(), timeout=5)
        if response.status_code == 200:
            result = response.json()
            await manager.broadcast(json.dumps({'type': 'PACKET', **result}))
            if result.get('label') == 'ATTACK':
                await manager.broadcast(json.dumps({'type': 'ALERT', **result}))
            return result
        return {"error": "ML API error", "status": response.status_code}
    except Exception as e:
        return {"error": str(e)}

# ---- SCAN RECEIVE ----
@app.post('/api/v1/scan')
async def receive_scan(devices: List[ScanDevice]):
    await manager.broadcast(json.dumps({'type': 'SCAN_UPDATE', 'devices': [d.dict() for d in devices], 'count': len(devices)}))
    return {'status': 'success', 'updated_count': len(devices)}

# ---- WEBSOCKET ----
@app.websocket('/ws')
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ---- MAIN ENDPOINTS ----
@app.get("/")
def read_root():
    return {"app": "Secure-Eye Backend", "version": "1.0", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get('/devices')
async def get_devices():
    devices = get_devices_from_influx()
    return {'devices': devices, 'total': len(devices)}

@app.get('/alerts')
async def get_alerts():
    alerts = get_alerts_from_influx()
    return {'status': 'success', 'data': alerts}

@app.get('/stats')
async def get_stats():
    stats = get_stats_from_influx()
    return {'status': 'success', 'data': stats}

@app.get('/machines')
async def get_machines():
    devices = get_devices_from_influx()
    return {'status': 'success', 'data': devices}

@app.get('/blocked')
async def get_blocked():
    return {'status': 'success', 'data': []}

@app.post('/block')
async def block_ip(payload: dict):
    return {'status': 'success', 'blocked': payload.get('ip')}

@app.delete('/blocked/{ip}')
async def unblock_ip(ip: str):
    return {'status': 'success', 'unblocked': ip}

# ---- STARTUP ----
if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run('main:app', host='0.0.0.0', port=port, reload=False)
