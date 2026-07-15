import time
import unittest
from pathlib import Path
import sys

from scapy.all import IP, TCP, Raw
from scapy.layers.tls.handshake import TLSClientHello
from scapy.layers.tls.extensions import TLS_Ext_ServerName, ServerName

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.url_extractor import URLExtractor
from analysis.spike_detector import SpikeDetector


class AdvancedAnalysisTests(unittest.TestCase):
    def test_http_packet_extracts_full_url(self):
        extractor = URLExtractor()
        packet = IP(src="192.168.1.12", dst="142.250.190.14") / TCP(sport=12345, dport=80) / Raw(
            b"GET /watch?v=abc HTTP/1.1\r\nHost: www.youtube.com\r\n\r\n"
        )

        event = extractor.process_packet(packet)

        self.assertIsNotNone(event)
        self.assertEqual(event["protocol"], "HTTP")
        self.assertEqual(event["url"], "http://www.youtube.com/watch?v=abc")

    def test_https_packet_extracts_sni(self):
        extractor = URLExtractor()
        client_hello = TLSClientHello(ext=[TLS_Ext_ServerName(servernames=[ServerName(servername=b"example.com")])])
        payload = bytes(client_hello)
        record = b"\x16\x03\x03" + len(payload).to_bytes(2, "big") + payload
        packet = IP(src="192.168.1.12", dst="142.250.190.14") / TCP(sport=12345, dport=443) / Raw(record)

        event = extractor.process_packet(packet)

        self.assertIsNotNone(event)
        self.assertEqual(event["protocol"], "HTTPS")
        self.assertEqual(event["url"], "example.com")

    def test_spike_detector_emits_alert_for_high_volume(self):
        # Monkeypatch time so we can simulate several seconds of traffic and
        # build a statistical baseline before injecting a burst.
        import time as _time
        original_time = _time.time
        fake = {"t": 1000.0}
        _time.time = lambda: fake["t"]
        try:
            detector = SpikeDetector(
                packet_threshold=150,
                bandwidth_threshold_bytes_per_second=1000000,
                cooldown=0,
            )
            src = "192.168.1.12"
            # 15 seconds of modest ~10 pps baseline traffic.
            for sec in range(15):
                fake["t"] = 1000.0 + sec
                for _ in range(10):
                    detector.process_packet({"src_ip": src, "size": 500, "timestamp": fake["t"]})
            # Burst second: 300 packets, then advance to finalize the bucket.
            fake["t"] = 1000.0 + 15
            for _ in range(300):
                detector.process_packet({"src_ip": src, "size": 500, "timestamp": fake["t"]})
            fake["t"] = 1000.0 + 16
            detector.process_packet({"src_ip": src, "size": 500, "timestamp": fake["t"]})

            alerts = detector.get_recent_alerts()
            self.assertTrue(any(alert["src_ip"] == src for alert in alerts))
        finally:
            _time.time = original_time



if __name__ == "__main__":
    unittest.main()
