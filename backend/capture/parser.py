"""
Packet Parser Utilities (req 1, 5, 6)

Helpers for classifying raw Scapy packets into a normalized structure. The
parser now understands far more than TCP/UDP/ICMP -- it recognises ARP, IPv6,
and a broad set of application protocols (DNS, DHCP, HTTP, HTTPS, TLS, SSH,
QUIC, ...). Classification is ``layer`` based: the value shown in charts,
tables and the timeline is the *highest* protocol we can infer, while
``protocol`` keeps the raw transport for filtering (``protocol == TCP``).
"""

from scapy.all import IP, IPv6, TCP, UDP, ICMP, ARP, Ether, Raw

# IP protocol number -> short name.
PROTO_MAP = {
    1: "ICMP",
    2: "IGMP",
    4: "IPv4",
    6: "TCP",
    17: "UDP",
    41: "IPv6",
    47: "GRE",
    50: "ESP",
    51: "AH",
    58: "ICMPv6",
}

# Friendly labels for the most common service ports. Used both for the
# protocol pie and for the per-packet info column.
PORT_LABELS = {
    20: "FTP",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    137: "NetBIOS",
    138: "NetBIOS",
    139: "NetBIOS",
    143: "IMAP",
    161: "SNMP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    587: "SMTP",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    3306: "MySQL",
    3389: "RDP",
    5432: "Postgres",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    9200: "Elastic",
}

# Protocols that ride explicitly on UDP/443 (and sometimes UDP/80).
QUIC_PORTS = {443, 80}


def get_protocol_name(protocol_number):
    """Convert an IP protocol number to its name."""
    return PROTO_MAP.get(protocol_number, f"OTHER({protocol_number})")


def is_local_ip(ip_address):
    """Return True when ``ip_address`` sits in a private / loopback range."""
    if not ip_address:
        return False
    local_ranges = ("192.168.", "10.", "172.16.", "172.17.", "172.18.",
                    "172.19.", "172.2", "172.3", "127.")
    return any(ip_address.startswith(prefix) for prefix in local_ranges)


def extract_ports(packet):
    """Extract (src_port, dst_port) for TCP/UDP packets, else (0, 0)."""
    src_port = dst_port = 0
    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
    return src_port, dst_port


def should_capture_packet(packet):
    """Decide whether a packet is interesting enough to process.

    We accept L3 packets (IPv4/IPv6), ARP (link-local resolution), and ICMPv6
    so the protocol chart can auto-discover the full protocol mix (req 6).
    """
    if packet.haslayer(ARP):
        return True
    if packet.haslayer(IP) or packet.haslayer(IPv6):
        return True
    return False


def tcp_flags(packet):
    """Return the list of human-readable TCP flag names set on the packet."""
    if not packet.haslayer(TCP):
        return []
    flags = int(packet[TCP].flags)
    names = []
    if flags & 0x02:
        names.append("SYN")
    if flags & 0x10:
        names.append("ACK")
    if flags & 0x01:
        names.append("FIN")
    if flags & 0x04:
        names.append("RST")
    if flags & 0x08:
        names.append("PSH")
    if flags & 0x20:
        names.append("URG")
    if flags & 0x40:
        names.append("ECE")
    if flags & 0x80:
        names.append("CWR")
    return names


def port_label(src_port, dst_port):
    """Return a friendly service label for the dominant port, if known."""
    port = dst_port or src_port
    return PORT_LABELS.get(port, "")


def _read_mac(packet):
    """Return (src_mac, dst_mac) from the Ethernet layer, or empty strings."""
    if packet.haslayer(Ether):
        eth = packet[Ether]
        return _mac_str(eth.src), _mac_str(eth.dst)
    return "", ""


def _mac_str(value):
    return value if isinstance(value, str) else (str(value) if value else "")


