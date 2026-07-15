"""Socket.IO wiring for NETSENTRY (req 3, 5, 9).

Exposes a single ``SocketIO`` instance, registers client event handlers, and
runs the background broadcaster that pushes ``statistics_update`` to every
connected client on a fixed interval. It also:

* Streams packets as batched ``packet_batch`` frames (the sniffer decides when
  to flush) so high capture rates stay smooth.
* Accepts a ``set_sensitivity`` event to re-tune the dynamic spike detector.
* Pushes ``interface_status`` details and an ``interface_warning`` event when a
  running adapter goes silent (req 5), and one-shot bandwidth alerts.
"""

import time

from flask_socketio import SocketIO
from analysis.stats import get_traffic_stats
from alerts.notifier import alert_notifier
from analysis.spike_detector import spike_detector
from capture.interface_manager import get_interface_statuses, get_interface_details, get_active_interface_name
from capture.sniffer import _flush_socket_batch, is_capture_running
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
        socketio.emit("interface_status", get_interface_details())

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

    @socketio.on("request_interfaces")
    def handle_request_interfaces():
        socketio.emit("interface_status", get_interface_details())

    @socketio.on("set_sensitivity")
    def handle_set_sensitivity(payload):
        level = (payload or {}).get("level") if isinstance(payload, dict) else payload
        ok = spike_detector.set_sensitivity(level) if level else False
        socketio.emit("sensitivity_updated", {
            "level": spike_detector.get_sensitivity(),
            "ok": ok,
        })
        socketio.emit("statistics_update", get_traffic_stats())


def start_statistics_broadcaster(interval_seconds=SOCKET_STATS_INTERVAL):
    """Periodically broadcast statistics, interface health and bandwidth alerts."""
    prev_high = False
    prev_idle = False

    def broadcaster():
        nonlocal prev_high, prev_idle
        while True:
            try:
                # Flush any packets still queued by the sniffer so the live
                # stream never lags behind the stats tick.
                _flush_socket_batch()

                stats = get_traffic_stats()
                socketio.emit("statistics_update", stats)
                # Push fresh per-interface detail (IPv4/MAC/packet counts/traffic
                # state) every tick so the UI reflects live VMware/physical state.
                socketio.emit("interface_status", get_interface_details(
                    active_real=get_active_interface_name(),
                    active_idle=stats.get("idle_warning", False),
                    capture_running=is_capture_running(),
                ))

                # Network-wide bandwidth threshold (one-shot edge trigger).
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

                # Inactive-interface warning (req 5): surface a clear message
                # instead of freezing silently.
                idle = stats.get("idle_warning", False)
                iface = stats.get("active_interface", "interface")
                if idle and not prev_idle:
                    socketio.emit("interface_warning", {
                        "interface": iface,
                        "message": (
                            f"No traffic detected on {iface}. The interface may be "
                            "inactive, disconnected, or not currently carrying traffic."
                        ),
                        "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                    })
                elif not idle and prev_idle:
                    socketio.emit("interface_warning_cleared", {
                        "interface": iface,
                        "timestamp": time.strftime("%H:%M:%S", time.localtime()),
                    })
                prev_idle = idle
            except Exception as exc:  # pragma: no cover - defensive
                import logging
                logging.getLogger(__name__).debug("Broadcaster error: %s", exc)
            socketio.sleep(interval_seconds)

    socketio.start_background_task(broadcaster)
