from flask import Flask, jsonify
from flask_cors import CORS
import json
import os

# Initializam aplicatia web
app = Flask(__name__)

# Permitem cererile de tip Cross-Origin (CORS) pentru a putea conecta Frontend-ul
CORS(app)

# Definim ruta pentru preluarea statisticilor
@app.route('/api/traffic', methods=['GET'])
def get_traffic():
    # 1. Verificam daca fisierul stats.json a fost creat de Load Balancer
    if os.path.exists('stats.json'):
        try:
            # 2. Citim datele din fisier
            with open('stats.json', 'r') as f:
                stats = json.load(f)
            # 3. Returnam datele citite in format JSON
            return jsonify(stats)
        except Exception:
            pass
            
    # 4. In caz de eroare sau daca fisierul nu exista inca, returnam valori default
    fallback_stats = {"server1": 0, "server2": 0, "server3": 0}
    return jsonify(fallback_stats)

if __name__ == '__main__':
    # 5. Pornim serverul pe portul 5000, ascultand pe toate retelele
    app.run(host='0.0.0.0', port=5000)
