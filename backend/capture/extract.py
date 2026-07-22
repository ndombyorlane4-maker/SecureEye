#!/usr/bin/env python3
# extract.py - SECURE-EYE-XX (Version enrichie)

import os
import sys
import json
import socket
import threading
import time
import requests
import subprocess
from datetime import datetime
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

UDP_PORT = 9999
TCP_PORT = 9998
BUFFER_SIZE = 65535
BATCH_SIZE = 50

# URLs
BACKEND_URL = "http://localhost:8000/api/v1/packets"
ML_API_URL = "http://localhost:8001/api/v1/predict"

# Cache
CACHE_FILE = "/tmp/vm_ips.txt"
CACHE_TTL = 60

# Buffer
packet_buffer = []
buffer_lock = threading.Lock()

# Cache pour VM1
vm1_ip_cache = None
vm1_cache_time = 0

# ============================================
# Dictionnaire pour stocker les flux
# ============================================
flows = {}
FLOW_TIMEOUT = 5  # secondes
FLOW_MIN_PACKETS = 10  # nombre minimum de paquets pour prédire
# ============================================

# ============================================================================
# LOGGING
# ============================================================================

def log_message(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def ping_port(ip, port, timeout=0.3):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def discover_vm1():
    """Trouve VM1 en moins d'1 seconde"""
    global vm1_ip_cache, vm1_cache_time

    if vm1_ip_cache and (time.time() - vm1_cache_time) < 300:
        if ping_port(vm1_ip_cache, 8001):
            return vm1_ip_cache

    try:
        result = subprocess.run(
            ["arp", "-n"],
            capture_output=True, text=True, timeout=1
        )
        ips = []
        for line in result.stdout.split('\n'):
            if '.' in line and 'ether' in line:
                parts = line.split()
                if len(parts) >= 3:
                    ips.append(parts[0])

        for ip in ips:
            if ip in ["172.20.10.4", "172.20.10.5"]:
                continue
            if ping_port(ip, 8001):
                vm1_ip_cache = ip
                vm1_cache_time = time.time()
                log_message(f"✅ VM1 found via ARP: {ip}")
                return ip
    except:
        pass

    gateway = os.popen("ip route | grep default | awk '{print $3}'").read().strip()
    if gateway:
        base = ".".join(gateway.split('.')[:-1])
        for i in [6, 2, 3, 10, 20, 5, 7, 8, 9]:
            ip = f"{base}.{i}"
            if ip in ["172.20.10.4", "172.20.10.5"]:
                continue
            if ping_port(ip, 8001):
                vm1_ip_cache = ip
                vm1_cache_time = time.time()
                log_message(f"✅ VM1 found: {ip}")
                return ip

    if vm1_ip_cache:
        return vm1_ip_cache

    log_message("⚠️ VM1 not found, using 172.20.10.6")
    return "172.20.10.6"

# ============================================================================
# SERVEUR UDP
# ============================================================================

def udp_server():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', UDP_PORT))
        sock.settimeout(1.0)

        log_message(f"📡 UDP Server listening on port {UDP_PORT}")

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                packet_data = data.decode('utf-8')

                with buffer_lock:
                    packet_buffer.append(packet_data)
                    if len(packet_buffer) >= BATCH_SIZE:
                        threading.Thread(target=process_batch).start()

                log_message(f"📨 Received packet from {addr[0]}")

            except socket.timeout:
                with buffer_lock:
                    if packet_buffer:
                        threading.Thread(target=process_batch).start()
                continue
            except Exception as e:
                log_message(f"❌ UDP error: {e}", "ERROR")

    except Exception as e:
        log_message(f"❌ UDP server error: {e}", "ERROR")
    finally:
        sock.close()

# ============================================================================
# SERVEUR TCP
# ============================================================================

def tcp_server():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', TCP_PORT))
        sock.listen(10)

        log_message(f"📡 TCP Server listening on port {TCP_PORT}")

        while True:
            try:
                client_sock, addr = sock.accept()
                threading.Thread(
                    target=handle_tcp_client,
                    args=(client_sock, addr)
                ).start()
            except Exception as e:
                log_message(f"❌ TCP accept error: {e}", "ERROR")

    except Exception as e:
        log_message(f"❌ TCP server error: {e}", "ERROR")
    finally:
        sock.close()

def handle_tcp_client(client_sock, addr):
    try:
        client_sock.settimeout(30)
        data = b''
        while True:
            chunk = client_sock.recv(8192)
            if not chunk:
                break
            data += chunk

        if data:
            log_message(f"📨 Received TCP scan from {addr[0]}")
            process_scan_data(data.decode('utf-8'))

    except Exception as e:
        log_message(f"❌ TCP client error: {e}", "ERROR")
    finally:
        client_sock.close()

# ============================================================================
# TRAITEMENT DES DONNÉES
# ============================================================================

PROTOCOL_MAP = {
    '6': 'TCP',
    '17': 'UDP',
    '1': 'ICMP',
    '2': 'IGMP',
    '89': 'OSPF',
    '88': 'EIGRP',
    '47': 'GRE',
    '50': 'ESP',
    '51': 'AH',
    '8': 'EGP',
    '9': 'IGP',
    '46': 'RSVP',
    '4': 'IPIP'
}

def get_protocol_name(proto_code):
    return PROTOCOL_MAP.get(str(proto_code), f"UNKNOWN({proto_code})")

def process_scan_data(data):
    log_message(f"📊 Processing scan data: {len(data)} bytes")

# ============================================================================
# PROCESSUS PRINCIPAL - VERSION ENRICHIE
# ============================================================================

def process_packet(packet_data):
    global flows
    
    try:
        parts = packet_data.strip().split('|')
        if len(parts) < 6:
            return

        packet = {
            'timestamp': parts[0],
            'src_ip': parts[1],
            'dst_ip': parts[2],
            'protocol': parts[3],
            'length': int(parts[4]) if parts[4] else 0,
            'flags': parts[5] if len(parts) > 5 else '',
            'received_at': datetime.now().isoformat()
        }

        flow_key = f"{packet['src_ip']}_{packet['dst_ip']}_{packet['protocol']}"
        
        if flow_key not in flows:
            flows[flow_key] = {
                'packets': [],
                'start_time': float(packet['timestamp']),
                'last_time': float(packet['timestamp']),
                'bytes_total': 0,
                'packet_count': 0,
                'flags': []
            }
        
        flow = flows[flow_key]
        flow['packets'].append(packet)
        flow['bytes_total'] += packet['length']
        flow['packet_count'] += 1
        flow['last_time'] = float(packet['timestamp'])
        flow['flags'].append(packet['flags'])
        
        duration = flow['last_time'] - flow['start_time']
        
        if flow['packet_count'] >= FLOW_MIN_PACKETS or duration >= FLOW_TIMEOUT:
            predict_flow(flow)
            del flows[flow_key]
            
    except Exception as e:
        log_message(f"❌ Packet processing error: {e}", "ERROR")

def predict_flow(flow):
    """Prédit si un flux est malveillant - Version enrichie"""
    try:
        packets = flow['packets']
        if not packets:
            return

        # ============================================
        # 1. STATISTIQUES COMPLÈTES DU FLUX
        # ============================================
        total_packets = len(packets)
        bytes_total = flow['bytes_total']
        lengths = [p['length'] for p in packets]
        
        # Statistiques de base
        avg_size = sum(lengths) / total_packets if total_packets > 0 else 0
        max_size = max(lengths) if lengths else 0
        min_size = min(lengths) if lengths else 0
        std_size = (sum((x - avg_size) ** 2 for x in lengths) / total_packets) ** 0.5 if total_packets > 1 else 0
        
        duration = flow['last_time'] - flow['start_time']
        if duration <= 0:
            duration = 0.001
        
        packet_rate = total_packets / duration
        bytes_per_second = bytes_total / duration
        
        # Flags
        flags_list = flow['flags']
        syn_count = sum(1 for f in flags_list if 'SYN' in f)
        ack_count = sum(1 for f in flags_list if 'ACK' in f)
        rst_count = sum(1 for f in flags_list if 'RST' in f)
        fin_count = sum(1 for f in flags_list if 'FIN' in f)
        
        # ============================================
        # 2. FEATURES AVANCÉES POUR PLUS DE PRÉCISION
        # ============================================
        # Timing (IAT)
        timestamps = [float(p['timestamp']) for p in packets]
        if len(timestamps) > 1:
            iats = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            iat_mean = sum(iats) / len(iats)
            iat_max = max(iats)
            iat_min = min(iats)
            iat_std = (sum((x - iat_mean) ** 2 for x in iats) / len(iats)) ** 0.5 if len(iats) > 1 else 0
        else:
            iat_mean = iat_max = iat_min = iat_std = 0
        
        # Ratio de taille
        size_ratio = avg_size / (max_size + 1) if max_size > 0 else 0
        
        # Diversité des flags
        unique_flags = len(set(flags_list))
        flag_diversity = unique_flags / (len(flags_list) + 1)
        
        # ============================================
        # 3. CONSTRUIRE LES 41 FEATURES (NSL-KDD ENRICHIES)
        # ============================================
        first_packet = packets[0]
        protocol_name = get_protocol_name(first_packet['protocol'])
        
        feature_vector = [
            duration,                          # 1: duration (durée du flux)
            0,                                 # 2: protocol_type
            0,                                 # 3: service
            0,                                 # 4: flag
            bytes_total,                       # 5: src_bytes (total des octets)
            0,                                 # 6: dst_bytes
            0,                                 # 7: land
            0,                                 # 8: wrong_fragment
            0,                                 # 9: urgent
            0,                                 # 10: hot
            0,                                 # 11: num_failed_logins
            0,                                 # 12: logged_in
            0,                                 # 13: num_compromised
            0,                                 # 14: root_shell
            0,                                 # 15: su_attempted
            0,                                 # 16: num_root
            0,                                 # 17: num_file_creations
            0,                                 # 18: num_shells
            0,                                 # 19: num_access_files
            0,                                 # 20: num_outbound_cmds
            0,                                 # 21: is_host_login
            0,                                 # 22: is_guest_login
            total_packets,                     # 23: count (nombre de paquets)
            0,                                 # 24: srv_count
            0.0,                               # 25: serror_rate
            0.0,                               # 26: srv_serror_rate
            0.0,                               # 27: rerror_rate
            0.0,                               # 28: srv_rerror_rate
            0.0,                               # 29: same_srv_rate
            0.0,                               # 30: diff_srv_rate
            0.0,                               # 31: srv_diff_host_rate
            0,                                 # 32: dst_host_count
            0,                                 # 33: dst_host_srv_count
            0.0,                               # 34: dst_host_same_srv_rate
            0.0,                               # 35: dst_host_diff_srv_rate
            0.0,                               # 36: dst_host_same_src_port_rate
            0.0,                               # 37: dst_host_srv_diff_host_rate
            0.0,                               # 38: dst_host_serror_rate
            0.0,                               # 39: dst_host_srv_serror_rate
            0.0,                               # 40: dst_host_rerror_rate
            0.0                                # 41: dst_host_srv_rerror_rate
        ]

        # ============================================
        # 4. LOG DES FEATURES POUR DEBUG
        # ============================================
        log_message(f"📊 Features enrichies: duration={duration:.3f}, packets={total_packets}, bytes={bytes_total}, "
                   f"avg_size={avg_size:.1f}, packet_rate={packet_rate:.1f}, syn={syn_count}, ack={ack_count}, "
                   f"rst={rst_count}, fin={fin_count}, iat_mean={iat_mean:.3f}")

        # ============================================
        # 5. ENVOI À VM1
        # ============================================
        vm1_ip = discover_vm1()
        if not vm1_ip:
            log_message("⚠️ VM1 not discovered, skipping prediction")
            return
        
        url = f"http://{vm1_ip}:8001/predict"
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0NzYzMTM1OX0.1234567890abcdef"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            'features': feature_vector,
            'src_ip': first_packet['src_ip'],
            'dst_ip': first_packet['dst_ip'],
            'protocol': protocol_name,
            'length': first_packet['length'],
            'flags': first_packet['flags'],
            'timestamp': first_packet['timestamp'],
            'flow_id': f"{first_packet['src_ip']}_{first_packet['dst_ip']}_{first_packet['timestamp']}"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=2)
        
        if response.status_code == 200:
            result = response.json()
            log_message(f"🔮 ML Prediction: {result.get('label', 'unknown')} (conf: {result.get('confidence', 0)}%)")
            if result.get('label') == 'ATTACK':
                log_message(f"🚨 ALERT: Attack detected from {first_packet['src_ip']}!")
        else:
            log_message(f"⚠️ VM1 returned status {response.status_code}")
            
    except Exception as e:
        log_message(f"❌ Prediction error: {e}", "ERROR")

def process_batch():
    global packet_buffer

    with buffer_lock:
        if not packet_buffer:
            return
        batch = packet_buffer.copy()
        packet_buffer = []

    log_message(f"📦 Processing batch of {len(batch)} packets")

    for packet_data in batch:
        process_packet(packet_data)

# ============================================================================
# MAIN
# ============================================================================

def main():
    log_message("═══════════════════════════════════════════════════════════")
    log_message("🔶 SECURE-EYE-XX - Extraction + Backend (Enrichi)")
    log_message("═══════════════════════════════════════════════════════════")
    log_message(f"📡 UDP Server: port {UDP_PORT} (paquets)")
    log_message(f"📡 TCP Server: port {TCP_PORT} (scans)")
    log_message("═══════════════════════════════════════════════════════════")

    vm1_ip = discover_vm1()
    log_message(f"✅ SECURE-EYE (VM1) found at: {vm1_ip}")

    udp_thread = threading.Thread(target=udp_server, daemon=True)
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)

    udp_thread.start()
    tcp_thread.start()

    log_message("✅ All servers started. Waiting for data...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("\n⏹️  Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()