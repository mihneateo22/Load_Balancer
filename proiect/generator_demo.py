import time
import random
from scapy.all import IP, TCP
from load_balancer import process_packet, VIP, PORT

print("=== Generator pornit ===")
while True:
    try:
        # Creștem numărul de conexiuni noi (5-15 conexiuni per iterație)
        new_conns = random.randint(5, 15)
        for _ in range(new_conns):
            client_port = random.randint(10000, 60000)
            
            # Creștem numărul de pachete trimise per conexiune
            for _ in range(random.randint(10, 30)):
                pkt = IP(src="192.168.1.10", dst=VIP)/TCP(sport=client_port, dport=PORT, flags="S")
                process_packet(pkt)
                
        # Reducem semnificativ timpul de așteptare pentru a inunda cu pachete
        time.sleep(0.02)
    except: break