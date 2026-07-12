"""Alert notifier: the single bridge between analysis modules and clients.

Analysis modules (URL extraction, spike detection, the statistics broadcaster)
call into this notifier instead of touching Socket.IO directly. The notifier
keeps a bounded in-memory history for REST hydration and, when a Socket.IO
server is attached, broadcasts the corresponding event to every connected
client. All emits are best-effort: if the server is not yet attached (e.g.
during import / unit tests) the calls are simply dropped.
"""

from collections import deque


class AlertNotifier:
    """Broadcast analysis updates and retain recent history."""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.recent_packets = deque(maxlen=300)
        self.recent_urls = deque(maxlen=100)
        self.recent_alerts = deque(maxlen=100)
        self.suspicious_ips = set()

    # -- Wiring -----------------------------------------------------------
    def set_socketio(self, socketio):
        """Attach the Flask-SocketIO instance once the app is created."""
        self.socketio = socketio

    # -- Publishing -------------------------------------------------------
    def publish_packet(self, payload):
        """Emit a single parsed packet to live log subscribers."""
        self.recent_packets.append(payload)
        self._emit("new_packet", payload)

    def publish_url(self, payload):
        """Emit a detected HTTP URL / HTTPS SNI."""
        self.recent_urls.append(payload)
        self._emit("new_url", payload)

    def publish_spike(self, payload):
        """Emit a per-IP traffic spike (drives spike + alert panels)."""
        self.recent_alerts.appendleft(payload)
        self.suspicious_ips.add(payload.get("src_ip"))
        self._emit("spike_detected", payload)
        self._emit("new_alert", payload)

    def publish_alert(self, payload):
        """Emit a generic alert (e.g. network-wide bandwidth threshold)."""
        self.recent_alerts.appendleft(payload)
        self._emit("new_alert", payload)

    # -- Internal ---------------------------------------------------------
    def _emit(self, event_name, payload):
        if not self.socketio:
            return
        try:
            self.socketio.emit(event_name, payload, broadcast=True)
        except Exception:
            pass

    # -- History accessors (used by REST endpoints) -----------------------
    def get_recent_packets(self):
        return list(self.recent_packets)

    def get_recent_urls(self):
        return list(self.recent_urls)

    def get_recent_alerts(self):
        return list(self.recent_alerts)

    def get_suspicious_ips(self):
        return sorted(self.suspicious_ips)


alert_notifier = AlertNotifier()
