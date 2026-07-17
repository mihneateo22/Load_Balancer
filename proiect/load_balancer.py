import json
import logging
import threading
from scapy.all import sniff, send, IP, TCP

# Configurare rețea - Dummy IPs pentru test (se vor ajusta în Mininet)
VIP = "10.0.0.100"
PORT = 80
SERVERS = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]

# Dicționar pentru Session Persistence: (Client_IP, Client_Port) -> Server_IP
sessions = {}

# Statistici pentru Backend API (Partea 3)
stats = {server: 0 for server in SERVERS}
rr_index = 0

# Lock pentru a proteja scrierea în fișier (opțional, dar recomandat)
stats_lock = threading.Lock()

def save_stats():
    """Salvează statisticile în stats.json pentru API-ul Flask."""
    with stats_lock:
        with open("stats.json", "w") as f:
            json.dump(stats, f)

def get_server(client_ip, client_port):
    """Alege un server pe bază de Round-Robin și memorează decizia (Session Persistence)."""
    global rr_index
    key = f"{client_ip}:{client_port}"
    if key not in sessions:
        # Flow nou -> Alege server prin Round-Robin
        server = SERVERS[rr_index % len(SERVERS)]
        rr_index += 1
        sessions[key] = server
        logging.info(f"[+] Flow nou {key} direcționat către {server}")
    return sessions[key]

def process_packet(pkt, test_mode=False):
    """Procesează pachetele prin interceptare pasivă."""
    if IP in pkt and TCP in pkt:
        # 1. Forward DNAT (Client -> VIP)
        if pkt[IP].dst == VIP and pkt[TCP].dport == PORT:
            client_ip = pkt[IP].src
            client_port = pkt[TCP].sport
            
            # Alegem serverul pe baza sesiunii (Session Persistence)
            server_ip = get_server(client_ip, client_port)
            
            # Rescriem IP Destinație
            pkt[IP].dst = server_ip
            
            # Ștergem checksum-urile ca Scapy să le recalculeze automat
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            # Actualizăm statisticile doar la SYN pentru a număra conexiunile,
            # sau la orice pachet dacă dorim volumul total (Cerința inițială e pachete trimise)
            stats[server_ip] += 1
            save_stats()
            
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

        # 2. Reverse DNAT (Server -> Client)
        elif pkt[IP].src in SERVERS and pkt[TCP].sport == PORT:
            # Pachetul vine de la backend și se întoarce la client
            # Rescriem IP Sursă ca fiind VIP-ul, altfel clientul dă DROP
            pkt[IP].src = VIP
            
            # Ștergem checksum-urile
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

def start_lb():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info(f"[*] Pornire Load Balancer L4 pe VIP {VIP}:{PORT}...")
    # Salvăm starea inițială a statisticilor
    save_stats()
    
    # Sniffăm doar trafic TCP
    # Nu folosim store=True ca să nu consumăm memoria
    sniff(filter="tcp", prn=process_packet, store=False)

if __name__ == "__main__":
    start_lb()
