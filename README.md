# CNS Project 1 - Complete Network Traffic Analyzer & Bandwidth Monitor

## Overview

**PacketMon** is a professional-grade real-time network packet analyzer and bandwidth monitoring system. It captures live network traffic, analyzes protocols, and identifies high-bandwidth consumers with intelligent alerting.

### Key Features

✅ **Real-Time Packet Capture** - Live network sniffing using Scapy  
✅ **Bandwidth Monitoring** - Tracks total bandwidth and per-IP usage  
✅ **High Bandwidth Alerts** - Automatic detection of excessive bandwidth usage  
✅ **Protocol Analysis** - Breaks down traffic by TCP, UDP, ICMP, etc.  
✅ **Live Dashboard** - Beautiful, responsive web UI with charts and metrics  
✅ **Database Persistence** - SQLite storage for historical analysis  
✅ **RESTful API** - Clean API endpoints for frontend consumption  
✅ **Performance Optimized** - Batch processing, efficient buffering, indexed DB queries  

---

## Project Architecture

```
CNS Project 1/
├── backend/                    # Python Flask API & Packet Sniffer
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── capture/
│   │   ├── sniffer.py         # Packet capture engine (Scapy)
│   │   └── parser.py          # Packet parsing utilities
│   ├── analysis/
│   │   ├── stats.py           # Traffic statistics
│   │   └── bandwidth.py       # 🆕 Bandwidth monitoring & alerts
│   ├── database/
│   │   └── db.py              # SQLite database management
│   ├── models/
│   │   └── traffic_model.py   # Data models
│   └── routes/
│       └── api.py             # API routes
├── frontend/                   # React + Vite Dashboard
│   ├── src/
│   │   ├── App.jsx            # Main dashboard component
│   │   ├── main.jsx           # Entry point
│   │   ├── index.css          # Global styles
│   │   ├── components/
│   │   │   ├── AnalyticsPanel.jsx
│   │   │   ├── LogTable.jsx
│   │   │   ├── TrafficCharts.js
│   │   │   └── Navbar.jsx
│   │   └── assets/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── scripts/
│   ├── start_project.sh       # Linux/Mac startup script
│   └── start_project.bat      # Windows startup script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Requirements

### System Requirements
- **Python 3.8+**
- **Node.js 16+** (with npm)
- **Admin/Root privileges** for network packet capture

### Python Dependencies
```
Flask==3.0.0
Flask-CORS==4.0.0
scapy==2.5.0
```

### Node.js Dependencies
```
react: ^19.2.5
recharts: ^3.8.1  (Charts)
lucide-react: ^1.11.0  (Icons)
vite: ^8.0.10
```

---

## Installation & Setup

### 1. Clone or Extract Project
```bash
cd CNS\ Project\ 1
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option A: Using Startup Scripts

#### **Windows:**
```batch
scripts\start_project.bat
```

#### **Linux/Mac:**
```bash
chmod +x scripts/start_project.sh
sudo scripts/start_project.sh  # Run with sudo for full packet capture
```

### Option B: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application
- **Frontend Dashboard:** http://localhost:5173
- **Backend API:** http://127.0.0.1:5000

---

## API Endpoints

### `GET /`
Health check endpoint
```json
{
  "status": "CNS Project 1 Backend Running",
  "sniffer_active": true,
  "version": "1.1.0"
}
```

### `GET /traffic`
Get last 50 captured packets
```json
[
  {
    "src_ip": "192.168.1.100",
    "dst_ip": "8.8.8.8",
    "src_port": 54322,
    "dst_port": 443,
    "protocol": "TCP",
    "size": 512,
    "timestamp": 1688234567.123,
    "is_local": true
  }
]
```

### `GET /stats`
Get comprehensive traffic statistics
```json
{
  "metrics": {
    "total_packets": 1250,
    "total_bytes": 524288,
    "kbps": 512.5,
    "mbps": 0.5,
    "avg_packet_size": 419.4
  },
  "protocol_distribution": {
    "TCP": 800,
    "UDP": 300,
    "ICMP": 150
  },
  "top_talkers": [
    {"ip": "192.168.1.100", "count": 450},
    {"ip": "192.168.1.50", "count": 380}
  ],
  "active_ports": [80, 443, 53, 22, 3306],
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

---

## Configuration

Edit `backend/config.py` to customize settings:

```python
# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 5000

# Sniffer Configuration
SNIFFER_BUFFER_SIZE = 1000      # Max packets in memory
SNIFFER_BATCH_SIZE = 50         # Packets per DB write

# Bandwidth Monitoring (NEW!)
BANDWIDTH_THRESHOLD_MBPS = 50       # Alert when exceeded
BANDWIDTH_WINDOW_SECONDS = 5        # Rolling window for calculation
HIGH_TRAFFIC_IP_THRESHOLD = 10      # Per-IP alert threshold (Mbps)

