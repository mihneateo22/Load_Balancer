from flask import Flask, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/traffic', methods=['GET'])
def get_traffic():
    if os.path.exists('stats.json'):
        try:
            with open('stats.json', 'r') as f:
                stats = json.load(f)
            return jsonify(stats)
        except Exception:
            pass
    fallback_stats = {"server1": 0, "server2": 0, "server3": 0}
    return jsonify(fallback_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
