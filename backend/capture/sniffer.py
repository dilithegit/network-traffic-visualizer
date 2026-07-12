"""Packet capture engine for NETSENTRY.

This module owns the live packet buffer and the background capture thread.
It is responsible for:

* Selecting a network interface (delegated to ``interface_manager``).
* Parsing raw Scapy packets into a normalized dictionary.
* Feeding each packet to the URL extractor and spike detector.
* Emitting ``new_packet`` events through the alert notifier (Socket.IO).
* Batching packets into the SQLite database for persistence.

The capture loop is non-blocking: it runs in a daemon thread and reads
packets with ``store=False`` so Scapy never buffers the whole stream in RAM.
"""

import time
import threading
from collections import deque
from datetime import datetime

from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw, DNS

from config import (
    SNIFFER_BUFFER_SIZE,
    SNIFFER_BATCH_SIZE,
    PACKET_THRESHOLD,
    BANDWIDTH_SPIKE_THRESHOLD_BYTES,
)
from capture.interface_manager import (
    set_active_interface,
    get_active_interface_name,
)
from capture.parser import should_capture_packet
from database.db import save_packets_batch
from alerts.notifier import alert_notifier
from analysis.url_extractor import url_extractor
from analysis.spike_detector import spike_detector

logger = __import__("logging").getLogger(__name__)

# Real-time rolling buffer consumed by the REST API and Socket.IO clients.
traffic_data = deque(maxlen=SNIFFER_BUFFER_SIZE)

# Internal capture state.
_capture_running = False
_capture_thread = None
_db_batch = []
_packet_id = 0
_id_lock = threading.Lock()


def _next_packet_id():
    """Return a monotonically increasing id used as a stable React key."""
    global _packet_id
    with _id_lock:
        _packet_id += 1
        return _packet_id


def get_active_interface():
    """Return the interface currently selected for capture."""
    return get_active_interface()


def is_capture_running():
    """Return True while the capture thread is active."""
    return _capture_running


def stop_capture():
    """Signal the capture thread to stop and wait for it to exit."""
    global _capture_running, _capture_thread
    _capture_running = False
    thread = _capture_thread
    if thread and thread.is_alive():
        thread.join(timeout=3)
    _capture_thread = None
    logger.info("[*] Capture stopped")
    return True


def start_capture(interface=None):
    """Start (or restart) capture on the given interface.

    If ``interface`` is ``None`` the default interface is selected. Any
    previously running capture is stopped first so switching interfaces never
    leaves two sniffers competing for the same buffer.
    """
    global _capture_running, _capture_thread

    if interface:
        set_active_interface(interface)

    # Resolve to the real Scapy name; the friendly name is only for display.
    target = get_active_interface_name()
    if not target:
        logger.error("[!] No suitable network interface found")
        _capture_running = False
        return False

    # Restart cleanly: stop any existing loop before spawning a new thread.
    if _capture_running and _capture_thread and _capture_thread.is_alive():
        _capture_running = False
        _capture_thread.join(timeout=3)

    _capture_running = True
    _capture_thread = threading.Thread(
        target=_capture_loop, args=(target,), daemon=True
    )
    _capture_thread.start()
    logger.info("[*] Capture started on interface: %s", target)
    return True


def _capture_loop(interface):
    """Blocking loop that drives Scapy's sniffer until stopped."""
    global _capture_running
    try:
        while _capture_running:
            sniff(
                iface=interface,
                prn=process_packet,
                store=False,
                stop_filter=lambda _: not _capture_running,
                timeout=1,
            )
    except Exception as exc:  # pragma: no cover - depends on OS/permissions
        logger.error("[!] Sniffer error on %s: %s", interface, exc)
        logger.error("[*] Hint: run with administrator / root privileges")
    finally:
        _capture_running = False


# ---------------------------------------------------------------------------
# Packet parsing
# ---------------------------------------------------------------------------

_PORT_LABELS = {
    21: "FTP", 22: "SSH", 25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    80: "HTTP", 110: "POP3", 123: "NTP", 143: "IMAP", 443: "HTTPS",
    587: "SMTP", 993: "IMAPS", 995: "POP3S",
}


def _port_label(src_port, dst_port):
    port = dst_port or src_port
    return _PORT_LABELS.get(port, "")


