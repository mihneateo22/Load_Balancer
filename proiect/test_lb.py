from scapy.all import IP, TCP
from load_balancer import process_packet, VIP, PORT, SERVERS, sessions

def test_load_balancer():
    print("=== Testing Load Balancer Logic ===\n")
    
    client1_ip = "192.168.1.10"
    client1_port = 54321
    
    client2_ip = "192.168.1.20"
    client2_port = 54322

    # 1. Client 1 trimite pachet (ex. SYN)
    pkt1 = IP(src=client1_ip, dst=VIP)/TCP(sport=client1_port, dport=PORT, flags="S")
    print(f"[*] Client 1 trimite: {pkt1[IP].src}:{pkt1[TCP].sport} -> {pkt1[IP].dst}:{pkt1[TCP].dport}")
    
    out1 = process_packet(pkt1, test_mode=True)
    assigned_server1 = out1[IP].dst
    print(f"    [+] LB DNAT rezultat: {out1[IP].src}:{out1[TCP].sport} -> {out1[IP].dst}:{out1[TCP].dport}")
    assert assigned_server1 in SERVERS, "Eroare: Pachetul nu a ajuns la un server valid."
    
    # 2. Client 2 trimite pachet
    pkt2 = IP(src=client2_ip, dst=VIP)/TCP(sport=client2_port, dport=PORT, flags="S")
    out2 = process_packet(pkt2, test_mode=True)
    assigned_server2 = out2[IP].dst
    print(f"[*] Client 2 trimite, ajunge la: {assigned_server2}")
    assert assigned_server2 != assigned_server1, "Eroare: Round-Robin nu funcționează corect (sau sunt prea puține servere)."

    # 3. Client 1 trimite al doilea pachet (ex. ACK) - Session Persistence
    pkt3 = IP(src=client1_ip, dst=VIP)/TCP(sport=client1_port, dport=PORT, flags="A")
    out3 = process_packet(pkt3, test_mode=True)
    assigned_server3 = out3[IP].dst
    print(f"[*] Client 1 trimite pachetul 2, ajunge la: {assigned_server3}")
    assert assigned_server3 == assigned_server1, "Eroare: Session Persistence nu a păstrat același server pentru Client 1."

    # 4. Server 1 răspunde către Client 1 (Reverse DNAT)
    pkt_return = IP(src=assigned_server1, dst=client1_ip)/TCP(sport=PORT, dport=client1_port, flags="SA")
    print(f"\n[*] Server {assigned_server1} răspunde: {pkt_return[IP].src}:{pkt_return[TCP].sport} -> {pkt_return[IP].dst}:{pkt_return[TCP].dport}")
    out_return = process_packet(pkt_return, test_mode=True)
    print(f"    [+] LB Reverse DNAT rezultat: {out_return[IP].src}:{out_return[TCP].sport} -> {out_return[IP].dst}:{out_return[TCP].dport}")
    
    assert out_return[IP].src == VIP, "Eroare: Reverse DNAT nu a modificat IP-ul sursă în VIP."
    assert not hasattr(out_return[IP], 'chksum') or out_return[IP].chksum == None, "Eroare: Checksum-ul IP nu a fost șters."
    assert not hasattr(out_return[TCP], 'chksum') or out_return[TCP].chksum == None, "Eroare: Checksum-ul TCP nu a fost șters."

    print("\n[✔] Toate testele au trecut cu succes! Logica este corectă.")

if __name__ == "__main__":
    test_load_balancer()
