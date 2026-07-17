# Load_Balancer 

Acest proiect demonstrează funcționarea unui Load Balancer de Nivel 4 (L4) cu un dashboard interactiv în timp real. Proiectul interceptează traficul de rețea (TCP), îl distribuie către servere virtuale (backend) folosind un algoritm Round-Robin curat și expune starea rețelei printr-un API RESTful care comunică cu o interfață web modernă.

## Arhitectura Proiectului

Sistemul este compus din patru componente principale:

1.  **Generator de Trafic (`generator_demo.py`):** Folosește Scapy pentru a simula rapid pachete TCP (tipic conexiuni SYN) venind de la un client către VIP-ul (Virtual IP) Load Balancer-ului.
2.  **Load Balancer L4 (`load_balancer.py`):** Sniffer de rețea care rulează la nivel de sistem. Interceptează pachetele, determină ce server backend să le primească (prin Round-Robin) și le redirecționează rescriind IP-ul de destinație. Citește `status.json` pentru a ști ce servere sunt active.
3.  **REST API (`api.py`):** Un server Flask care citește statisticile de la LB (`stats.json`) și starea serverelor (`status.json`), calculează metricile în timp real (viteze, fluxuri, conexiuni) și le oferă dashboard-ului.
4.  **Dashboard-ul Web (`index.html`, `app.js`, `style.css`):** Interfața grafică modernă care pollează API-ul la fiecare secundă. Desenează topologia, distribuția traficului și oferă butoane pentru oprirea/pornirea dinamică a serverelor ("Kill Switch").

## Pre-rechizite

Pentru a rula acest proiect, ai nevoie de:
*   Un mediu Linux (ex: Ubuntu, WSL).
*   Python 3 instalat.
*   Librăriile necesare: `scapy`, `flask`, `flask-cors`.

Instalare dependențe:
```bash
pip install scapy flask flask-cors
```

## Instrucțiuni de Rulare

Pentru o funcționare corectă, scripturile trebuie pornite în ordinea de mai jos, preferabil în terminale separate. 

> **Notă:** `load_balancer.py` și `generator_demo.py` manipulează pachete direct la nivel de interfață, așadar trebuie rulate cu privilegii de administrator (`sudo`).

### 1. Pornește REST API-ul
Acest pas va porni serverul web pentru date și va inițializa fișierul `status.json`.
```bash
python api.py
```
*Lasă terminalul deschis.*

### 2. Pornește Load Balancer-ul
Acest pas va porni procesul care scanează pachetele și calculează statisticile, pe care le va scrie în `stats.json`.
```bash
sudo python load_balancer.py
```
*Lasă terminalul deschis.*

### 3. Pornește Generatorul de Trafic
Acest script va începe să inunde rețeaua virtuală cu pachete către Load Balancer.
```bash
sudo python generator_demo.py
```
*Lasă terminalul deschis.*

### 4. Accesează Dashboard-ul
Nu ai nevoie de un server web separat pentru front-end. 
* Deschide direct fișierul **`index.html`** într-un browser modern (Chrome/Edge/Firefox).
* Asigură-te că IP-ul declarat în `app.js` corespunde cu adresa pe care rulează `api.py` (pentru WSL sau LAN).

## Testare Interactivă
Odată ce dashboard-ul s-a conectat la API, vei observa distribuția proporțională a traficului. Pentru a testa funcționalitatea de Load Balancing:
1. Apasă butonul **"KILL"** pe oricare dintre servere (ex: Server 3).
2. Observă cum Load Balancer-ul încetează imediat să mai ruteze pachete către acel IP, distribuția traficului fiind reîmpărțită între serverele rămase. Viteza și fluxurile active vor scădea rapid spre 0 pentru serverul oprit.
3. Apasă **"START"** pentru a-l reintroduce în rotație.