"""URL & hostname extraction (req 1, 2).

Reconstructs full HTTP URLs (host + path) and extracts TLS Server Name
Indication (SNI) together with Client Hello metadata. Encrypted flows that
lack SNI fall back to the hostname cache (DNS correlation) so the destination
is shown as a name rather than an opaque "HTTPS" / empty value.

The public ``analyze()`` method returns a *structured* result so the sniffer
can embed HTTP/DNS/TLS detail in the per-packet inspector payload, while
``process_packet()`` still emits the legacy ``new_url`` feed event.
"""

import logging
from collections import deque
from datetime import datetime

from scapy.all import IP, IPv6, TCP, UDP, Raw, DNS
from scapy.layers.http import HTTPRequest
from scapy.layers.tls.all import TLS
from scapy.layers.tls.extensions import TLS_Ext_ServerName

from analysis.hostname_cache import hostname_cache

logger = logging.getLogger(__name__)


class URLExtractor:
    """Extract HTTP URLs, HTTPS SNI values and TLS Client Hello metadata."""

    def __init__(self, notifier=None):
        self.notifier = notifier
        self.recent_urls = deque(maxlen=100)

    # ------------------------------------------------------------------
    # Structured analysis (used by the sniffer for packet inspection)
    # ------------------------------------------------------------------
    def analyze(self, packet):
        """Return a dict with url / http / tls details, or empty dict.

        Result keys: ``url``, ``protocol`` ("HTTP"/"HTTPS"), ``transport``,
        ``hostname``, ``http`` ({method, host, path, headers}), ``tls``
        ({sni, version, cipher_suites, extensions}).
        """
        # Accept both IPv4 and IPv6; only non-IP packets (e.g. raw ARP) bail.
        if packet.haslayer(IP):
            ip_layer = packet[IP]
        elif packet.haslayer(IPv6):
            ip_layer = packet[IPv6]
        else:
            return {}

        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        src_port = dst_port = 0
        if packet.haslayer(TCP):
            src_port, dst_port = packet[TCP].sport, packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port, dst_port = packet[UDP].sport, packet[UDP].dport

        # 1) Native Scapy HTTP request (most reliable, keeps headers).
        if packet.haslayer(HTTPRequest):
            request = packet[HTTPRequest]
            host = request.Host.decode("utf-8", errors="ignore") if request.Host else None
            path = request.Path.decode("utf-8", errors="ignore") if request.Path else "/"
            method = request.Method.decode("utf-8", errors="ignore") if request.Method else "GET"
            if host:
                return {
                    "url": self._build_url(host, path),
                    "protocol": "HTTP",
                    "transport": "HTTP",
                    "hostname": host,
                    "http": {
                        "method": method,
                        "host": host,
                        "path": path,
                        "headers": self._http_headers(request),
                    },
                    "tls": None,
                }

        # 2) Raw HTTP payload (hand-rolled requests without the http layer).
        if packet.haslayer(Raw):
            payload = bytes(packet[Raw].load)
            if self._is_http_payload(payload):
                host, path, method, headers = self._extract_http_details(payload)
                if host:
                    return {
                        "url": self._build_url(host, path),
                        "protocol": "HTTP",
                        "transport": "HTTP",
                        "hostname": host,
                        "http": {
                            "method": method,
                            "host": host,
                            "path": path,
                            "headers": headers,
                        },
                        "tls": None,
                    }

        # 3) TLS / HTTPS: SNI + Client Hello metadata.
        if self._is_tls_candidate(packet):
            tls_info = self._extract_tls(packet)
            if tls_info:
                sni = tls_info.get("sni")
                hostname = sni or hostname_cache.resolve(dst_ip) or hostname_cache.resolve(src_ip)
                return {
                    "url": hostname or None,
                    "protocol": "HTTPS",
                    "transport": "TLS",
                    "hostname": hostname,
                    "http": None,
                    "tls": tls_info,
                }

        return {}

    def _http_headers(self, request):
        headers = []
        try:
            fields = getattr(request, "fields", {})
            for key, value in fields.items():
                if key in ("Method", "Path", "Host"):
                    continue
                headers.append(f"{key}: {value}")
        except Exception:
            pass
        return headers

    # ------------------------------------------------------------------
    # Legacy feed emission (new_url)
    # ------------------------------------------------------------------
    def process_packet(self, packet):
        result = self.analyze(packet)
        if not result:
            logger.debug("Packet skipped for URL analysis: %s -> %s",
                         packet[IP].src if packet.haslayer(IP) else "?",
                         packet[IP].dst if packet.haslayer(IP) else "?")
            return None

        ip_layer = packet[IP] if packet.haslayer(IP) else (packet[IPv6] if packet.haslayer(IPv6) else None)
        src_ip = ip_layer.src if ip_layer else "?"
        dst_ip = ip_layer.dst if ip_layer else "?"
        src_port = dst_port = 0
        if packet.haslayer(TCP):
            src_port, dst_port = packet[TCP].sport, packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port, dst_port = packet[UDP].sport, packet[UDP].dport

        event = self._build_event(
            src_ip, dst_ip, src_port, dst_port,
            result.get("protocol"), result.get("url"), result.get("hostname"),
            result.get("transport"),
        )
        logger.info("%s detected: %s", result.get("protocol"), result.get("url"))
        self._publish(event)
        return event

    # ------------------------------------------------------------------
    # TLS internals
    # ------------------------------------------------------------------
    def _is_tls_candidate(self, packet):
        if packet.haslayer(TLS):
            return True
        if packet.haslayer(TCP) and (packet[TCP].dport == 443 or packet[TCP].sport == 443):
            return True
        if packet.haslayer(UDP) and (packet[UDP].dport == 443 or packet[UDP].sport == 443):
            return True
        return False

    def _extract_tls(self, packet):
        tls_info = {
            "sni": None,
            "version": None,
            "cipher_suites": None,
            "extensions": None,
            "handshake_type": "Client Hello",
            "has_record": False,
        }
        try:
            # Preferred: structured Client Hello from scapy's TLS layer.
            if packet.haslayer(TLS_Ext_ServerName):
                ext = packet.getlayer(TLS_Ext_ServerName)
                names = getattr(ext, "servernames", None)
                if names:
                    tls_info["sni"] = self._parse_server_name(names[0])
            if packet.haslayer(TLS):
                tls_layer = packet.getlayer(TLS)
                self._enrich_from_tls_layer(tls_layer, tls_info)
            # Fallback: raw byte parsing of the Client Hello record.
            if packet.haslayer(Raw):
                payload = bytes(packet[Raw].load)
                if payload:
                    tls_info["has_record"] = payload[0] == 0x16
                    sni = self._extract_sni_from_payload(payload)
                    if sni and not tls_info["sni"]:
                        tls_info["sni"] = sni
        except Exception as exc:
            logger.debug("TLS analysis failed: %s", exc)
        # Keep TLS info when we have a real handshake record (so an SNI-less
        # Client Hello still resolves to a hostname via the DNS cache) but
        # ignore empty 443 segments (ACKs) to avoid feed spam.
        if not (tls_info["sni"] or tls_info["version"] or tls_info["has_record"]):
            return None
        return tls_info

    def _enrich_from_tls_layer(self, tls_layer, tls_info):
        try:
            for msg in getattr(tls_layer, "msg", []) or []:
                version = getattr(msg, "version", None)
                if version:
                    tls_info["version"] = getattr(version, "ssl_version", None) or str(version)
                suites = getattr(msg, "cipher_suites", None)
                if suites is not None:
                    tls_info["cipher_suites"] = len(suites) if hasattr(suites, "__len__") else None
                for ext in getattr(msg, "ext", []) or getattr(msg, "exts", []):
                    if isinstance(ext, TLS_Ext_ServerName):
                        tls_info["sni"] = self._parse_server_name(ext.servernames[0])
        except Exception as exc:
            logger.debug("TLS layer parse failed: %s", exc)

    def _parse_server_name(self, server_name):
        name = getattr(server_name, "servername", None)
        if name:
            return name.decode("utf-8", errors="ignore") if isinstance(name, bytes) else str(name)
        return None

    def _extract_sni_from_payload(self, payload):
        if len(payload) < 5 or payload[0] != 0x16:
            return None
        try:
            record_length = int.from_bytes(payload[3:5], "big")
            if len(payload) < 5 + record_length:
                return None
            if payload[5] != 0x01:  # Client Hello
                return None
            handshake_length = int.from_bytes(payload[6:9], "big")
            if len(payload) < 9 + handshake_length:
                return None
            pos = 9
            pos += 2  # client version
            pos += 32  # random
            if pos + 1 > len(payload):
                return None
            pos += 1 + payload[pos]  # session id
            if pos + 2 > len(payload):
                return None
            cipher_suites_len = int.from_bytes(payload[pos:pos + 2], "big")
            pos += 2 + cipher_suites_len
            if pos + 1 > len(payload):
                return None
            pos += 1 + payload[pos]  # compression methods
            if pos + 2 > len(payload):
                return None
            extensions_length = int.from_bytes(payload[pos:pos + 2], "big")
            pos += 2
            end = pos + extensions_length
            while pos + 4 <= end and pos + 4 <= len(payload):
                ext_type = int.from_bytes(payload[pos:pos + 2], "big")
                ext_len = int.from_bytes(payload[pos + 2:pos + 4], "big")
                pos += 4
                if ext_type == 0:  # SNI
                    if pos + 2 > len(payload):
                        return None
                    name_list_len = int.from_bytes(payload[pos:pos + 2], "big")
                    pos += 2
                    name_end = pos + name_list_len
                    while pos + 3 <= name_end and pos + 3 <= len(payload):
                        name_type = payload[pos]
                        name_len = int.from_bytes(payload[pos + 1:pos + 3], "big")
                        pos += 3
                        if pos + name_len > len(payload) or pos + name_len > name_end:
                            return None
                        if name_type == 0:
                            return payload[pos:pos + name_len].decode("utf-8", errors="ignore")
                        pos += name_len
                    return None
                pos += ext_len
        except Exception as exc:
            logger.debug("SNI payload parse error: %s", exc)
        return None

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------
    def _is_http_payload(self, payload):
        text = payload.decode("latin-1", errors="ignore")
        return "HTTP/" in text or text.startswith(("GET ", "POST ", "HEAD ", "PUT ", "DELETE "))

    def _extract_http_details(self, payload):
        text = payload.decode("latin-1", errors="ignore")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        host = None
        path = "/"
        method = "GET"
        headers = []
        request_line_seen = False
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
            elif line.startswith(("GET ", "POST ", "HEAD ", "PUT ", "DELETE ", "OPTIONS ")):
                parts = line.split(" ")
                method = parts[0]
                if len(parts) >= 2:
                    path = parts[1]
                request_line_seen = True
            elif request_line_seen and ":" in line:
                headers.append(line)
        return host, path, method, headers

    def _build_url(self, host, path):
        if not host:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{host}{path}"

    def _build_event(self, src_ip, dst_ip, src_port, dst_port, protocol, url, hostname, transport):
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "url": url,
            "hostname": hostname,
            "transport": transport,
        }

    def publish_result(self, result, src_ip, dst_ip, src_port, dst_port):
        """Build + emit a ``new_url`` event from an ``analyze()`` result."""
        if not result or not result.get("url"):
            return None
        event = self._build_event(
            src_ip, dst_ip, src_port, dst_port,
            result.get("protocol"), result.get("url"), result.get("hostname"),
            result.get("transport"),
        )
        self._publish(event)
        return event

    def _publish(self, event):
        self.recent_urls.append(event)
        if self.notifier:
            self.notifier.publish_url(event)

    def get_recent_urls(self):
        return list(self.recent_urls)


from alerts.notifier import alert_notifier  # noqa: E402  (avoid import cycle)

# Shared extractor instance wired to the live notifier.
url_extractor = URLExtractor(notifier=alert_notifier)
