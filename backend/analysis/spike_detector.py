"""Dynamic, statistical traffic-spike detector (req 3).

Replaces the previous fixed-threshold detector. For every source IP we bucket
packets into one-second intervals and keep a rolling baseline of
(packets/sec, bytes/sec) samples. An observation is flagged when it deviates
from the learned baseline by more than a configurable number of standard
deviations (z-score). Severity scales automatically with the magnitude of the
deviation, and three sensitivity presets (low / medium / high) tune how
aggressively we alert.
"""

import time
import threading
from collections import defaultdict, deque

from config import (
    PACKET_THRESHOLD,
    BANDWIDTH_SPIKE_THRESHOLD_BYTES,
    SPIKE_ALERT_COOLDOWN,
    SPIKE_SENSITIVITY,
    SPIKE_SENSITIVITY_PRESETS,
    SPIKE_SEVERITY_CRITICAL_Z,
    SPIKE_SEVERITY_WARNING_Z,
)
from analysis.hostname_cache import hostname_cache

logger = __import__("logging").getLogger(__name__)


class SpikeDetector:
    """Detect anomalous traffic spikes using a per-IP statistical baseline."""

    def __init__(
        self,
        notifier=None,
        sensitivity=SPIKE_SENSITIVITY,
        packet_threshold=PACKET_THRESHOLD,
        bandwidth_threshold_bytes_per_second=BANDWIDTH_SPIKE_THRESHOLD_BYTES,
        cooldown=SPIKE_ALERT_COOLDOWN,
    ):
        self.notifier = notifier
        self.packet_threshold = packet_threshold
        self.bandwidth_threshold_bytes_per_second = bandwidth_threshold_bytes_per_second
        self.cooldown = cooldown

        self.sensitivity = sensitivity
        self._preset = SPIKE_SENSITIVITY_PRESETS.get(sensitivity, SPIKE_SENSITIVITY_PRESETS["medium"])
        self.warning_z = self._preset["zscore"]
        # Critical escalation scales with the chosen sensitivity preset.
        self.critical_z = max(self.warning_z * 1.6, SPIKE_SEVERITY_CRITICAL_Z)
        self.min_samples = self._preset["min_samples"]
        self.window = self._preset["window"]

        self.recent_alerts = deque(maxlen=100)
        self.accumulators = {}               # ip -> {second, count, bytes}
        self.baselines = defaultdict(deque)  # ip -> deque[(pps, bps)]
        self._prev_status = {}               # ip -> last emitted status
        self._last_alert_ts = {}             # ip -> last emit timestamp
        self.host_profiles = {}              # ip -> profile dict
        self._lock = threading.Lock()

    # -- Configuration ----------------------------------------------------
    def set_sensitivity(self, level):
        """Switch the sensitivity preset (low | medium | high)."""
        preset = SPIKE_SENSITIVITY_PRESETS.get(level)
        if not preset:
            return False
        with self._lock:
            self.sensitivity = level
            self._preset = preset
            self.warning_z = preset["zscore"]
            self.critical_z = max(preset["zscore"] * 1.6, SPIKE_SEVERITY_CRITICAL_Z)
            self.min_samples = preset["min_samples"]
            self.window = preset["window"]
            # Reset baselines so the new preset learns fresh.
            self.baselines.clear()
            self.accumulators.clear()
        return True

    def get_sensitivity(self):
        return self.sensitivity

    # -- Ingestion --------------------------------------------------------
    def process_packet(self, packet):
        src_ip = packet.get("src_ip")
        size = packet.get("size", 0)
        if not src_ip:
            return None

        now = time.time()
        sec = int(now)

        acc = self.accumulators.get(src_ip)
        if acc is None:
            acc = self.accumulators[src_ip] = {"second": sec, "count": 0, "bytes": 0}

        # Bucket boundary crossed: finalize the previous second. The current
        # packet starts the new bucket. This yields one evaluation per IP/sec.
        if sec != acc["second"]:
            alert = self._finalize(src_ip, acc, sec)
            acc["second"] = sec
            acc["count"] = 0
            acc["bytes"] = 0
        else:
            alert = None

        acc["count"] += 1
        acc["bytes"] += size

        # Update lightweight profile counters (no baseline required).
        self._touch_profile(src_ip, size, now)
        return alert

    # -- Evaluation -------------------------------------------------------
    def _finalize(self, ip, acc, sec):
        pps = acc["count"]
        bps = acc["bytes"]
        mbps = round((bps * 8) / (1024 * 1024), 2)

        with self._lock:
            samples = self.baselines[ip]
            # Evaluate against the *existing* baseline (current excluded).
            if len(samples) >= self.min_samples:
                mean_pps, std_pps, mean_bps, std_bps = self._stats(samples)
                z_pps = self._zscore(pps, mean_pps, std_pps)
                z_bps = self._zscore(mbps, mean_bps, std_bps)
                # A zero-variance baseline with a sudden jump is, by
                # definition, anomalous: force a high z-score so it triggers.
                if std_pps == 0 and pps > mean_pps:
                    z_pps = max(z_pps, self.critical_z + 1)
                if std_bps == 0 and mbps > mean_bps:
                    z_bps = max(z_bps, self.critical_z + 1)
                z = max(z_pps, z_bps)
                status = self._severity(z)
            else:
                # Warm-up: fall back to the legacy fixed thresholds.
                status = self._fixed_status(pps, bps)

            # Append the finalized sample *after* evaluation.
            samples.append((pps, mbps))
            while len(samples) > self.window:
                samples.popleft()

        profile = self.host_profiles.get(ip)
        if profile:
            profile["current_status"] = status

        return self._maybe_alert(ip, status, pps, mbps, sec)

    def _stats(self, samples):
        n = len(samples)
        mean_pps = sum(s[0] for s in samples) / n
        mean_bps = sum(s[1] for s in samples) / n
        var_pps = sum((s[0] - mean_pps) ** 2 for s in samples) / n
        var_bps = sum((s[1] - mean_bps) ** 2 for s in samples) / n
        return mean_pps, var_pps ** 0.5, mean_bps, var_bps ** 0.5

    @staticmethod
    def _zscore(value, mean, std):
        if std <= 0:
            return 0.0
        return (value - mean) / std

    def _severity(self, z):
        if z >= self.critical_z:
            return "CRITICAL"
        if z >= self.warning_z:
            return "WARNING"
        return "NORMAL"

    def _fixed_status(self, pps, bps):
        if pps >= self.packet_threshold and bps >= self.bandwidth_threshold_bytes_per_second:
            return "CRITICAL"
        if pps >= self.packet_threshold or bps >= self.bandwidth_threshold_bytes_per_second:
            return "WARNING"
        return "NORMAL"

    def _maybe_alert(self, ip, status, pps, mbps, sec):
        prev = self._prev_status.get(ip, "NORMAL")
        last_ts = self._last_alert_ts.get(ip, 0)
        now = time.time()
        should_alert = status != "NORMAL" and (
            status != prev or (now - last_ts) >= self.cooldown
        )
        alert = None
        if should_alert:
            profile = self.host_profiles.setdefault(ip, self._new_profile(ip))
            profile["spike_count"] += 1
            profile["current_status"] = status
            # Resolve a hostname for the offending IP via the DNS cache so
            # alerts read "www.youtube.com" instead of a bare address (req 4).
            hostname = hostname_cache.resolve(ip) or ""
            alert = {
                "alert": "Traffic Spike Detected",
                "alert_type": "HIGH BANDWIDTH" if mbps >= 1 else "SPIKE",
                "src_ip": ip,
                "hostname": hostname,
                "packets_per_second": pps,
                "bandwidth_mbps": mbps,
                "peak_mbps": profile["highest_bandwidth_mbps"],
                "severity": status,
                "timestamp": time.strftime("%H:%M:%S", time.localtime(now)),
            }
            self._prev_status[ip] = status
            self._last_alert_ts[ip] = now
            self.recent_alerts.appendleft(alert)
            if self.notifier:
                self.notifier.publish_spike(alert)
        elif status == "NORMAL":
            self._prev_status[ip] = "NORMAL"
        return alert

    def _touch_profile(self, ip, size, now):
        profile = self.host_profiles.get(ip)
        if not profile:
            profile = self.host_profiles[ip] = self._new_profile(ip)
        mbps = round((size * 8) / (1024 * 1024), 4)
        profile["highest_bandwidth_mbps"] = max(profile["highest_bandwidth_mbps"], mbps)
        profile["last_activity"] = time.strftime("%H:%M:%S", time.localtime(now))

    @staticmethod
    def _new_profile(ip):
        return {
            "ip": ip,
            "spike_count": 0,
            "highest_bandwidth_mbps": 0,
            "last_activity": None,
            "current_status": "NORMAL",
        }

    # -- Accessors --------------------------------------------------------
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
