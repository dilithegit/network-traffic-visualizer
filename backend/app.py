import threading
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Internal imports
from capture.sniffer import traffic_data, start_sniffer, stop_sniffer, is_capture_running
from analysis.stats import get_traffic_stats
from database.db import init_db
from config import API_HOST, API_PORT, API_DEBUG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

sniffer_thread = None

def run_sniffer_thread():
    """Wrapper to start the sniffer in a background thread."""
    logger.info("[*] Initializing Network Sniffer...")
    try:
        start_sniffer()
    except Exception as e:
        logger.error(f"[!] Sniffer Error: {e}")

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    try:
        is_alive = sniffer_thread.is_alive() if sniffer_thread else False
    except (NameError, AttributeError):
        is_alive = False
    return jsonify({
        "status": "CNS Project 1 Backend Running",
        "sniffer_active": is_alive,
        "version": "1.1.0"
    }), 200

@app.route("/traffic", methods=["GET"])
def get_traffic():
    """Get recent traffic packets"""
    try:
        return jsonify(list(traffic_data)[-50:]), 200
    except Exception as e:
        logger.error(f"Error in /traffic: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/stats", methods=["GET"])
def stats():
    """Get comprehensive traffic statistics"""
    try:
        return jsonify(get_traffic_stats()), 200
    except Exception as e:
        logger.error(f"Error in /stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/capture/stop", methods=["POST"])
def stop_capture():
    """Stop the packet sniffer and mark capture as inactive."""
    try:
        stop_sniffer()
        return jsonify({"success": True, "running": False}), 200
    except Exception as e:
        logger.error(f"Error stopping capture: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/capture/status", methods=["GET"])
def capture_status():
    """Return the current capture running state."""
    return jsonify({"running": is_capture_running()}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # 1. Create the database and table FIRST
    logger.info("[*] Initializing database...")
    init_db()
    
    # 2. Start the sniffer SECOND
    logger.info("[*] Starting packet sniffer thread...")
    sniffer_thread = threading.Thread(target=run_sniffer_thread, daemon=True)
    sniffer_thread.start()
    
    # 3. Run the API THIRD
    logger.info(f"[*] API running at http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)