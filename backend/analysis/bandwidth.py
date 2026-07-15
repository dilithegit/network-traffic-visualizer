"""
Bandwidth Monitoring Module
Tracks and analyzes network bandwidth usage with per-IP metrics
"""

from collections import defaultdict, deque
import time
from capture.sniffer import traffic_data
from config import BANDWIDTH_THRESHOLD_MBPS, BANDWIDTH_WINDOW_SECONDS, HIGH_TRAFFIC_IP_THRESHOLD

class BandwidthMonitor:
    """Monitor bandwidth usage and identify high consumers"""
    
    def __init__(self, window_seconds=BANDWIDTH_WINDOW_SECONDS):
        self.window_seconds = window_seconds
        self.ip_bandwidth = defaultdict(deque)  # IP -> deque of (timestamp, bytes)
        self.total_bandwidth_history = deque(maxlen=100)  # Last 100 measurements
    
    def update(self):
        """Update bandwidth statistics from current traffic data"""
        current_time = time.time()
        data_snapshot = list(traffic_data)
        
        if not data_snapshot:
            return
        
        # Calculate total bandwidth in current window
        window_start = current_time - self.window_seconds
        window_packets = [p for p in data_snapshot if p['timestamp'] >= window_start]
        
        total_bytes = sum(p['size'] for p in window_packets)
        total_mbps = (total_bytes * 8) / (1024 * 1024 * self.window_seconds)
        total_bps = (total_bytes * 8) / self.window_seconds
        total_pps = len(window_packets) / self.window_seconds
        
        self.total_bandwidth_history.append({
            'timestamp': current_time,
            'mbps': total_mbps,
            'bps': total_bps,
            'pps': total_pps,
        })
        
        # Calculate per-IP bandwidth
        ip_bytes = defaultdict(int)
        for packet in window_packets:
            ip_bytes[packet['src_ip']] += packet['size']
        
        for ip, bytes_sent in ip_bytes.items():
            mbps = (bytes_sent * 8) / (1024 * 1024 * self.window_seconds)
            self.ip_bandwidth[ip].append({
                'timestamp': current_time,
                'mbps': mbps
            })
    
    def get_bandwidth_status(self):
        """
        Returns comprehensive bandwidth analysis
        """
        if not self.total_bandwidth_history:
            return {
                'total_mbps': 0,
                'total_bps': 0,
                'total_pps': 0,
                'avg_mbps': 0,
                'peak_mbps': 0,
                'avg_bps': 0,
                'peak_bps': 0,
                'avg_pps': 0,
                'peak_pps': 0,
                'is_high': False,
                'high_consumers': [],
            }
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Get recent measurements
        recent_measurements = [m for m in self.total_bandwidth_history 
                              if m['timestamp'] >= window_start]
        
        if not recent_measurements:
            total_mbps = total_bps = total_pps = 0
            avg_mbps = avg_bps = avg_pps = 0
        else:
            last = recent_measurements[-1]
            total_mbps = last['mbps']
            total_bps = last.get('bps', 0)
            total_pps = last.get('pps', 0)
            avg_mbps = sum(m['mbps'] for m in recent_measurements) / len(recent_measurements)
            avg_bps = sum(m.get('bps', 0) for m in recent_measurements) / len(recent_measurements)
            avg_pps = sum(m.get('pps', 0) for m in recent_measurements) / len(recent_measurements)
        
        peak_mbps = max((m['mbps'] for m in self.total_bandwidth_history), default=0)
        peak_bps = max((m.get('bps', 0) for m in self.total_bandwidth_history), default=0)
        peak_pps = max((m.get('pps', 0) for m in self.total_bandwidth_history), default=0)
        
        # Identify high bandwidth consumers
        high_consumers = []
        for ip, bandwidth_history in self.ip_bandwidth.items():
            recent_ip_data = [b for b in bandwidth_history 
                             if b['timestamp'] >= window_start]
            if recent_ip_data:
                ip_mbps = recent_ip_data[-1]['mbps']
                if ip_mbps > HIGH_TRAFFIC_IP_THRESHOLD:
                    high_consumers.append({
                        'ip': ip,
                        'mbps': round(ip_mbps, 2),
                        'severity': 'CRITICAL' if ip_mbps > BANDWIDTH_THRESHOLD_MBPS else 'WARNING'
                    })
        
        # Sort by bandwidth
        high_consumers.sort(key=lambda x: x['mbps'], reverse=True)
        
        return {
            'total_mbps': round(total_mbps, 2),
            'total_bps': round(total_bps, 2),
            'total_pps': round(total_pps, 2),
            'avg_mbps': round(avg_mbps, 2),
            'peak_mbps': round(peak_mbps, 2),
            'avg_bps': round(avg_bps, 2),
            'peak_bps': round(peak_bps, 2),
            'avg_pps': round(avg_pps, 2),
            'peak_pps': round(peak_pps, 2),
            'is_high': total_mbps > BANDWIDTH_THRESHOLD_MBPS,
            'threshold_mbps': BANDWIDTH_THRESHOLD_MBPS,
            'high_consumers': high_consumers[:5],  # Top 5 consumers
            'consumer_count': len(high_consumers)
        }


# Global instance
bandwidth_monitor = BandwidthMonitor()
