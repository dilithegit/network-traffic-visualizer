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

# Real-Time Socket.IO batching (req 9). Packets are accumulated and pushed to
# clients as a single `packet_batch` event instead of one emit per packet. This
# keeps the UI smooth and the server light under heavy capture rates.
SOCKET_BATCH_SIZE = 25             # Flush once this many packets are queued
SOCKET_BATCH_INTERVAL = 0.2        # ...or at least this often (seconds)

# How often (seconds) the statistics broadcaster pushes an update to clients.
SOCKET_STATS_INTERVAL = 2

# Packet inspection preview (req 7). Raw payload is capped before being sent to
# the browser to avoid bloating the Socket.IO frame.
PAYLOAD_PREVIEW_BYTES = 512

# Bandwidth Monitoring (network-wide)
BANDWIDTH_THRESHOLD_MBPS = 50      # Alert when total throughput exceeds this
BANDWIDTH_WINDOW_SECONDS = 5       # Rolling window for bandwidth calculation
HIGH_TRAFFIC_IP_THRESHOLD = 10     # Per-IP Mbps that flags a high consumer

# Per-IP Traffic Spike Detection
PACKET_THRESHOLD = 150             # Packets/sec from a single IP before a spike
BANDWIDTH_SPIKE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB/s per IP before a spike
SPIKE_ALERT_COOLDOWN = 5           # Min seconds between repeated alerts for one IP

# ---------------------------------------------------------------------------
# Intelligent (dynamic) spike detection (req 3)
# ---------------------------------------------------------------------------
# Sensitivity presets. Each maps a z-score threshold, the minimum number of
# baseline samples required before we trust the mean/stddev, and the size of
# the sliding baseline window (seconds) used to learn "normal" behaviour.
SPIKE_SENSITIVITY = "medium"       # low | medium | high
SPIKE_SENSITIVITY_PRESETS = {
    "low":    {"zscore": 5.0, "min_samples": 20, "window": 120},
    "medium": {"zscore": 3.5, "min_samples": 12, "window": 90},
    "high":   {"zscore": 2.0, "min_samples": 8,  "window": 60},
}
# Severity is escalated automatically based on how many sigmas the observed
# rate is from the learned baseline.
SPIKE_SEVERITY_CRITICAL_Z = 4.0    # >= this z -> CRITICAL
SPIKE_SEVERITY_WARNING_Z = 2.5     # >= this z -> WARNING (else INFO)
SPIKE_BASELINE_DECAY = 0.9         # EMA factor for the running mean/stddev

# ---------------------------------------------------------------------------
# DNS correlation & hostname caching (req 1)
# ---------------------------------------------------------------------------
DNS_CORRELATION_ENABLED = True     # map resolved names to IPs for SNI fallback
HOSTNAME_CACHE_TTL = 600           # seconds an IP->host mapping stays valid

# ---------------------------------------------------------------------------
# Dynamic protocol distribution (req 6)
# ---------------------------------------------------------------------------
PROTOCOL_INACTIVE_TIMEOUT = 45     # remove a protocol not seen for this long (s)

# ---------------------------------------------------------------------------
# Interface health (req 5)
# ---------------------------------------------------------------------------
INTERFACE_IDLE_WARNING_SECONDS = 8 # emit a warning if a running iface is silent

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "packets.db")

# Logging
LOG_LEVEL = "INFO"
