import json
import logging
import threading
from scapy.all import sniff, send, IP, TCP
import os

VIP = "10.0.0.100"
PORT = 80
ALL_SERVERS = ["10.0.0.2", "10.0.0.3", "10.0.0.4"]

sessions = {}
stats = {server: 0 for server in ALL_SERVERS}
stats_lock = threading.Lock()

# Variabila globala pentru Round-Robin
rr_index = 0

def save_stats():
    with stats_lock:
        with open("stats.json", "w") as f:
            json.dump(stats, f)

def get_active_servers():
    # Citim cine este activ din fisierul status.json creat de API
    if os.path.exists("status.json"):
        with open("status.json", "r") as f:
            return json.load(f)
    return ALL_SERVERS

def get_server(client_ip, client_port):
    global rr_index
    key = f"{client_ip}:{client_port}"
    active = get_active_servers()
    
    if key in sessions and sessions[key] not in active:
        del sessions[key]
        
    if key not in sessions and active:
        # Round-Robin curat cu index incremental
        sessions[key] = active[rr_index % len(active)]
        rr_index += 1
        
    return sessions.get(key)

def process_packet(pkt):
    if IP in pkt and TCP in pkt:
        if pkt[IP].dst == VIP and pkt[TCP].dport == PORT:
            server_ip = get_server(pkt[IP].src, pkt[TCP].sport)
            if server_ip:
                pkt[IP].dst = server_ip
                del pkt[IP].chksum
                del pkt[TCP].chksum
                with stats_lock:
                    stats[server_ip] += 1
                save_stats()
                send(pkt[IP], verbose=False)
        elif pkt[IP].src in ALL_SERVERS and pkt[TCP].sport == PORT:
            pkt[IP].src = VIP
            del pkt[IP].chksum
            del pkt[TCP].chksum
            send(pkt[IP], verbose=False)

if __name__ == "__main__":
    print("Load Balancer pornit...")
    sniff(filter="tcp", prn=process_packet, store=False)