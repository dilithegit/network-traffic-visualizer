# Bandwidth Monitoring - Complete Feature Guide

## 🎯 Overview

The **Bandwidth Monitoring** system is a new feature added to CNS Project 1 that provides intelligent detection and alerting for excessive network bandwidth usage.

---

## 📊 What It Monitors

### 1. Network-Wide Bandwidth
- **Current Bandwidth:** Real-time Mbps consumption
- **Average Bandwidth:** Mean Mbps over monitoring window
- **Peak Bandwidth:** Maximum Mbps recorded
- **Status:** Alert if exceeds threshold

### 2. Per-IP Bandwidth Analysis
- Identifies which IP addresses consume the most bandwidth
- Severity classification (WARNING vs CRITICAL)
- Top 5 high-consuming IPs displayed
- Real-time monitoring with 5-second rolling window

---

## 🔧 How It Works

### Backend Implementation

**File:** `backend/analysis/bandwidth.py`

```python
class BandwidthMonitor:
    """
    Tracks bandwidth usage with:
    - Rolling 5-second window
    - Per-IP consumption tracking
    - Automatic threshold detection
    """
    
    def update(self):
        # Updates from latest traffic data
        
    def get_bandwidth_status(self):
        # Returns comprehensive bandwidth metrics
```

### Data Flow

```
Packets Captured
      ↓
Traffic Buffer (sniffer.py)
      ↓
Statistics Engine (stats.py)
      ↓
Bandwidth Monitor (bandwidth.py) ← NEW!
      ↓
API Response (/stats endpoint)
      ↓
Frontend Dashboard
```

---

## 📈 Configuration

### Default Settings
```python
# backend/config.py

# Network-wide threshold
BANDWIDTH_THRESHOLD_MBPS = 50

# Rolling window for calculation
BANDWIDTH_WINDOW_SECONDS = 5

# Per-IP threshold
HIGH_TRAFFIC_IP_THRESHOLD = 10
```

### Common Configurations

#### For Home Network (Lower Threshold)
```python
BANDWIDTH_THRESHOLD_MBPS = 20      # Alert at 20 Mbps
HIGH_TRAFFIC_IP_THRESHOLD = 5      # Per-IP limit 5 Mbps
BANDWIDTH_WINDOW_SECONDS = 3       # Faster response
```

#### For Corporate Network (Higher Threshold)
```python
BANDWIDTH_THRESHOLD_MBPS = 200     # Alert at 200 Mbps
HIGH_TRAFFIC_IP_THRESHOLD = 50     # Per-IP limit 50 Mbps
BANDWIDTH_WINDOW_SECONDS = 10      # Longer averaging
```

#### For Real-Time Sensitivity
```python
BANDWIDTH_WINDOW_SECONDS = 1       # 1-second window (very responsive)
```

---

## 📱 Frontend Display

### Bandwidth Card
```
┌─ Bandwidth Usage ─────────────┐
│                               │
│     12.5 Mbps                │
│                               │
│  Peak: 45.8 Mbps             │
└───────────────────────────────┘
```

### Alert Banner (When Exceeded)
```
⚠️ HIGH BANDWIDTH ALERT: 65.3 Mbps (Threshold: 50 Mbps)
```

### High Consumers List
```
🚨 High Bandwidth Consumers

192.168.1.100  →  8.5 Mbps (WARNING)
10.0.0.5       →  5.2 Mbps (WARNING)
```

### Bandwidth Chart
```
Bandwidth Usage (Mbps)
│
│    ╱╲
│   ╱  ╲    ╱─────
│  ╱    ╲  ╱
│─────────────────  Threshold Line
└─────────────────
Time →
```

---

## 🚨 Alert System

### Severity Levels

#### WARNING
- Single IP exceeds `HIGH_TRAFFIC_IP_THRESHOLD`
- But network overall is below threshold
- **Action:** Monitor the specific IP

#### CRITICAL
- Single IP exceeds network `BANDWIDTH_THRESHOLD_MBPS`
- **Action:** Immediate investigation recommended

### Alert Indicators

**Color Coding:**
- 🟢 Green: Normal (< Threshold)
- 🟡 Yellow: Warning (10-50% below threshold)
- 🔴 Red: Critical (> Threshold)

---

## 📊 API Response Format

### GET `/stats` Response

```json
{
  "bandwidth": {
    "total_mbps": 12.5,
    "avg_mbps": 11.2,
    "peak_mbps": 45.8,
    "is_high": false,
    "threshold_mbps": 50,
    "high_consumers": [
      {
        "ip": "192.168.1.100",
        "mbps": 8.5,
        "severity": "WARNING"
      }
    ],
    "consumer_count": 1
  }
}
```

### Fields Explanation

