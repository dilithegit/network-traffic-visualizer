import logging
from collections import deque
from datetime import datetime

from scapy.all import IP, TCP, UDP, Raw
from scapy.layers.http import HTTPRequest
from scapy.layers.tls.all import TLS
from scapy.layers.tls.extensions import TLS_Ext_ServerName

logger = logging.getLogger(__name__)


class URLExtractor:
    """Extract HTTP URLs and HTTPS SNI values from captured packets."""

    def __init__(self, notifier=None):
        self.notifier = notifier
        self.recent_urls = deque(maxlen=100)

    def process_packet(self, packet):
        if not packet.haslayer(IP):
            logger.debug("Skipping packet without IP layer")
            return None

        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst

        if packet.haslayer(HTTPRequest):
            request = packet[HTTPRequest]
            host = request.Host.decode("utf-8", errors="ignore") if request.Host else None
            path = request.Path.decode("utf-8", errors="ignore") if request.Path else "/"
            if host:
                url = self._build_url(host, path)
                event = self._build_event(src_ip, dst_ip, "HTTP", url, "HTTP")
                logger.info("HTTP URL detected: %s", url)
                self._publish(event)
                return event

        if packet.haslayer(Raw):
            payload = bytes(packet[Raw].load)
            if self._is_http_payload(payload):
                host, path = self._extract_http_details(payload)
                if host:
                    url = self._build_url(host, path)
                    event = self._build_event(src_ip, dst_ip, "HTTP", url, "HTTP")
                    logger.info("HTTP URL detected from payload: %s", url)
                    self._publish(event)
                    return event

        if self._is_tls_candidate(packet):
            sni = self._extract_sni(packet)
            if sni:
                event = self._build_event(src_ip, dst_ip, "HTTPS", sni, "TLS")
                logger.info("HTTPS SNI detected: %s", sni)
                self._publish(event)
                return event

        logger.debug("Packet skipped for URL analysis: %s -> %s", src_ip, dst_ip)
        return None

    def _is_tls_candidate(self, packet):
        if packet.haslayer(TLS):
            return True
        if packet.haslayer(TCP) and (packet[TCP].dport == 443 or packet[TCP].sport == 443):
            return True
        if packet.haslayer(UDP) and (packet[UDP].dport == 443 or packet[UDP].sport == 443):
            return True
        return False

    def _extract_sni(self, packet):
        try:
            if packet.haslayer(TLS_Ext_ServerName):
                tls_ext = packet.getlayer(TLS_Ext_ServerName)
                server_names = getattr(tls_ext, "servernames", None)
                if server_names:
                    return self._parse_server_name(server_names[0])

            if packet.haslayer(TLS):
                tls_layer = packet.getlayer(TLS)
                sni = self._extract_sni_from_tls_layer(tls_layer)
                if sni:
                    return sni

            if packet.haslayer(Raw):
                payload = bytes(packet[Raw].load)
                if payload:
                    sni = self._extract_sni_from_payload(payload)
                    if sni:
                        return sni
        except Exception as exc:
            logger.debug("TLS handshake SNI detection failed: %s", exc)
        return None

    def _extract_sni_from_tls_layer(self, tls_layer):
        try:
            for msg in getattr(tls_layer, "msg", []):
                for ext in getattr(msg, "ext", []) or getattr(msg, "exts", []):
                    if isinstance(ext, TLS_Ext_ServerName):
                        return self._parse_server_name(ext.servernames[0])
        except Exception as exc:
            logger.debug("TLS layer SNI parse failed: %s", exc)
        return None

    def _parse_server_name(self, server_name):
        name = getattr(server_name, "servername", None)
        if name:
            if isinstance(name, bytes):
                return name.decode("utf-8", errors="ignore")
            return str(name)
        return None

    def _extract_sni_from_payload(self, payload):
        if len(payload) < 5 or payload[0] != 0x16:
            return None

        try:
            record_length = int.from_bytes(payload[3:5], "big")
            if len(payload) < 5 + record_length:
                return None

            handshake_type = payload[5]
            if handshake_type != 0x01:
                return None

            handshake_length = int.from_bytes(payload[6:9], "big")
            if len(payload) < 9 + handshake_length:
                return None

            pos = 9
            pos += 2
            pos += 32
            if pos + 1 > len(payload):
                return None

            session_id_len = payload[pos]
            pos += 1 + session_id_len
            if pos + 2 > len(payload):
                return None

            cipher_suites_len = int.from_bytes(payload[pos:pos + 2], "big")
            pos += 2 + cipher_suites_len
            if pos + 1 > len(payload):
                return None

            compression_methods_len = payload[pos]
            pos += 1 + compression_methods_len
            if pos + 2 > len(payload):
                return None

            extensions_length = int.from_bytes(payload[pos:pos + 2], "big")
            pos += 2
            end = pos + extensions_length
            while pos + 4 <= end and pos + 4 <= len(payload):
                ext_type = int.from_bytes(payload[pos:pos + 2], "big")
                ext_len = int.from_bytes(payload[pos + 2:pos + 4], "big")
                pos += 4
                if ext_type == 0:
                    if pos + 2 > len(payload):
                        return None
                    server_name_list_len = int.from_bytes(payload[pos:pos + 2], "big")
                    pos += 2
                    name_end = pos + server_name_list_len
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
            logger.debug("Error parsing SNI from payload: %s", exc)
        return None

    def _is_http_payload(self, payload):
        text = payload.decode("latin-1", errors="ignore")
        return "HTTP/" in text or text.startswith(("GET ", "POST ", "HEAD ", "PUT ", "DELETE "))

    def _extract_http_details(self, payload):
        text = payload.decode("latin-1", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        host = None
        path = "/"

        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
            elif line.startswith(("GET ", "POST ", "HEAD ", "PUT ", "DELETE ")):
                parts = line.split(" ")
                if len(parts) >= 2:
                    path = parts[1]

        return host, path

    def _build_url(self, host, path):
        if not host:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{host}{path}"

    def _build_event(self, src_ip, dst_ip, protocol, url, transport):
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": protocol,
            "url": url,
            "transport": transport,
        }

    def _publish(self, event):
        self.recent_urls.append(event)
        if self.notifier:
            self.notifier.publish_url(event)

    def get_recent_urls(self):
        return list(self.recent_urls)


from alerts.notifier import alert_notifier  # noqa: E402  (avoid import cycle)

# Shared extractor instance wired to the live notifier.
url_extractor = URLExtractor(notifier=alert_notifier)
