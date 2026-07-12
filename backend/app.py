"""NETSENTRY (formerly PacketMon) - Flask + Socket.IO application entry point.

Wires together the REST blueprint, the Socket.IO layer, and the packet
capture engine. Capture does not start automatically; the dashboard selects
an interface and calls ``/capture/start``. The statistics broadcaster is
launched as a Socket.IO background task so clients receive live updates.
"""

import logging
import threading

from flask import Flask, jsonify
from flask_cors import CORS

from config import API_HOST, API_PORT, API_DEBUG
from database.db import init_db
from routes.api import api
from services.socket_events import socketio, init_socketio, start_statistics_broadcaster
from capture.sniffer import start_capture
from capture.interface_manager import get_default_interface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.register_blueprint(api)
init_socketio(app)


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint."""
    from capture.sniffer import is_capture_running
    return jsonify({
        "status": "NETSENTRY Backend Running",
        "sniffer_active": is_capture_running(),
        "version": "2.0.0",
    }), 200


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(_error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("[*] Initializing database...")
    init_db()

    default_iface = get_default_interface()
    if default_iface:
        logger.info("[*] Auto-starting capture on: %s", default_iface)
        threading.Thread(
            target=start_capture, args=(default_iface,), daemon=True
        ).start()
    else:
        logger.warning("[!] No default interface found; start capture manually.")

    start_statistics_broadcaster()
    logger.info("[*] NETSENTRY API + Socket.IO on http://%s:%s", API_HOST, API_PORT)
    socketio.run(app, host=API_HOST, port=API_PORT, debug=API_DEBUG)