def classify(packet):
    """Return a normalized dict of common packet fields.

    Keys produced: ``protocol``, ``layer``, ``info``, ``transport``,
    ``src_port``, ``dst_port``, ``mac_src``, ``mac_dst``, ``ttl``,
    ``has_ip``, ``src_ip``, ``dst_ip``, ``size``, ``ip_version``,
    ``is_local``, ``flags``.
    """
    size = len(packet)
    mac_src, mac_dst = _read_mac(packet)
    src_port = dst_port = 0
    flags = []
    ttl = None
    info = ""
    transport = ""
    layer = "OTHER"

    # --- ARP (no IP layer) ---------------------------------------------
    if packet.haslayer(ARP):
        arp = packet[ARP]
        op = "request" if arp.op == 1 else "reply" if arp.op == 2 else str(arp.op)
        src_ip = _mac_str(getattr(arp, "psrc", ""))
        dst_ip = _mac_str(getattr(arp, "pdst", ""))
        return {
            "protocol": "ARP",
            "layer": "ARP",
            "info": f"ARP {op}: {src_ip} -> {dst_ip}",
            "transport": "arp",
            "src_port": 0,
            "dst_port": 0,
            "mac_src": mac_src,
            "mac_dst": mac_dst,
            "ttl": None,
            "has_ip": False,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "size": size,
            "ip_version": 4,
            "is_local": True,
            "flags": [],
        }

    # --- IPv4 / IPv6 ---------------------------------------------------
    ip_version = 6 if packet.haslayer(IPv6) else 4
    ip_layer = packet[IP] if ip_version == 4 else packet[IPv6]
    src_ip = _mac_str(ip_layer.src)
    dst_ip = _mac_str(ip_layer.dst)
    ttl = getattr(ip_layer, "ttl", None)
    if ip_layer is None:
        return {
            "protocol": "OTHER", "layer": "OTHER", "info": "",
            "transport": "", "src_port": 0, "dst_port": 0,
            "mac_src": mac_src, "mac_dst": mac_dst, "ttl": None,
            "has_ip": False, "src_ip": "", "dst_ip": "", "size": size,
            "ip_version": 4, "is_local": False, "flags": [],
        }

    proto_num = ip_layer.proto if ip_version == 4 else ip_layer.nh
    protocol = get_protocol_name(proto_num)

    if packet.haslayer(TCP):
        src_port, dst_port = extract_ports(packet)
        transport = "tcp"
        flags = tcp_flags(packet)
        label = port_label(src_port, dst_port)
        if flags:
            info = ", ".join(flags)
            layer = _layer_for_port(src_port, dst_port, label, transport)
        elif label:
            info = label
            layer = label
        else:
            info = "TCP"
            layer = "TCP"
    elif packet.haslayer(UDP):
        src_port, dst_port = extract_ports(packet)
        transport = "udp"
        label = port_label(src_port, dst_port)
        if {src_port, dst_port} & QUIC_PORTS:
            layer = "QUIC"
            info = "QUIC"
        elif dst_port == 53 or src_port == 53:
            layer = "DNS"
            info = "DNS"
        elif label:
            layer = label
            info = label
        else:
            layer = "UDP"
            info = "UDP"
    elif packet.haslayer(ICMP):
        transport = "icmp"
        layer = "ICMP"
        info = "ICMP"
        protocol = "ICMP"
    else:
        layer = protocol
        info = protocol

    return {
        "protocol": protocol,
        "layer": layer,
        "info": info,
        "transport": transport,
        "src_port": src_port,
        "dst_port": dst_port,
        "mac_src": mac_src,
        "mac_dst": mac_dst,
        "ttl": ttl,
        "has_ip": True,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "size": size,
        "ip_version": ip_version,
        "is_local": is_local_ip(src_ip),
        "flags": flags,
    }


def _layer_for_port(src_port, dst_port, label, transport):
    """Pick the most specific layer for a TCP packet based on its port."""
    if dst_port == 80 or src_port == 80:
        return "HTTP"
    if dst_port == 443 or src_port == 443:
        return "HTTPS"
    if label:
        return label
    return "TCP"
