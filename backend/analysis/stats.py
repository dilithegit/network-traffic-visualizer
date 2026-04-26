from collections import Counter
from backend.capture.sniffer import traffic_data

def get_traffic_stats():
    data_snapshot = list(traffic_data)
    
    if not data_snapshot:
        return {
            "total_packets": 0,
            "total_bytes": 0,
            "bps": 0,
            "protocol_distribution": {},
            "top_talkers": []
        }

    protocols = Counter()
    sources = Counter()
    total_bytes = 0
    
    # Calculate duration for BPS (Bytes Per Second)
    start_t = data_snapshot[0]['timestamp']
    end_t = data_snapshot[-1]['timestamp']
    duration = max(end_t - start_t, 1) # Ensure no division by zero

    for packet in data_snapshot:
        protocols[packet["protocol"]] += 1
        sources[packet["src_ip"]] += 1
        total_bytes += packet.get("size", 0)

    return {
        "metrics": {
            "total_packets": len(data_snapshot),
            "total_bytes": total_bytes,
            "kbps": round((total_bytes * 8) / (duration * 1024), 2), # Kilobits per second
            "avg_packet_size": round(total_bytes / len(data_snapshot), 2),
        },
        "protocol_distribution": dict(protocols),
        "top_talkers": [{"ip": ip, "count": count} for ip, count in sources.most_common(5)],
        "active_ports": list(set([p['dst_port'] for p in data_snapshot if p['dst_port'] > 0]))[:10]
    }