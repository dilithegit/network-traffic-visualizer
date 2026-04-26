import threading
from flask import Flask, jsonify
from flask_cors import CORS

# Internal imports
from backend.capture.sniffer import traffic_data, start_sniffer
from backend.analysis.stats import get_traffic_stats
from backend.database.db import init_db

app = Flask(__name__)
CORS(app)

def run_sniffer_thread():
    """Wrapper to start the sniffer in a background thread."""
    print("[*] Initializing Network Sniffer...")
    try:
        start_sniffer()
    except Exception as e:
        print(f"[!] Sniffer Error: {e}")

@app.route("/")
def home():
    # We use a try/except here just in case the thread hasn't defined 'sniffer_thread' yet
    try:
        is_alive = sniffer_thread.is_alive()
    except NameError:
        is_alive = False
    return {"status": "CNS Project 1 Backend Running", "sniffer_active": is_alive}

@app.route("/traffic", methods=["GET"])
def get_traffic():
    try:
        # traffic_data is a deque, so we convert to list to slice it for JSON
        return jsonify(list(traffic_data)[-50:])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/stats", methods=["GET"])
def stats():
    try:
        return jsonify(get_traffic_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 1. Create the database and table FIRST
    # This ensures the 'packets' table exists before the sniffer tries to write to it
    init_db() 
    
    # 2. Start the sniffer SECOND
    sniffer_thread = threading.Thread(target=run_sniffer_thread, daemon=True)
    sniffer_thread.start()
    
    # 3. Run the API THIRD
    print("[*] API running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)