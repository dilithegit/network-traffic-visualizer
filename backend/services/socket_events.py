"""Socket.IO wiring for NETSENTRY.

Exposes a single ``SocketIO`` instance, registers client event handlers, and
runs the background broadcaster that pushes ``statistics_update`` to every
connected client on a fixed interval. When the network-wide bandwidth
threshold is crossed it also emits a one-shot ``new_alert`` so the alert feed
is not spammed every tick.
"""

import time

from flask_socketio import SocketIO
from analysis.stats import get_traffic_stats
from alerts.notifier import alert_notifier
from config import SOCKET_STATS_INTERVAL

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def init_socketio(app):
    """Attach Socket.IO to the Flask app and register handlers."""
    socketio.init_app(app)
    alert_notifier.set_socketio(socketio)

    @socketio.on("connect")
    def handle_connect():
        socketio.emit("statistics_update", get_traffic_stats())
        socketio.emit("suspicious_hosts", alert_notifier.get_suspicious_ips())
        socketio.emit("alert_history", alert_notifier.get_recent_alerts())
        socketio.emit("url_history", alert_notifier.get_recent_urls())

    @socketio.on("request_stats")
    def handle_request_stats():
        socketio.emit("statistics_update", get_traffic_stats())

    @socketio.on("request_urls")
    def handle_request_urls():
        socketio.emit("url_history", alert_notifier.get_recent_urls())

    @socketio.on("request_alerts")
    def handle_request_alerts():
        socketio.emit("alert_history", alert_notifier.get_recent_alerts())

    @socketio.on("request_suspicious")
    def handle_request_suspicious():
        socketio.emit("suspicious_hosts", alert_notifier.get_suspicious_ips())


def start_statistics_broadcaster(interval_seconds=SOCKET_STATS_INTERVAL):
    """Periodically broadcast statistics and one-shot bandwidth alerts."""
    prev_high = False

    def broadcaster():
        nonlocal prev_high
        while True:
            try:
                stats = get_traffic_stats()
                socketio.emit("statistics_update", stats)

                bandwidth = stats.get("bandwidth", {})
                is_high = bandwidth.get("is_high", False)
                if is_high and not prev_high:
                    alert_notifier.publish_alert({
                        "alert": "Bandwidth Threshold Exceeded",
                        "severity": "CRITICAL",
                        "mbps": bandwidth.get("total_mbps"),
                        "threshold_mbps": bandwidth.get("threshold_mbps"),
                        "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                    })
                prev_high = is_high
            except Exception as exc:  # pragma: no cover - defensive
                import logging
                logging.getLogger(__name__).debug("Broadcaster error: %s", exc)
            socketio.sleep(interval_seconds)

    socketio.start_background_task(broadcaster)
