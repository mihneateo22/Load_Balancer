import json
import logging
import threading
from scapy.all import sniff, send, IP, TCP

# 1. Definim datele retelei si ale IP-ului virtual
VIP = "10.0.0.100"
PORT = 80

# 2. Definim lista serverelor backend
SERVERS = ["10.0.0.2", "10.0.0.3", "10.0.0.4"]

# 3. Definim dictionarul pentru pastrarea sesiunilor (Session Persistence)
sessions = {}

# 4. Initializam statisticile de trafic pentru fiecare server
stats = {server: 0 for server in SERVERS}
rr_index = 0

# 5. Cream un lock pentru a preveni coliziunile la scrierea in fisier
stats_lock = threading.Lock()

def save_stats():
    # 6. Salvam statisticile in fisierul stats.json pentru a fi citite de API-ul Flask
    with stats_lock:
        with open("stats.json", "w") as f:
            json.dump(stats, f)

def get_server(client_ip, client_port):
    global rr_index
    # 7. Cream cheia unica pentru flow (IP:Port)
    key = f"{client_ip}:{client_port}"
    
    # 8. Verificam daca este un flow nou (Session Persistence)
    if key not in sessions:
        # Aici aplicam logica de Round-Robin pentru a alege serverul
        server = SERVERS[rr_index % len(SERVERS)]
        rr_index += 1
        
        # Salvam alegerea in dictionarul de sesiuni
        sessions[key] = server
        logging.info(f"[+] Flow nou {key} direcționat către {server}")
        
    return sessions[key]

def process_packet(pkt, test_mode=False):
    # 9. Asiguram ca prelucram doar pachetele IP si TCP
    if IP in pkt and TCP in pkt:
        
        # 10. Interceptam pachetele trimise catre Load Balancer (Client -> LB)
        if pkt[IP].dst == VIP and pkt[TCP].dport == PORT:
            client_ip = pkt[IP].src
            client_port = pkt[TCP].sport
            
            # 11. Alegem serverul bazat pe Round-Robin si Session Persistence
            server_ip = get_server(client_ip, client_port)
            
            # 12. Modificam IP-ul destinatie (Forward DNAT)
            pkt[IP].dst = server_ip
            
            # 13. Stergem sumele de control pentru a lasa Scapy sa le recalculeze automat
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            # 14. Actualizam si salvam statisticile
            stats[server_ip] += 1
            save_stats()
            
            # 15. Trimitem pachetul mai departe in retea
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

        # 16. Interceptam pachetele care se intorc de la servere (Server -> LB -> Client)
        elif pkt[IP].src in SERVERS and pkt[TCP].sport == PORT:
            # 17. Modificam IP-ul sursa pentru ca clientul sa creada ca VIP-ul i-a raspuns (Reverse DNAT)
            pkt[IP].src = VIP
            
            # 18. Stergem sumele de control
            del pkt[IP].chksum
            del pkt[TCP].chksum
            
            # 19. Trimitem pachetul returnat inapoi in retea
            if not test_mode:
                send(pkt[IP], verbose=False)
            return pkt

def start_lb():
    # 20. Pornim logarea si ascultarea traficului (Sniff)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info(f"[*] Pornire Load Balancer L4 pe VIP {VIP}:{PORT}...")
    
    save_stats()
    
    # Folosim filter="tcp" pentru a captura exclusiv traficul dorit
    sniff(filter="tcp", prn=process_packet, store=False)

if __name__ == "__main__":
    start_lb()
