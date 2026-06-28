"""
Packet Parser Utility
Provides helpers for parsing network packets
"""

from scapy.all import IP, TCP, UDP, ICMP

def get_protocol_name(protocol_number):
    """
    Convert protocol number to name
    
    Args:
        protocol_number: IP protocol number
        
    Returns:
        Protocol name as string
    """
    protocol_map = {
        6: "TCP",
        17: "UDP",
        1: "ICMP",
        2: "IGMP",
        41: "IPv6",
        47: "GRE",
    }
    return protocol_map.get(protocol_number, f"OTHER({protocol_number})")

def is_local_ip(ip_address):
    """
    Check if IP is in local network ranges
    
    Args:
        ip_address: IP address as string
        
    Returns:
        True if local, False otherwise
    """
    local_ranges = [
        "192.168.",
        "10.",
        "172.16.",
        "127.",
    ]
    return any(ip_address.startswith(prefix) for prefix in local_ranges)

def extract_ports(packet):
    """
    Extract source and destination ports from packet
    
    Args:
        packet: Scapy packet
        
    Returns:
        Tuple of (src_port, dst_port)
    """
    src_port = 0
    dst_port = 0
    
    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
    
    return src_port, dst_port

def should_capture_packet(packet):
    """
    Determine if packet should be captured
    
    Args:
        packet: Scapy packet
        
    Returns:
        True if packet should be captured, False otherwise
    """
    if not packet.haslayer(IP):
        return False
    
    protocol = packet[IP].proto
    # Only capture TCP, UDP, ICMP
    return protocol in [6, 17, 1]
