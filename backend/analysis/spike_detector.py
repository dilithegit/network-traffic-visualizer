"""Per-IP traffic spike detector and suspicious-host registry.

For every source IP we keep a rolling 1-second window of packets and bytes.
When the packets/sec or bytes/sec cross configurable thresholds the host is
marked WARNING or CRITICAL. Each host accumulates a profile (spike count,
peak bandwidth, last activity, current status) that powers the Suspicious
Hosts panel.
"""

import time
from collections import defaultdict, deque

from config import (
    PACKET_THRESHOLD,
    BANDWIDTH_SPIKE_THRESHOLD_BYTES,
    SPIKE_ALERT_COOLDOWN,
)

logger = __import__("logging").getLogger(__name__)


class SpikeDetector:
    """Detect suspicious traffic spikes and maintain a suspicious hosts registry."""

    def __init__(
        self,
        packet_threshold=PACKET_THRESHOLD,
        bandwidth_threshold_bytes_per_second=BANDWIDTH_SPIKE_THRESHOLD_BYTES,
        notifier=None,
        window_seconds=1.0,
        cooldown=SPIKE_ALERT_COOLDOWN,
    ):
        self.packet_threshold = packet_threshold
        self.bandwidth_threshold_bytes_per_second = bandwidth_threshold_bytes_per_second
        self.notifier = notifier
        self.window_seconds = window_seconds
        self.cooldown = cooldown

        self.recent_alerts = deque(maxlen=100)
        self.packet_history = defaultdict(deque)  # ip -> deque[(ts, size)]
        self._prev_status = {}                     # ip -> last emitted status
        self._last_alert_ts = {}                   # ip -> last emit timestamp
        self.host_profiles = {}                    # ip -> profile dict

    def process_packet(self, packet):
        src_ip = packet.get("src_ip")
        size = packet.get("size", 0)
        if not src_ip:
            return None

        now = time.time()
        history = self.packet_history[src_ip]
        history.append((now, size))
        self._prune(history, now)

        packets_per_second = len(history)
        bytes_per_second = sum(sz for _, sz in history)
        mbps = round((bytes_per_second * 8) / (1024 * 1024), 2)

        profile = self.host_profiles.setdefault(src_ip, {
            "ip": src_ip,
            "spike_count": 0,
            "highest_bandwidth_mbps": 0,
            "last_activity": None,
            "current_status": "NORMAL",
        })

        profile["highest_bandwidth_mbps"] = max(profile["highest_bandwidth_mbps"], mbps)
        profile["last_activity"] = time.strftime("%H:%M:%S", time.localtime(now))

        status = self._determine_status(packets_per_second, bytes_per_second)
        profile["current_status"] = status

        # Only emit when the status changes or after a cooldown, so a host that
        # stays hot does not flood the alert feed every single packet.
        prev = self._prev_status.get(src_ip, "NORMAL")
        last_ts = self._last_alert_ts.get(src_ip, 0)
        should_alert = status != "NORMAL" and (
            status != prev or (now - last_ts) >= self.cooldown
        )

        alert = None
        if should_alert:
            profile["spike_count"] += 1
            alert = {
                "alert": "Traffic Spike Detected",
                "src_ip": src_ip,
                "packets_per_second": packets_per_second,
                "bandwidth_mbps": mbps,
                "severity": status,
                "timestamp": time.strftime("%H:%M:%S", time.localtime(now)),
            }
            self._prev_status[src_ip] = status
            self._last_alert_ts[src_ip] = now
            self.recent_alerts.appendleft(alert)
            if self.notifier:
                self.notifier.publish_spike(alert)
        elif status == "NORMAL":
            self._prev_status[src_ip] = "NORMAL"

        return alert

    def _determine_status(self, pps, bps):
        if pps >= self.packet_threshold and bps >= self.bandwidth_threshold_bytes_per_second:
            return "CRITICAL"
        if bps >= self.bandwidth_threshold_bytes_per_second or pps >= self.packet_threshold:
            return "WARNING"
        return "NORMAL"

    def _prune(self, history, now):
        cutoff = now - self.window_seconds
        while history and history[0][0] < cutoff:
            history.popleft()

    def get_recent_alerts(self):
        return list(self.recent_alerts)

    def get_suspicious_hosts(self):
        return sorted(
            self.host_profiles.values(),
            key=lambda item: (
                item["current_status"] != "NORMAL",
                item["current_status"] == "WARNING",
                item["highest_bandwidth_mbps"],
            ),
            reverse=True,
        )

    def get_host_profile(self, ip):
        return self.host_profiles.get(ip, {})


from alerts.notifier import alert_notifier  # noqa: E402  (avoid import cycle)

spike_detector = SpikeDetector(notifier=alert_notifier)