# Database
DB_PATH = "backend/database/packets.db"
```

---

## Bandwidth Monitoring (NEW FEATURE)

### Overview
The bandwidth monitoring module tracks real-time network bandwidth usage and identifies high-consuming IPs.

### Features
- **Total Bandwidth Tracking:** Current, average, and peak Mbps
- **Per-IP Analysis:** Identify which IPs consume the most bandwidth
- **Intelligent Alerts:** Automatic detection of:
  - Network-wide high bandwidth (> `BANDWIDTH_THRESHOLD_MBPS`)
  - Per-IP high consumption (> `HIGH_TRAFFIC_IP_THRESHOLD`)
  - Severity levels: WARNING, CRITICAL

### Implementation Details

**File:** `backend/analysis/bandwidth.py`

```python
from bandwidth import bandwidth_monitor

# Update stats
bandwidth_monitor.update()

# Get bandwidth status
status = bandwidth_monitor.get_bandwidth_status()
# Returns:
# {
#   'total_mbps': 12.5,
#   'avg_mbps': 11.2,
#   'peak_mbps': 45.8,
#   'is_high': False,
#   'threshold_mbps': 50,
#   'high_consumers': [...],
#   'consumer_count': 1
# }
```

### Frontend Integration
- Real-time bandwidth chart (line graph showing Mbps over time)
- High bandwidth alert banner
- List of top bandwidth consumers
- Severity indicators (WARNING/CRITICAL)

---

## Key Optimizations

### Backend
1. **Efficient Packet Buffering** - Circular deque with configurable size
2. **Batch Database Writes** - 50 packets per transaction (reduces I/O)
3. **Protocol Filtering** - Only captures TCP, UDP, ICMP
4. **Database Indexing** - Fast queries on src_ip and timestamp
5. **Thread-based Sniffer** - Non-blocking network capture
6. **Window-based Bandwidth Calculation** - Efficient rolling window stats

### Frontend
1. **React State Management** - Efficient re-renders
2. **Parallel API Calls** - Concurrent traffic + stats fetching
3. **Chart Optimization** - Recharts with disabled animations
4. **Error Handling** - User-friendly error messages
5. **Responsive Design** - Works on all screen sizes

---

## Troubleshooting

### Issue: "No suitable network interface found"
**Solution:** Run with admin/root privileges
```bash
# Windows
# Run Command Prompt as Administrator

# Linux/Mac
sudo python backend/app.py
```

### Issue: "Address already in use"
**Solution:** Port 5000 is in use. Change in `config.py`:
```python
API_PORT = 5001  # Use different port
```

### Issue: Frontend cannot connect to backend
**Solution:** Check if backend is running:
```bash
curl http://127.0.0.1:5000/
```

### Issue: Slow performance / High CPU usage
**Solution:** Adjust buffer sizes in `config.py`:
```python
SNIFFER_BUFFER_SIZE = 500   # Reduce memory usage
SNIFFER_BATCH_SIZE = 100    # Batch more packets
```

---

## Development

### Adding New Features

**Backend:**
1. Edit relevant module in `backend/`
2. Test with API endpoints
3. Verify database persistence

**Frontend:**
1. Update components in `frontend/src/components/`
2. Add new routes in App.jsx
3. Test with React dev tools

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
# Creates dist/ folder for deployment
```

**Backend:**
- Currently development-ready
- For production: Use gunicorn instead of Flask dev server
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 app:app
  ```

---

## Database Schema

### packets table
```sql
CREATE TABLE packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_ip TEXT,
  dst_ip TEXT,
  src_port INTEGER,
  dst_port INTEGER,
  protocol TEXT,
  size INTEGER,
  timestamp REAL,
  is_local INTEGER
);

-- Indexes for fast queries
CREATE INDEX idx_src_ip ON packets(src_ip);
CREATE INDEX idx_timestamp ON packets(timestamp);
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Max Packets in Memory | 1,000 |
| DB Write Batch Size | 50 packets |
| API Update Interval | 2 seconds |
| Dashboard Refresh | 2 seconds |
| Bandwidth Window | 5 seconds (rolling) |
| High Consumers | Top 5 IPs |

---

## License & Usage
This project is provided as-is for network analysis and monitoring purposes. Ensure compliance with your network's policies and local laws when capturing network traffic.

---

## Version History

### v1.1.0 (Current)
- ✨ Added bandwidth monitoring module
- 🎨 Enhanced dashboard with bandwidth charts
- 🚨 High bandwidth consumer alerts
- ⚡ Database query optimization
- 📊 Per-IP bandwidth analysis
- 🔧 Configurable thresholds

### v1.0.0
- Initial release
- Basic packet capture & analysis
- Real-time dashboard
- Protocol distribution

---

## Support

For issues or questions, review the troubleshooting section or examine logs:
```bash
# Backend logs
cat backend/database/packets.db  # Check database

# Frontend logs
Check browser console (F12)
```

---

**Made with ❤️ for network security professionals**