def _tcp_flags(packet):
    flags = packet[TCP].flags
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
    return names


def process_packet(packet):
    """Parse a packet, update shared state and fan out to analysis modules."""
    if not should_capture_packet(packet):
        return

    ip = packet[IP]
    src = ip.src
    dst = ip.dst
    proto = ip.proto
    size = len(packet)

    src_port = dst_port = 0
    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    proto_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
    proto_name = proto_map.get(proto, f"OTHER({proto})")

    info = ""
    layer = proto_name

    if packet.haslayer(TCP):
        flags = _tcp_flags(packet)
        port_label = _port_label(src_port, dst_port)
        if flags:
            info = ", ".join(flags)
        elif port_label:
            info = port_label
        else:
            info = "TCP"

        if dst_port in {80, 443} or src_port in {80, 443}:
            layer = "HTTP" if (dst_port == 80 or src_port == 80) else "HTTPS"
        elif port_label:
            layer = port_label

        if packet.haslayer(Raw):
            try:
                payload = bytes(packet[Raw].load)
                text = payload.decode("latin-1", errors="ignore")
                if "HTTP/" in text or text.startswith(
                    ("GET ", "POST ", "HEAD ", "PUT ", "DELETE ")
                ):
                    info = "HTTP " + text.splitlines()[0].strip()
                elif "CONNECT " in text:
                    info = "HTTPS CONNECT"
                elif payload[:3] == b"\x16\x03":
                    info = "TLS ClientHello"
            except Exception:
                pass

    elif packet.haslayer(UDP):
        port_label = _port_label(src_port, dst_port)
        # QUIC rides on UDP/443 for most modern services.
        if {src_port, dst_port} & {443}:
            layer = "QUIC"
            info = "QUIC"
        if dst_port == 53 or src_port == 53:
            layer = "DNS"
            if packet.haslayer(DNS):
                dns = packet[DNS]
                qname = ""
                if dns.qdcount and dns.qd:
                    try:
                        qname = dns.qd.qname.decode("utf-8", errors="ignore")
                    except Exception:
                        qname = str(dns.qd.qname)
                info = f"DNS query: {qname}" if qname else "DNS"
            else:
                info = "DNS"
        elif port_label:
            info = port_label
            layer = port_label
        elif layer != "QUIC":
            info = "UDP"
    elif packet.haslayer(ICMP):
        info = "ICMP"

    current_time = time.time()
    entry = {
        "id": _next_packet_id(),
        "src_ip": src,
        "dst_ip": dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": proto_name,
        "size": size,
        "timestamp": current_time,
        "time": datetime.now().strftime("%H:%M:%S"),
        "is_local": src.startswith(("192.168", "10.", "172.16", "127.")),
        "info": info,
        "layer": layer,
    }

    # 1. Update the live buffer that feeds the REST API + Socket.IO clients.
    traffic_data.append(entry)

    # 2. Emit a lightweight packet event for the live log (capped client-side).
    alert_notifier.publish_packet(entry)

    # 3. Extract HTTP URLs / HTTPS SNI (emits new_url on a match).
    try:
        url_extractor.process_packet(packet)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("URL extraction failed: %s", exc)

    # 4. Run per-IP spike detection (emits spike_detected / new_alert).
    try:
        spike_detector.process_packet(entry)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Spike detection failed: %s", exc)

    # 5. Batch packets into SQLite for historical persistence.
    _db_batch.append(entry)
    if len(_db_batch) >= SNIFFER_BATCH_SIZE:
        _flush_db_batch()


def _flush_db_batch():
    global _db_batch
    if not _db_batch:
        return
    batch = _db_batch
    _db_batch = []
    try:
        save_packets_batch([
            {
                "src_ip": p["src_ip"],
                "dst_ip": p["dst_ip"],
                "src_port": p["src_port"],
                "dst_port": p["dst_port"],
                "protocol": p["protocol"],
                "size": p["size"],
                "timestamp": p["timestamp"],
                "is_local": p["is_local"],
            }
            for p in batch
        ])
    except Exception as exc:
        logger.error("[!] Database write error: %s", exc)


def get_packet_count():
    """Number of packets currently held in the live buffer."""
    return len(traffic_data)


def flush():
    """Flush any pending database batch (call on shutdown)."""
    _flush_db_batch()
