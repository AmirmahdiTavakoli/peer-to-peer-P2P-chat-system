from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for peers (Dictionary)
# Format: { "username": {"ip": "127.0.0.1", "port": 5001} }
online_peers = {}

@app.route('/register', methods=['POST'])
def register():
    """
    Endpoint 1: Register a new peer
    Input: JSON { "username": "Alice", "ip": "...", "port": ... }
    """
    data = request.json
    username = data.get('username')
    ip = data.get('ip')
    port = data.get('port')
    
    if not username or not ip or not port:
        return jsonify({"message": "Invalid data"}), 400
    
    # Save to memory (or Redis if you implemented the bonus)
    online_peers[username] = {"ip": ip, "port": port}
    
    print(f"[+] Registered user: {username} at {ip}:{port}")
    return jsonify({"message": "Registered successfully"}), 201

@app.route('/peers', methods=['GET'])
def get_peers():
    """
    Endpoint 2: Get list of all peers
    """
    return jsonify(list(online_peers.keys())), 200

@app.route('/peerinfo', methods=['GET'])
def get_peer_info():
    """
    Endpoint 3: Get specific peer info
    Input: ?username=Alice
    """
    username = request.args.get('username')
    info = online_peers.get(username)
    
    if info:
        return jsonify(info), 200
    else:
        return jsonify({"message": "User not found"}), 404

if __name__ == '__main__':
    print("[*] Registry Server running on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
