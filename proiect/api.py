from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
import time
import random

app = Flask(__name__)
CORS(app)

START_TIME = time.time()

# Buffer pentru media mobila (retine istoricul ultimelor citiri)
# Format: { ip: [(timp1, pachete1), (timp2, pachete2), ...] }
history_buffer = {"10.0.0.2": [], "10.0.0.3": [], "10.0.0.4": []}
MAX_HISTORY = 3  # Tine minte ultimele 3 secunde pentru o viteza neteda

# STAREA SERVERELOR: Tine minte cine este Alive (True) si cine este "Omorat" (False)
server_health = {1: True, 2: True, 3: True}

def update_status_file():
    # Mapam ID-urile pe IP-urile serverelor
    ip_map = {1: "10.0.0.2", 2: "10.0.0.3", 3: "10.0.0.4"}
    
    # Construim o lista doar cu IP-urile serverelor care sunt "Alive" (True)
    active_ips = [ip_map[sid] for sid, is_alive in server_health.items() if is_alive]
    
    # Scriem fisierul status.json pentru a fi citit de Load Balancer
    try:
        with open("status.json", "w") as f:
            json.dump(active_ips, f)
    except Exception as e:
        print("Eroare la scrierea status.json:", e)

# Apelam functia o data la pornire pentru a initializa corect fisierul
update_status_file()

@app.route('/api/traffic', methods=['GET'])
def get_traffic():
    global history_buffer
    
    uptime = int(time.time() - START_TIME)
    stats = {"10.0.0.2": 0, "10.0.0.3": 0, "10.0.0.4": 0} 

    # Citim datele de la Load Balancer (Scapy)
    if os.path.exists('stats.json'):
        try:
            with open('stats.json', 'r') as f:
                stats.update(json.load(f))
        except Exception:
            pass

    current_time = time.time()

    server_list = []
    total_packets = 0
    total_conns = 0
    total_flows = 0
    ip_to_id = {"10.0.0.2": 1, "10.0.0.3": 2, "10.0.0.4": 3}
    
    for ip, current_packets in stats.items():
        if ip in ip_to_id:
            s_id = ip_to_id[ip]
            is_alive = server_health[s_id]  # Citim starea serverului
            
            rate = 0
            
            # Adaugam valoarea curenta in istoric doar daca serverul e alive
            if is_alive:
                history_buffer[ip].append((current_time, current_packets))
            else:
                # Daca e mort, stergem istoricul recent pentru a forta viteza pe 0 instant
                history_buffer[ip].clear()
            
            # Pastram doar ultimele X inregistrari
            if len(history_buffer[ip]) > MAX_HISTORY:
                history_buffer[ip].pop(0)
                
            # Calculam viteza mediata (Smooth Rate) doar pt servere alive
            if is_alive and len(history_buffer[ip]) >= 2:
                oldest_time, oldest_packets = history_buffer[ip][0]
                newest_time, newest_packets = history_buffer[ip][-1]
                
                dt = newest_time - oldest_time
                dp = newest_packets - oldest_packets
                
                if dt > 0 and dp > 0:
                    rate = int(dp / dt)

           # CONEXIUNI (Istoric/Cumulativ): Cresc constant bazat pe totalul de pachete primite
            conns = current_packets // 10 if current_packets > 0 else 0
            
            # FLOW-URI ACTIVE (Timp real): Fluctuează în funcție de viteza de moment (rate)
            flows = rate // 2 if rate > 0 else 0
            if rate > 0 and flows == 0: 
                flows = 1 
                
            latency = random.randint(12, 24) if (current_packets > 0 and is_alive) else None
            
            server_list.append({
                "id": s_id,
                "ip": ip,
                "packets": current_packets,
                "connections": conns,
                "active_flows": flows,
                "alive": is_alive,  # Trimitem starea de sanatate pe site
                "last_seen_ms": latency,
                "rate_backend": rate  # Trimitem viteza smooth catre frontend
            })
            total_packets += current_packets
            total_conns += conns
            total_flows += flows

    response_data = {
        "vip": "10.0.0.100",
        "algorithm": "Round-Robin + Flow Persistence",
        "uptime_seconds": uptime,
        "servers": server_list,
        "totals": {
            "packets": total_packets,
            "connections": total_conns,
            "flows_tracked": total_flows
        }
    }
    
    return jsonify(response_data)

# RUTA NOUA: Pentru butonul de KILL / START
@app.route('/api/servers/<int:server_id>/toggle', methods=['POST'])
def toggle_server(server_id):
    if server_id in server_health:
        # Schimbam starea (True devine False, False devine True)
        server_health[server_id] = not server_health[server_id]
        
        # Actualizam fisierul status.json pentru a fi citit de Load Balancer
        update_status_file()
        
        return jsonify({"status": "success", "id": server_id, "alive": server_health[server_id]})
    return jsonify({"error": "Server not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)