from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel

class LoadBalancerTopo(Topo):
    def build(self):
        # 1. Adaugam switch-ul central (Layer 2)
        switch = self.addSwitch('s1')

        # 2. Adaugam host-ul Client
        client = self.addHost('h_client', ip='10.0.0.1/24')

        # 3. Adaugam Load Balancer-ul (Aici va rula scriptul Scapy)
        lb = self.addHost('h_lb', ip='10.0.0.100/24')

        # 4. Adaugam cele 3 servere backend
        server1 = self.addHost('h_srv1', ip='10.0.0.2/24')
        server2 = self.addHost('h_srv2', ip='10.0.0.3/24')
        server3 = self.addHost('h_srv3', ip='10.0.0.4/24')

        # 5. Cablam reteaua: conectam toate nodurile la switch
        self.addLink(client, switch)
        self.addLink(lb, switch)
        self.addLink(server1, switch)
        self.addLink(server2, switch)
        self.addLink(server3, switch)

def run():
    # Setam nivelul de logare pentru a vedea detaliile in consola
    setLogLevel('info')
    
    print("\n[+] Construim topologia Mininet...")
    topo = LoadBalancerTopo()
    
    # Initializam reteaua cu un controller default
    net = Mininet(topo=topo, controller=OVSController)
    
    print("[+] Pornim reteaua...")
    net.start()
    
    print("\n*** Topologia a fost creata cu succes! ***")
    print("*** Pentru a testa conectivitatea, scrie comanda: pingall ***")
    print("*** Pentru a iesi si a inchide reteaua, scrie: exit ***\n")
    
    # Deschidem interfata CLI a Mininet pentru a interactiona
    CLI(net)
    
    # Oprim curat procesele Mininet la iesire
    net.stop()

if __name__ == '__main__':
    run()