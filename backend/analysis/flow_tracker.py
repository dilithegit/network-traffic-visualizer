"""Active network flow tracking (req 5).

Groups packets into conversations (flows) so the dashboard can show what is
actually consuming bandwidth: a download from ``download.microsoft.com`` at
91 Mbps, a YouTube stream at 18 Mbps, etc. A flow is keyed by the pair of
endpoints plus the service port and IP protocol, so both directions of a
conversation are merged into one record. For every flow we maintain total
bytes, a short recent window for the *current* speed, and resolve a hostname
via HTTP/HTTPS metadata or the DNS cache.
"""

import time
import threading
from collections import deque

from config import HOSTNAME_CACHE_TTL
from analysis.hostname_cache import hostname_cache

# Flow considered finished (and retired) after this many idle seconds.
FLOW_TIMEOUT = 60
# Window used to compute the live "current speed".
SPEED_WINDOW = 2.0

# Domains we treat as streaming rather than generic downloads.
STREAMING_DOMAINS = ("youtube", "netflix", "twitch", "spotify", "vimeo",
                     "disney", "hulu", "googlevideo", "fbcdn", "tiktok")

EPHEMERAL = 1024  # ports below this are generally services, not clients


def _service_port(src_port, dst_port):
    """Pick the stable service port so both directions share one flow key."""
    if src_port and src_port < EPHEMERAL:
        return src_port
    if dst_port and dst_port < EPHEMERAL:
        return dst_port
    # Both ephemeral (peer-to-peer-ish): use the larger as the anchor.
    return max(src_port or 0, dst_port or 0)


def _flow_type(hostname, layer, bytes_remote, bytes_local, total_bytes):
    host = (hostname or "").lower()
    if any(sd in host for sd in STREAMING_DOMAINS):
        return "Streaming"
    web = layer in ("HTTP", "HTTPS", "QUIC", "TLS", "FTP")
    if web and bytes_remote >= bytes_local and total_bytes > 1_000_000:
        return "Download"
    if bytes_local > bytes_remote and total_bytes > 1_000_000:
        return "Upload"
    return "Transfer"


class FlowTracker:
    """Maintain a rolling set of active network flows."""

    def __init__(self):
        self.flows = {}
        self._lock = threading.Lock()

    def process_packet(self, pkt):
        src_ip = pkt.get("src_ip")
        dst_ip = pkt.get("dst_ip")
        if not src_ip or not dst_ip:
            return
        size = pkt.get("size", 0)
        src_port = pkt.get("src_port", 0) or 0
        dst_port = pkt.get("dst_port", 0) or 0
        proto = pkt.get("protocol", "")
        layer = pkt.get("layer", proto)
        ts = pkt.get("timestamp", time.time())

        service_port = _service_port(src_port, dst_port)
        key = (frozenset((src_ip, dst_ip)), service_port, proto)

        with self._lock:
            flow = self.flows.get(key)
            if flow is None:
                # Identify the remote (non-local) endpoint for hostname lookup.
                remote = dst_ip if pkt.get("is_local") else src_ip
                if remote == src_ip and pkt.get("is_local"):
                    remote = dst_ip
                flow = {
                    "key": key,
                    "ip_a": src_ip,
                    "ip_b": dst_ip,
                    "service_port": service_port,
                    "protocol": proto,
                    "layer": layer,
                    "remote_ip": remote,
                    "hostname": "",
                    "start_ts": ts,
                    "last_ts": ts,
                    "total_bytes": 0,
                    "bytes_a_to_b": 0,
                    "bytes_b_to_a": 0,
                    "recent": deque(),  # (ts, size)
                }
                self.flows[key] = flow

            flow["last_ts"] = ts
            flow["total_bytes"] += size
            if src_ip == flow["ip_a"]:
                flow["bytes_a_to_b"] += size
            else:
                flow["bytes_b_to_a"] += size

            # Hostname: prefer packet metadata, else DNS cache on the remote IP.
            if pkt.get("hostname"):
                flow["hostname"] = pkt["hostname"]
            elif not flow["hostname"]:
                flow["hostname"] = hostname_cache.resolve(flow["remote_ip"]) or ""

            flow["recent"].append((ts, size))
            while flow["recent"] and flow["recent"][0][0] < ts - SPEED_WINDOW:
                flow["recent"].popleft()

    def get_flows(self, limit=25):
        """Return active flows as display-ready dicts, busiest first."""
        now = time.time()
        with self._lock:
            # Retire idle flows.
            expired = [k for k, f in self.flows.items() if now - f["last_ts"] > FLOW_TIMEOUT]
            for k in expired:
                self.flows.pop(k, None)
            records = list(self.flows.values())

        result = []
        for f in records:
            window = max(SPEED_WINDOW, now - f["start_ts"])
            recent_bytes = sum(s for _, s in f["recent"])
            current_mbps = round((recent_bytes * 8) / (window * 1_000_000), 2)
            duration = int(now - f["start_ts"])
            bytes_remote = max(f["bytes_a_to_b"], f["bytes_b_to_a"])
            bytes_local = min(f["bytes_a_to_b"], f["bytes_b_to_a"])
            flow_type = _flow_type(f["hostname"], f["layer"], bytes_remote, bytes_local, f["total_bytes"])
            result.append({
                "hostname": f["hostname"] or f["remote_ip"],
                "src_ip": f["ip_a"],
                "dst_ip": f["ip_b"],
                "remote_ip": f["remote_ip"],
                "protocol": f["layer"] or f["protocol"],
                "service_port": f["service_port"],
                "type": flow_type,
                "duration": duration,
                "current_mbps": current_mbps,
                "total_bytes": f["total_bytes"],
            })
        result.sort(key=lambda r: r["current_mbps"], reverse=True)
        return result[:limit]


# Shared instance used by the capture pipeline.
flow_tracker = FlowTracker()
