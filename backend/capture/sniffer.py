from scapy.all import sniff, get_if_list, conf
import time
from collections import deque
from backend.database.db import save_packets_batch

# Real-time buffer for the Flask API (Phase 1 & 2)
traffic_data = deque(maxlen=1000)

# Temporary list to hold packets before writing to DB (Phase 3)
db_batch = []

def get_active_interface():
    """Dynamically finds the best network interface to sniff on."""
    print("[*] Scanning for available network interfaces...")
    try:
        iface = conf.iface
        if iface:
            return iface
    except Exception:
        pass

    interfaces = get_if_list()
    for i in interfaces:
        if "Loopback" not in i and "Virtual" not in i:
            return i
    return None

def process_packet(packet):
    global db_batch
    
    if packet.haslayer("IP"):
        ip_layer = packet["IP"]
        src = ip_layer.src
        dst = ip_layer.dst
        proto = ip_layer.proto
        size = len(packet)
        
        # Identify Ports for TCP/UDP
        src_port = 0
        dst_port = 0
        if packet.haslayer("TCP"):
            src_port = packet["TCP"].sport
            dst_port = packet["TCP"].dport
        elif packet.haslayer("UDP"):
            src_port = packet["UDP"].sport
            dst_port = packet["UDP"].dport

        proto_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
        proto_name = proto_map.get(proto, f"OTHER({proto})")

        # Skip non-critical traffic to save space/memory
        if proto not in [6, 17, 1]:
            return

        entry = {
            "src_ip": src,
            "dst_ip": dst,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": proto_name,
            "size": size,
            "timestamp": time.time(),
            "is_local": src.startswith(("192.168", "10.", "172.16")) 
        }

        # Update the live buffer for the Frontend
        traffic_data.append(entry)
        
        # Add to batch for Database Persistence
        db_batch.append(entry)

        # Write to SQLite every 50 packets to optimize Disk I/O
        if len(db_batch) >= 50:
            try:
                save_packets_batch(db_batch)
                db_batch = [] # Reset batch after successful save
            except Exception as e:
                print(f"[!] Database Write Error: {e}")

def start_sniffer():
    target_iface = get_active_interface()
    
    if not target_iface:
        print("[!] FATAL: No suitable network interface found.")
        return
    
    try:
        print(f"[*] Sniffer active on: {target_iface}")
        # store=False is critical to prevent Scapy from consuming all RAM
        sniff(
            iface=target_iface,
            prn=process_packet,
            store=False
        )
    except Exception as e:
        print(f"[!] Sniffer ERROR: {e}")
        print("[*] Hint: Ensure you are running as Administrator (sudo).")

if __name__ == "__main__":
    # If running this file directly, it will start sniffing without the API
    start_sniffer()