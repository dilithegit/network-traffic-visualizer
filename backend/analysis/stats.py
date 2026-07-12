"""Aggregated traffic statistics for NETSENTRY.

Builds the payload pushed to clients on every ``statistics_update`` event and
served by the ``/stats`` REST endpoint. It reads the live packet buffer plus
the bandwidth monitor and spike detector so a single response describes the
whole network at a glance.
"""

import socket
import time
from collections import Counter

from capture.sniffer import traffic_data, get_packet_count
from capture.interface_manager import get_active_interface_display
from analysis.bandwidth import bandwidth_monitor
from analysis.spike_detector import spike_detector
from config import PACKET_THRESHOLD, BANDWIDTH_SPIKE_THRESHOLD_BYTES


def get_traffic_stats():
    """Return a comprehensive snapshot of current network activity."""
    data_snapshot = list(traffic_data)

    if not data_snapshot:
        return _empty_stats()

    protocols = Counter()
    sources = Counter()
    layers = Counter()
    total_bytes = 0

    for packet in data_snapshot:
        protocols[packet["protocol"]] += 1
        layers[packet.get("layer", packet["protocol"])] += 1
        sources[packet["src_ip"]] += 1
        total_bytes += packet.get("size", 0)

    # Duration for BPS is derived from the buffer span (capped buffer).
    start_t = data_snapshot[0]["timestamp"]
    end_t = data_snapshot[-1]["timestamp"]
    duration = max(end_t - start_t, 1)

    bandwidth_monitor.update()
    bandwidth_status = bandwidth_monitor.get_bandwidth_status()

    return {
        "hostname": socket.gethostname(),
        "active_interface": get_active_interface_display(),
        "capture_active": any(p is not None for p in [get_active_interface_display()]),
        "metrics": {
            "total_packets": len(data_snapshot),
            "total_bytes": total_bytes,
            "buffered_packets": get_packet_count(),
            "kbps": round((total_bytes * 8) / (duration * 1024), 2),
            "mbps": round((total_bytes * 8) / (duration * 1024 * 1024), 2),
            "avg_packet_size": round(total_bytes / len(data_snapshot), 2),
        },
        "protocol_distribution": dict(protocols),
        "layer_distribution": dict(layers),
        "top_talkers": [
            {"ip": ip, "count": count} for ip, count in sources.most_common(5)
        ],
        "active_ports": sorted(
            {p["dst_port"] for p in data_snapshot if p["dst_port"] > 0}
        )[:10],
        "bandwidth": bandwidth_status,
        "suspicious_hosts": spike_detector.get_suspicious_hosts(),
        "thresholds": {
            "packet_threshold": PACKET_THRESHOLD,
            "bandwidth_threshold_bytes": BANDWIDTH_SPIKE_THRESHOLD_BYTES,
        },
    }


def _empty_stats():
    return {
        "hostname": socket.gethostname(),
        "active_interface": get_active_interface_display(),
        "capture_active": False,
        "metrics": {
            "total_packets": 0,
            "total_bytes": 0,
            "buffered_packets": 0,
            "kbps": 0,
            "mbps": 0,
            "avg_packet_size": 0,
        },
        "protocol_distribution": {},
        "layer_distribution": {},
        "top_talkers": [],
        "active_ports": [],
        "bandwidth": {
            "total_mbps": 0,
            "avg_mbps": 0,
            "peak_mbps": 0,
            "is_high": False,
            "high_consumers": [],
        },
        "suspicious_hosts": [],
        "thresholds": {
            "packet_threshold": PACKET_THRESHOLD,
            "bandwidth_threshold_bytes": BANDWIDTH_SPIKE_THRESHOLD_BYTES,
        },
    }
