from scapy.all import sniff, get_if_list, conf
import time
from collections import deque
from database.db import save_packets_batch
from config import SNIFFER_BUFFER_SIZE, SNIFFER_BATCH_SIZE

# Real-time buffer for the Flask API (Phase 1 & 2)
traffic_data = deque(maxlen=SNIFFER_BUFFER_SIZE)

# Temporary list to hold packets before writing to DB (Phase 3)
db_batch = []

# Reset counter every 10 minutes
packet_count_since_reset = 0
last_count_reset = time.time()

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
    global db_batch, packet_count_since_reset, last_count_reset
    
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

        info = ""
        layer = proto_name

        if packet.haslayer("TCP"):
            tcp_flags = packet["TCP"].flags
            flag_names = []
            if tcp_flags & 0x02:
                flag_names.append("SYN")
            if tcp_flags & 0x10:
                flag_names.append("ACK")
            if tcp_flags & 0x01:
                flag_names.append("FIN")
            if tcp_flags & 0x04:
                flag_names.append("RST")
            if tcp_flags & 0x08:
                flag_names.append("PSH")
            if tcp_flags & 0x20:
                flag_names.append("URG")
            info = ",".join(flag_names) if flag_names else "TCP"
            if dst_port in {80, 443} or src_port in {80, 443}:
                layer = "HTTP"
        elif packet.haslayer("UDP"):
            if dst_port == 53 or src_port == 53:
                info = "DNS"
                layer = "DNS"
            else:
                info = "UDP"
        elif packet.haslayer("ICMP"):
            info = "ICMP"
        else:
            info = proto_name

        current_time = time.time()
        global packet_count_since_reset, last_count_reset
        if current_time - last_count_reset >= 600:
            packet_count_since_reset = 0
            last_count_reset = current_time

        packet_count_since_reset += 1

        entry = {
            "src_ip": src,
            "dst_ip": dst,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": proto_name,
            "size": size,
            "timestamp": current_time,
            "is_local": src.startswith(("192.168", "10.", "172.16")),
            "info": info,
            "layer": layer,
            "packet_age": current_time,
        }

        # Update the live buffer for the Frontend
        traffic_data.append(entry)
        
        # Add to batch for Database Persistence
        db_batch.append(entry)

        # Write to SQLite every N packets to optimize Disk I/O
        if len(db_batch) >= SNIFFER_BATCH_SIZE:
            try:
                save_packets_batch(db_batch)
                db_batch = []  # Reset batch after successful save
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

def get_packet_count_since_reset():
    """Return the packet count since the last 10-minute reset."""
    return packet_count_since_reset

if __name__ == "__main__":
    # If running this file directly, it will start sniffing without the API
    start_sniffer()