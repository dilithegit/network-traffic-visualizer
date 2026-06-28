import socket
import time
from collections import Counter
from capture.sniffer import traffic_data, get_packet_count_since_reset

try:
    from .bandwidth import bandwidth_monitor
except ImportError:
    from analysis.bandwidth import bandwidth_monitor

def get_traffic_stats():
    """Get comprehensive traffic statistics"""
    data_snapshot = list(traffic_data)
    
    if not data_snapshot:
        return {
            "hostname": socket.gethostname(),
            "metrics": {
                "total_packets": 0,
                "total_bytes": 0,
                "kbps": 0,
                "mbps": 0,
                "avg_packet_size": 0,
                "packets_since_reset": 0,
            },
            "protocol_distribution": {},
            "top_talkers": [],
            "active_ports": [],
            "bandwidth": {
                "total_mbps": 0,
                "is_high": False,
                "high_consumers": []
            }
        }

    protocols = Counter()
    sources = Counter()
    total_bytes = 0
    current_time = time.time()
    window_start = current_time - 600
    window_packets = [pkt for pkt in data_snapshot if pkt['timestamp'] >= window_start]

    # Calculate duration for BPS (Bytes Per Second)
    start_t = window_packets[0]['timestamp'] if window_packets else data_snapshot[0]['timestamp']
    end_t = window_packets[-1]['timestamp'] if window_packets else data_snapshot[-1]['timestamp']
    duration = max(end_t - start_t, 1)  # Ensure no division by zero

    for packet in data_snapshot:
        protocols[packet["protocol"]] += 1
        sources[packet["src_ip"]] += 1
        total_bytes += packet.get("size", 0)

    # Update bandwidth monitor
    bandwidth_monitor.update()
    bandwidth_status = bandwidth_monitor.get_bandwidth_status()

    return {
        "hostname": socket.gethostname(),
        "metrics": {
            "total_packets": len(data_snapshot),
            "packets_since_reset": get_packet_count_since_reset(),
            "total_bytes": total_bytes,
            "kbps": round((total_bytes * 8) / (duration * 1024), 2),  # Kilobits per second
            "mbps": round((total_bytes * 8) / (duration * 1024 * 1024), 2),  # Megabits per second
            "avg_packet_size": round(total_bytes / len(data_snapshot), 2),
        },
        "protocol_distribution": dict(protocols),
        "top_talkers": [{"ip": ip, "count": count} for ip, count in sources.most_common(5)],
        "active_ports": list(set([p['dst_port'] for p in data_snapshot if p['dst_port'] > 0]))[:10],
        "bandwidth": bandwidth_status
    }