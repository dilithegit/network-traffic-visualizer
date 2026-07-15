"""Packet capture engine for NETSENTRY (req 1-9).

Owns the live packet buffer and the background capture thread. Responsibilities:

* Select an interface (delegated to ``interface_manager``).
* Classify raw Scapy packets into a normalized dictionary (``capture.parser``).
* Enrich each packet with MAC addresses, TTL, TCP flags, a hex/ASCII payload
  preview, DNS/TLS/HTTP details and a resolved destination hostname (DNS
  correlation + SNI fallback from ``analysis.url_extractor`` and
  ``analysis.hostname_cache``).
* Batch parsed packets and push them to clients as a single ``packet_batch``
  Socket.IO event (req 9) instead of one emit per packet.
* Feed URL extraction and the dynamic spike detector.
* Detect inactive interfaces and expose ``last_packet_time`` so the broadcaster
  can warn the UI (req 5).
* Batch packets into SQLite for persistence.

The capture loop runs in a daemon thread and reads with ``store=False`` so
Scapy never buffers the whole stream in RAM.
"""

import time
import threading
from collections import deque
from datetime import datetime

from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, Raw, DNS

from config import (
    SNIFFER_BUFFER_SIZE,
    SNIFFER_BATCH_SIZE,
    SOCKET_BATCH_SIZE,
    SOCKET_BATCH_INTERVAL,
    PACKET_THRESHOLD,
    BANDWIDTH_SPIKE_THRESHOLD_BYTES,
    PAYLOAD_PREVIEW_BYTES,
)
from capture.interface_manager import (
    set_active_interface,
    get_active_interface_name,
)
from capture.parser import classify, should_capture_packet
from database.db import save_packets_batch
from alerts.notifier import alert_notifier
from analysis.url_extractor import url_extractor
from analysis.spike_detector import spike_detector
from analysis.hostname_cache import hostname_cache
from analysis.flow_tracker import flow_tracker

logger = __import__("logging").getLogger(__name__)

# Real-time rolling buffer consumed by the REST API and Socket.IO clients.
traffic_data = deque(maxlen=SNIFFER_BUFFER_SIZE)

# Internal capture state.
_capture_running = False
_capture_thread = None
_db_batch = []
_packet_id = 0
_id_lock = threading.Lock()

# Socket.IO batching state (req 9): packets are queued and flushed together.
_socket_batch = []
_socket_batch_lock = threading.Lock()
_last_socket_flush = 0.0

# Idle watchdog (req 5): timestamp of the most recent captured packet.
last_packet_time = 0.0


def _next_packet_id():
    """Return a monotonically increasing id used as a stable React key."""
    global _packet_id
    with _id_lock:
        _packet_id += 1
        return _packet_id


def get_active_interface():
    """Return the interface currently selected for capture."""
    return get_active_interface_name()


def is_capture_running():
    """Return True while the capture thread is active."""
    return _capture_running


def get_last_packet_time():
    """Epoch seconds of the most recent captured packet (0 if never)."""
    return last_packet_time


def stop_capture():
    """Signal the capture thread to stop and wait for it to exit."""
    global _capture_running, _capture_thread
    _capture_running = False
    thread = _capture_thread
    if thread and thread.is_alive():
        thread.join(timeout=3)
    _capture_thread = None
    _flush_socket_batch()
    logger.info("[*] Capture stopped")
    return True


def start_capture(interface=None):
    """Start (or restart) capture on the given interface.

    Any previously running capture is stopped first so switching interfaces
    never leaves two sniffers competing for the same buffer.
    """
    global _capture_running, _capture_thread

    if interface:
        set_active_interface(interface)

    target = get_active_interface_name()
    if not target:
        logger.error("[!] No suitable network interface found")
        _capture_running = False
        return False

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
    global _capture_running, last_packet_time
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
        _flush_socket_batch()


# ---------------------------------------------------------------------------
# Packet parsing + enrichment
# ---------------------------------------------------------------------------

