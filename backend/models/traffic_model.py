"""
Traffic Data Model
Defines the structure of network traffic data
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class TrafficPacket:
    """Represents a single network packet"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    size: int
    timestamp: float
    is_local: bool
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'size': self.size,
            'timestamp': self.timestamp,
            'is_local': self.is_local,
        }

@dataclass
class BandwidthMetrics:
    """Bandwidth metrics for a time period"""
    total_mbps: float
    avg_mbps: float
    peak_mbps: float
    is_high: bool
    threshold_mbps: float
    high_consumers: list
    consumer_count: int

@dataclass
class TrafficStats:
    """Comprehensive traffic statistics"""
    total_packets: int
    total_bytes: int
    kbps: float
    mbps: float
    avg_packet_size: float
    protocol_distribution: dict
    top_talkers: list
    active_ports: list
    bandwidth: BandwidthMetrics
