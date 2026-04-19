from scapy.all import sniff

traffic_data = []

def process_packet(packet):
    if packet.haslayer("IP"):
        src = packet["IP"].src
        dst = packet["IP"].dst
        proto = packet["IP"].proto
        size = len(packet)

        # Map protocol number to name
        proto_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
        proto_name = proto_map.get(proto, f"OTHER({proto})")

        entry = {
            "src": src,
            "dst": dst,
            "protocol": proto_name,
            "size": size
        }

        traffic_data.append(entry)
        print(f"{src} → {dst} | {proto_name} | {size} bytes")


def start_sniffer():
    try:
        print("Starting capture on interface...")
        sniff(
            iface=r"\Device\NPF_{1F664E68-AA37-4A1E-A105-6A13DD114D69}",
            prn=process_packet,
            store=False,
            count=0
        )
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    start_sniffer()