def _payload_preview(packet):
    """Return (hex_string, ascii_string) for the first bytes of the payload."""
    if not packet.haslayer(Raw):
        return "", ""
    try:
        raw = bytes(packet[Raw].load)[:PAYLOAD_PREVIEW_BYTES]
    except Exception:
        return "", ""
    hex_lines = []
    ascii_chars = []
    for i in range(0, len(raw), 16):
        chunk = raw[i:i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        hex_lines.append(hex_part)
        ascii_chars.append(ascii_part)
    return "\n".join(hex_lines), "".join(ascii_chars)


def _dns_info(packet):
    """Extract a compact DNS summary (query name, response answers)."""
    if not packet.haslayer(DNS):
        return None
    dns = packet[DNS]
    info = {
        "type": "response" if getattr(dns, "qr", 0) == 1 else "query",
        "query": None,
        "answer_count": getattr(dns, "ancount", 0),
        "answers": [],
    }
    try:
        qd = getattr(dns, "qd", None)
        if qd:
            info["query"] = qd.qname.decode("utf-8", "ignore") if isinstance(qd.qname, bytes) else str(qd.qname)
    except Exception:
        pass
    # Cache the mapping for SNI-less HTTPS correlation (req 1).
    hostname_cache.learn_from_dns(dns)
    try:
        an = getattr(dns, "an", None)
        if an:
            records = an if isinstance(an, list) else [an]
            for rr in records:
                rdata = getattr(rr, "rdata", None)
                if isinstance(rdata, str):
                    info["answers"].append(rdata)
    except Exception:
        pass
    return info


def process_packet(packet):
    """Parse, enrich and fan out a single packet."""
    global last_packet_time
    if not should_capture_packet(packet):
        return

    base = classify(packet)
    now = time.time()
    last_packet_time = now

    src_ip = base["src_ip"]
    dst_ip = base["dst_ip"]
    src_port = base["src_port"]
    dst_port = base["dst_port"]

    # DNS info (also feeds the hostname cache).
    dns = _dns_info(packet)

    # HTTP / HTTPS / TLS analysis (structured for the inspector).
    analyzed = url_extractor.analyze(packet) if base["has_ip"] else {}
    url = analyzed.get("url")
    hostname = analyzed.get("hostname")
    tls = analyzed.get("tls")
    http = analyzed.get("http")

    # Destination hostname fallback: SNI -> DNS cache -> IP.
    if not hostname and dst_ip:
        hostname = hostname_cache.resolve(dst_ip) or hostname_cache.resolve(src_ip)

    # Emit a URL-feed event when we have something meaningful.
    if url:
        url_extractor.publish_result(analyzed, src_ip, dst_ip, src_port, dst_port)

    # HTTP details from raw payload when scapy's http layer was absent.
    if not http and packet.haslayer(Raw):
        http = _raw_http_headers(packet)

    hex_str, ascii_str = _payload_preview(packet)

    entry = {
        "id": _next_packet_id(),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": base["protocol"],
        "layer": base["layer"],
        "size": base["size"],
        "timestamp": now,
        "time": datetime.now().strftime("%H:%M:%S"),
        "is_local": base["is_local"],
        "info": base["info"],
        "transport": base["transport"],
        "ip_version": base["ip_version"],
        "mac_src": base["mac_src"],
        "mac_dst": base["mac_dst"],
        "ttl": base["ttl"],
        "flags": base["flags"],
        "hostname": hostname or "",
        "url": url or "",
        "dns": dns,
        "tls": tls,
        "http": http,
        "payload_hex": hex_str,
        "payload_ascii": ascii_str,
    }

    traffic_data.append(entry)
    _queue_socket(entry)

    try:
        spike_detector.process_packet(entry)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Spike detection failed: %s", exc)

    try:
        flow_tracker.process_packet(entry)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Flow tracking failed: %s", exc)

    _db_batch.append(entry)
    if len(_db_batch) >= SNIFFER_BATCH_SIZE:
        _flush_db_batch()


def _raw_http_headers(packet):
    """Best-effort HTTP header extraction from a raw TCP payload."""
    try:
        raw = bytes(packet[Raw].load)
        text = raw.decode("latin-1", "ignore")
        if not ("HTTP/" in text or text.startswith(("GET ", "POST ", "HEAD ", "PUT "))):
            return None
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        host = None
        path = "/"
        method = "GET"
        headers = []
        seen = False
        for ln in lines:
            if ln.lower().startswith("host:"):
                host = ln.split(":", 1)[1].strip()
            elif ln.startswith(("GET ", "POST ", "HEAD ", "PUT ", "OPTIONS ")):
                parts = ln.split(" ")
                method = parts[0]
                if len(parts) >= 2:
                    path = parts[1]
                seen = True
            elif seen and ":" in ln:
                headers.append(ln)
        if not host:
            return None
        return {"method": method, "host": host, "path": path, "headers": headers}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Socket.IO batching (req 9)
# ---------------------------------------------------------------------------

def _queue_socket(entry):
    """Append an entry to the Socket.IO batch and flush when due."""
    global _last_socket_flush
    with _socket_batch_lock:
        _socket_batch.append(entry)
        due = (
            len(_socket_batch) >= SOCKET_BATCH_SIZE
            or (time.time() - _last_socket_flush) >= SOCKET_BATCH_INTERVAL
        )
        if due:
            _flush_socket_batch_locked()


def _flush_socket_batch():
    with _socket_batch_lock:
        _flush_socket_batch_locked()


def _flush_socket_batch_locked():
    """Emit queued packets as a single ``packet_batch`` event."""
    global _socket_batch, _last_socket_flush
    if not _socket_batch:
        return
    batch = _socket_batch
    _socket_batch = []
    _last_socket_flush = time.time()
    alert_notifier.publish_packet_batch(batch)


# ---------------------------------------------------------------------------
# Database batching
# ---------------------------------------------------------------------------

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
    _flush_socket_batch()