| Field | Description | Example |
|-------|-------------|---------|
| `total_mbps` | Current bandwidth (last 5 sec) | 12.5 |
| `avg_mbps` | Average over window | 11.2 |
| `peak_mbps` | Maximum recorded | 45.8 |
| `is_high` | Exceeds threshold? | false |
| `threshold_mbps` | Alert threshold | 50 |
| `high_consumers` | IPs over limit | Array |
| `consumer_count` | Count of high IPs | 1 |

---

## 🔍 Use Cases

### 1. Detect Bandwidth Hogging
Identify which device/IP is consuming excessive bandwidth.

```python
# In browser console
fetch('http://127.0.0.1:5000/stats')
  .then(r => r.json())
  .then(d => console.log(d.bandwidth.high_consumers))
```

### 2. Network Capacity Planning
Monitor peak bandwidth to plan network upgrades.

### 3. Security Monitoring
Detect unusual bandwidth consumption (potential data exfiltration).

### 4. QoS Implementation
Set alerts to trigger QoS rules when thresholds exceeded.

---

## 💾 Database Integration

### Stored Data

All packets are stored in SQLite with:
- Source/Destination IP
- Port numbers
- Protocol type
- Packet size (used for bandwidth calculation)
- Timestamp
- Local flag

### Query Example
```python
# backend/database/db.py

# Get high-bandwidth traffic
SELECT src_ip, SUM(size) as total_bytes
FROM packets
WHERE timestamp > datetime('now', '-5 minutes')
GROUP BY src_ip
ORDER BY total_bytes DESC
LIMIT 10
```

---

## 🎨 Customization Examples

### Example 1: Alert on Specific IP

**Requirement:** Alert when 192.168.1.50 uses > 5 Mbps

**Solution:**
1. Edit `backend/analysis/bandwidth.py`
2. Add custom logic in `get_bandwidth_status()`
3. Check for specific IP and add to alerts

```python
def get_bandwidth_status(self):
    # ... existing code ...
    
    # Custom check for specific IP
    specific_ip = "192.168.1.50"
    if specific_ip in self.ip_bandwidth:
        ip_mbps = # ... calculate ...
        if ip_mbps > 5:  # Custom threshold
            # Add special alert
            pass
```

### Example 2: Log High Bandwidth Events

**Requirement:** Save bandwidth alerts to log file

**Solution:**
```python
import logging

logger = logging.getLogger(__name__)

# In bandwidth.py
if total_mbps > BANDWIDTH_THRESHOLD_MBPS:
    logger.warning(f"HIGH BANDWIDTH: {total_mbps} Mbps")
```

### Example 3: Email Alerts

**Requirement:** Send email when bandwidth exceeds threshold

**Solution:** Add to app.py
```python
import smtplib

if bandwidth_status['is_high']:
    send_email_alert(bandwidth_status)
```

---

## 📈 Performance Metrics

### Calculation Efficiency

- **Time Window:** 5 seconds (configurable)
- **Update Frequency:** Every API call (2 sec default)
- **Per-IP Tracking:** O(n) where n = unique IPs
- **Memory Overhead:** ~1KB per IP tracked

### Example Load
- 1,000 packets/second
- 100 unique IPs
- ~100KB bandwidth history memory
- <1ms calculation time

---

## 🐛 Debugging

### Enable Detailed Logging

**In backend/app.py:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then check logs for bandwidth calculations
```

### Test Bandwidth Calculation
```bash
# Generate test traffic
# Linux: iperf or dd
# Windows: Get-Content largefile.bin | Out-Null

# Monitor in terminal
curl http://127.0.0.1:5000/stats | jq '.bandwidth'
```

---

## 🔄 Future Enhancements

Potential improvements:

1. **Historical Bandwidth Charts**
   - Store hourly/daily bandwidth peaks
   - Display trends over time

2. **Automated Actions**
   - Trigger QoS rules
   - Rate limiting
   - Blocking/Whitelisting

3. **Machine Learning**
   - Anomaly detection
   - Predictive alerts
   - Behavioral analysis

4. **Distributed Monitoring**
   - Multiple network segments
   - Gateway-level monitoring
   - Multi-site aggregation

---

## 📚 References

- **Config:** `backend/config.py`
- **Module:** `backend/analysis/bandwidth.py`
- **Integration:** `backend/analysis/stats.py`
- **Frontend:** `frontend/src/App.jsx` (bandwidth display)
- **API:** `backend/app.py` (/stats endpoint)

---

## ✅ Checklist for Deployment

- [ ] Set appropriate `BANDWIDTH_THRESHOLD_MBPS`
- [ ] Adjust `HIGH_TRAFFIC_IP_THRESHOLD` for your network
- [ ] Test alerts with synthetic traffic
- [ ] Configure email/logging if needed
- [ ] Document threshold rationale
- [ ] Train users on alert response
- [ ] Monitor false positives first week
- [ ] Refine thresholds based on baselines

---

**Happy bandwidth monitoring! 📊**
