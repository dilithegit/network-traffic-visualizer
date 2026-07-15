"""Aggregated traffic statistics for NETSENTRY (req 4, 5, 6).

Builds the payload pushed on every ``statistics_update`` event and served by
the ``/stats`` REST endpoint. It reads the live packet buffer plus the
bandwidth monitor and spike detector so a single response describes the whole
network at a glance, including real-time bandwidth (current/peak/average),
packets & bytes per second, active connections/devices, and a dynamic protocol
distribution that auto-discovers protocols and retires inactive ones.
"""

import socket
import time
from collections import Counter

from capture.sniffer import (
    traffic_data,
    get_packet_count,
    is_capture_running,
    get_last_packet_time,
)
from capture.interface_manager import get_active_interface_display
from analysis.bandwidth import bandwidth_monitor
from analysis.spike_detector import spike_detector
from config import (
    PACKET_THRESHOLD,
    BANDWIDTH_SPIKE_THRESHOLD_BYTES,
    PROTOCOL_INACTIVE_TIMEOUT,
    INTERFACE_IDLE_WARNING_SECONDS,
)

# Persistent, per-layer last-seen timestamps so the protocol chart can keep a
# recently-active protocol visible briefly (and retire it after the timeout).
_protocol_last_seen = {}
_protocol_last_count = {}


def get_traffic_stats():
    """Return a comprehensive snapshot of current network activity."""
    data_snapshot = list(traffic_data)

    if not data_snapshot:
        return _empty_stats()

    protocols = Counter()
    layers = Counter()
    sources = Counter()
    flows = set()
    devices = set()
    total_bytes = 0

    for packet in data_snapshot:
        protocols[packet["protocol"]] += 1
        layer = packet.get("layer", packet["protocol"])
        layers[layer] += 1
        sources[packet["src_ip"]] += 1
        total_bytes += packet.get("size", 0)
        if packet.get("src_ip") and packet.get("dst_ip"):
            flows.add((
                packet["src_ip"], packet["dst_ip"],
                packet.get("dst_port", 0), packet.get("protocol", ""),
            ))
            devices.add(packet["src_ip"])
            devices.add(packet["dst_ip"])

    # Update persistent protocol activity (req 6).
    now = time.time()
    for layer, count in layers.items():
        _protocol_last_seen[layer] = now
        _protocol_last_count[layer] = count
    active_layers = {}
    for layer, seen in _protocol_last_seen.items():
        if now - seen <= PROTOCOL_INACTIVE_TIMEOUT:
            active_layers[layer] = _protocol_last_count.get(layer, 0)
        else:
            _protocol_last_seen.pop(layer, None)
            _protocol_last_count.pop(layer, None)

    start_t = data_snapshot[0]["timestamp"]
    end_t = data_snapshot[-1]["timestamp"]
    duration = max(end_t - start_t, 1)

    bandwidth_monitor.update()
    bandwidth_status = bandwidth_monitor.get_bandwidth_status()

    idle_warning = False
    if is_capture_running():
        last_pkt = get_last_packet_time()
        idle_warning = last_pkt > 0 and (now - last_pkt) > INTERFACE_IDLE_WARNING_SECONDS

    return {
        "hostname": socket.gethostname(),
        "active_interface": get_active_interface_display(),
        "capture_active": is_capture_running(),
        "idle_warning": idle_warning,
        "metrics": {
            "total_packets": len(data_snapshot),
            "total_bytes": total_bytes,
            "buffered_packets": get_packet_count(),
            "kbps": round((total_bytes * 8) / (duration * 1024), 2),
            "mbps": round((total_bytes * 8) / (duration * 1024 * 1024), 2),
            "avg_packet_size": round(total_bytes / len(data_snapshot), 2),
            "current_bps": bandwidth_status.get("total_bps", 0),
            "current_pps": bandwidth_status.get("total_pps", 0),
            "avg_pps": bandwidth_status.get("avg_pps", 0),
            "peak_pps": bandwidth_status.get("peak_pps", 0),
            "avg_bps": bandwidth_status.get("avg_bps", 0),
            "peak_bps": bandwidth_status.get("peak_bps", 0),
            "active_connections": len(flows),
            "active_devices": len(devices),
        },
        "protocol_distribution": dict(protocols),
        "layer_distribution": active_layers,
        "top_talkers": [
            {"ip": ip, "count": count} for ip, count in sources.most_common(5)
        ],
        "active_ports": sorted(
            {p["dst_port"] for p in data_snapshot if p["dst_port"] > 0}
        )[:10],
        "bandwidth": bandwidth_status,
        "suspicious_hosts": spike_detector.get_suspicious_hosts(),
        "spike_sensitivity": spike_detector.get_sensitivity(),
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
        "idle_warning": False,
        "metrics": {
            "total_packets": 0,
            "total_bytes": 0,
            "buffered_packets": 0,
            "kbps": 0,
            "mbps": 0,
            "avg_packet_size": 0,
            "current_bps": 0,
            "current_pps": 0,
            "avg_pps": 0,
            "peak_pps": 0,
            "avg_bps": 0,
            "peak_bps": 0,
            "active_connections": 0,
            "active_devices": 0,
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
        "spike_sensitivity": spike_detector.get_sensitivity(),
        "thresholds": {
            "packet_threshold": PACKET_THRESHOLD,
            "bandwidth_threshold_bytes": BANDWIDTH_SPIKE_THRESHOLD_BYTES,
        },
    }
