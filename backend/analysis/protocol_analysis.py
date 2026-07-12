"""Protocol analysis helpers for packet inspection."""


def get_port_label(src_port, dst_port):
    """Return a friendly label for common service ports."""
    port = dst_port or src_port
    labels = {
        21: "FTP",
        22: "SSH",
        25: "SMTP",
        53: "DNS",
        67: "DHCP",
        68: "DHCP",
        80: "HTTP",
        110: "POP3",
        123: "NTP",
        143: "IMAP",
        443: "HTTPS",
        587: "SMTP",
        993: "IMAPS",
        995: "POP3S",
    }
    return labels.get(port, "")
