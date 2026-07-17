import json
import logging
import threading
from scapy.all import sniff, send, IP, TCP

VIP = "10.0.0.100"
PORT = 80
SERVERS = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]

sessions = {}
stats = {server: 0 for server in SERVERS}
rr_index = 0
stats_lock = threading.Lock()

def save_stats():
    with stats_lock:
        with open("stats.json", "w") as f:
            json.dump(stats, f)

def get_server(client_ip, client_port):
    global rr_index
    key = f"{client_ip}:{client_port}"
    if key not in sessions:
        server = SERVERS[rr_index % len(SERVERS)]
        rr_index += 1
        sessions[key] = server
        logging.info(f"[+] Flow nou {key} direcționat către {server}")
    return sessions[key]

def process_packet(pkt, test_mode=False):
    if IP in pkt and TCP in pkt:
        if pkt[IP].dst == VIP and pkt[TCP].dport == PORT:
            client_ip = pkt[IP].src
            client_port = pkt[TCP].sport
            
            server_ip = get_server(client_ip, client_port)
            pkt[IP].dst = server_ip
            
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            stats[server_ip] += 1
            save_stats()
            
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

        elif pkt[IP].src in SERVERS and pkt[TCP].sport == PORT:
            pkt[IP].src = VIP
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

def start_lb():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info(f"[*] Pornire Load Balancer L4 pe VIP {VIP}:{PORT}...")
    save_stats()
    sniff(filter="tcp", prn=process_packet, store=False)

if __name__ == "__main__":
    start_lb()
