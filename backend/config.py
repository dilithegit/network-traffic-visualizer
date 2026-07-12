"""Configuration settings for NETSENTRY (formerly PacketMon).

All tunable values live here so the rest of the codebase can stay free of
hardcoded constants. Thresholds for spike detection and bandwidth monitoring
are defined once and reused by the analysis modules.
"""

import os

# API / Socket.IO Configuration
API_HOST = "127.0.0.1"
API_PORT = 5000
API_DEBUG = False

# Sniffer Configuration
SNIFFER_BUFFER_SIZE = 500          # Max packets kept in the live in-memory buffer
SNIFFER_BATCH_SIZE = 50            # Packets to batch before a single DB write

# How often (seconds) the statistics broadcaster pushes an update to clients.
SOCKET_STATS_INTERVAL = 2

# Bandwidth Monitoring (network-wide)
BANDWIDTH_THRESHOLD_MBPS = 50      # Alert when total throughput exceeds this
BANDWIDTH_WINDOW_SECONDS = 5       # Rolling window for bandwidth calculation
HIGH_TRAFFIC_IP_THRESHOLD = 10     # Per-IP Mbps that flags a high consumer

# Per-IP Traffic Spike Detection
PACKET_THRESHOLD = 150             # Packets/sec from a single IP before a spike
BANDWIDTH_SPIKE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB/s per IP before a spike
SPIKE_ALERT_COOLDOWN = 5           # Min seconds between repeated alerts for one IP

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "packets.db")

# Logging
LOG_LEVEL = "INFO"
