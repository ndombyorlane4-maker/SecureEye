import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', '')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'secureeye')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'network_metrics')  # Updated

def write_event(result: dict):
    """Write event to InfluxDB"""
    try:
        # If no token, skip (for Render deployment)
        if not INFLUXDB_TOKEN:
            print("⚠️ InfluxDB token missing - write disabled")
            return
        
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        # Create the data point
        point = Point('network_flow') \
            .tag('label', result.get('label', 'NORMAL')) \
            .tag('protocol', result.get('protocol', 'TCP')) \
            .tag('src', result.get('src', '?')) \
            .tag('dst', result.get('dst', '?')) \
            .field('confidence', result.get('confidence', 0.0)) \
            .field('size', result.get('size', 0)) \
            .time(datetime.utcnow(), WritePrecision.NS)
        
        # Write to InfluxDB
        write_api.write(
            bucket=INFLUXDB_BUCKET,
            org=INFLUXDB_ORG,
            record=point
        )
        client.close()
        print(f"✅ InfluxDB: {result.get('src')} -> {result.get('label')}")
        return True
        
    except Exception as e:
        print(f"❌ InfluxDB write error: {e}")
        return False

def write_alert(alert: dict):
    """Write an alert to InfluxDB"""
    try:
        if not INFLUXDB_TOKEN:
            print("⚠️ InfluxDB token missing - alert write disabled")
            return
        
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        point = Point('alert') \
            .tag('src', alert.get('src', '?')) \
            .tag('dst', alert.get('dst', '?')) \
            .tag('label', alert.get('label', 'ATTACK')) \
            .tag('protocol', alert.get('protocol', 'TCP')) \
            .field('confidence', alert.get('confidence', 0.0)) \
            .field('size', alert.get('size', 0)) \
            .time(datetime.utcnow(), WritePrecision.NS)
        
        write_api.write(
            bucket=INFLUXDB_BUCKET,
            org=INFLUXDB_ORG,
            record=point
        )
        client.close()
        print(f"🚨 Alert written to InfluxDB: {alert.get('src')} -> {alert.get('label')}")
        return True
        
    except Exception as e:
        print(f"❌ Alert write error: {e}")
        return False
