"""Configuration settings for CNS Project 1"""

import os

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 5000
API_DEBUG = False

# Sniffer Configuration
SNIFFER_BUFFER_SIZE = 1000  # Max packets in real-time buffer
SNIFFER_BATCH_SIZE = 50     # Packets to batch before DB write

# Bandwidth Monitoring
BANDWIDTH_THRESHOLD_MBPS = 50      # Alert threshold in Mbps
BANDWIDTH_WINDOW_SECONDS = 5       # Rolling window for bandwidth calculation
HIGH_TRAFFIC_IP_THRESHOLD = 10     # Mbps per IP

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "packets.db")

# Logging
LOG_LEVEL = "INFO"
