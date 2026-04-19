import sys
import os
import threading
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'capture'))
from sniffer import traffic_data, start_sniffer

app = Flask(__name__)
CORS(app)

@app.route("/traffic", methods=["GET"])
def get_traffic():
    return jsonify(traffic_data)

if __name__ == "__main__":
    # Run sniffer in background thread so Flask can also run
    sniffer_thread = threading.Thread(target=start_sniffer, daemon=True)
    sniffer_thread.start()
    app.run(debug=False)  # debug=False required when using threads