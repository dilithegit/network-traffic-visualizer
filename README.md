# NETSENTRY (PacketMon) - Real-Time Network Traffic Analyzer & Bandwidth Monitor

## Overview

**NETSENTRY** (formerly **PacketMon**) is a lightweight, Wireshark-inspired, real-time network packet analyzer and bandwidth monitoring system for Local Area Networks. It captures live traffic with Scapy, extracts modern web activity (HTTP URLs + HTTPS SNI, including QUIC), detects traffic spikes and suspicious hosts, and streams everything to a responsive React dashboard over Socket.IO.

### Key Features

✅ **Real-Time Packet Capture** - Live network sniffing using Scapy  
✅ **Dynamic Interface Selection** - Wireshark-style dropdown; switch interfaces without restart  
✅ **Modern URL Detection** - HTTP URL reconstruction + HTTPS SNI (TLS) extraction  
✅ **QUIC / UDP Capture** - Detects modern UDP/443 traffic  
✅ **Bandwidth Monitoring** - Tracks total bandwidth and per-IP usage  
✅ **Traffic Spike Detection** - Per-IP packets/sec & bytes/sec anomaly alerts  
✅ **Suspicious Host Tracking** - WARNING / CRITICAL status registry per IP  
✅ **Live Alerts & Feeds** - Real-time URL, spike and alert panels  
✅ **Protocol Analysis** - Breaks down traffic by TCP, UDP, ICMP, QUIC, etc.  
✅ **Live Dashboard** - Responsive Tailwind UI with Chart.js, light/dark themes  
✅ **Socket.IO Streaming** - Separate events for packets, URLs, spikes, stats, alerts  
✅ **Database Persistence** - SQLite storage for historical analysis  
✅ **RESTful API** - Clean API endpoints for frontend consumption  
✅ **Performance Optimized** - Rolling buffers, rAF-batched rendering, batch DB writes  

### v3.0.0 Feature Enhancements

The platform was overhauled into a professional-grade monitor. Highlights:

1. **Enhanced URL & Hostname Detection** — full HTTP URL reconstruction
   (`http://host/path`), TLS SNI + Client Hello analysis, and DNS-correlation
   hostname caching so encrypted flows still show a destination name
   (`backend/analysis/hostname_cache.py`, `url_extractor.py`).
2. **Richer Live URL Feed** — every entry now carries timestamp, source/dest
   IP, hostname, URL, protocol and destination port.
3. **Dynamic Spike Detection** — a statistical engine (per-IP packets/sec &
   bytes/sec baselines, moving average + rolling std-dev, z-score) with
   Low/Medium/High sensitivity presets; severity scales with deviation.
4. **Real-Time Network Stats** — current/peak/average bandwidth, packets/sec,
   bytes/sec, active connections and active devices.
5. **VMware / Inactive Interface Handling** — robust enumeration with up/down,
   virtual and loopback classification; a clear warning is shown when a running
   adapter goes silent instead of freezing.
6. **Dynamic Protocol Distribution** — auto-discovers any observed protocol
   (ARP, TCP, UDP, ICMP, DNS, DHCP, TLS, SSH, QUIC, …) with a timeout-based
   lifecycle so stale protocols retire.
7. **Advanced Packet Inspection** — Wireshark-style side panel: endpoints, MACs,
   ports, TTL, TCP flags, DNS/TLS/HTTP detail and a hex + ASCII payload preview.
8. **Instant Search & Filtering** — syntax filters
   (`protocol == DNS`, `ip == 192.168.1.10`, `port == 443`, `host contains youtube`)
   applied client-side without interrupting capture.
9. **Dashboard Stability & Performance** — `React.memo`/`useMemo`/`useCallback`
   throughout, packet state isolated from UI state, and Socket.IO batching
   (`packet_batch`) with rolling buffers.
10. **Packet Capture Timeline** — horizontal, colour-coded, zoomable timeline
    with Pause/Resume/Auto-scroll; selecting an event highlights the packet and
    opens the inspector.

### Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO, Scapy
- **Frontend:** React (Vite), Tailwind CSS, Chart.js
- **Realtime:** Socket.IO

---

## Project Architecture

```
CNS Project 1/
├── backend/                    # Python Flask + Socket.IO API & Packet Sniffer
│   ├── app.py                 # App entry: blueprint + Socket.IO wiring
│   ├── config.py              # Configuration & thresholds
│   ├── capture/
│   │   ├── sniffer.py         # Packet capture engine (Scapy) + URL/spike fan-out
│   │   ├── parser.py          # Packet parsing utilities
│   │   └── interface_manager.py  # Wireshark-style interface enumeration
│   ├── analysis/
│   │   ├── stats.py           # Aggregated traffic statistics
│   │   ├── bandwidth.py       # Bandwidth monitoring & alerts
│   │   ├── url_extractor.py   # HTTP URL + HTTPS SNI extraction
│   │   └── spike_detector.py  # Per-IP spike detection & suspicious hosts
│   ├── alerts/
│   │   └── notifier.py        # Socket.IO event broadcaster + history
│   ├── database/
│   │   └── db.py              # SQLite database management
│   ├── models/
│   │   └── traffic_model.py   # Data models
│   ├── routes/
│   │   └── api.py             # REST API routes
│   ├── services/
│   │   └── socket_events.py   # Socket.IO handlers + stats broadcaster
│   └── tests/                 # Backend unit tests
├── frontend/                   # React (Vite) + Tailwind + Chart.js Dashboard
│   ├── src/
│   │   ├── main.jsx           # Entry point
│   │   ├── App.jsx            # Re-export of Dashboard
│   │   ├── index.css          # Tailwind directives + base styles
│   │   ├── components/        # Navbar, charts, feeds, tables, panels
│   │   ├── pages/Dashboard.jsx# Dashboard layout
│   │   ├── context/           # ThemeContext, StatsContext
│   │   ├── hooks/             # useCaptureControl, useSocketEvents
│   │   └── services/          # socket.js, api.js, chartSetup.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── scripts/                   # Cross-platform startup scripts
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

### `GET /interfaces`
List available capture interfaces (Wireshark-style friendly names).
```json
{ "interfaces": ["Wi-Fi", "Ethernet", "Loopback"], "active_interface": "Wi-Fi" }
```

### `POST /capture/start`
Start (or restart) capture on a selected interface.
```json
{ "interface": "Wi-Fi" }
```

### `POST /capture/stop`
Stop the running capture.

### `GET /capture/status`
```json
{ "running": true, "active_interface": "Wi-Fi" }
```

### `GET /alerts`
```json
{
  "alerts": [ { "alert": "Traffic Spike Detected", "src_ip": "192.168.1.14", "severity": "HIGH" } ],
  "url_history": [ { "timestamp": "14:23:10", "src_ip": "192.168.1.12", "protocol": "HTTPS", "url": "youtube.com" } ],
  "suspicious_hosts": [ "192.168.1.14" ]
}
```

### Socket.IO Events
Real-time push channel (client connects to `http://127.0.0.1:5000`):
- `new_packet` - a single parsed packet (live log)
- `new_url` - a detected HTTP URL / HTTPS SNI
- `spike_detected` - a per-IP traffic spike
- `statistics_update` - aggregated stats every ~2s
- `new_alert` - generic alert (bandwidth threshold, spikes, domains)

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

### v3.0.0 (Current) - Professional-Grade Overhaul
- 🔎 Full HTTP URL reconstruction + TLS SNI/Client Hello analysis
- 🧠 DNS-correlation hostname cache (encrypted flows show a name, not "HTTPS")
- 📡 Richer Live URL feed (timestamp, IPs, hostname, URL, protocol, port)
- 📈 Dynamic statistical spike detection with Low/Medium/High sensitivity
- ⚡ Real-time bandwidth/pps/bps, active connections & devices
- 🖥️ VMware / inactive-interface detection with actionable warnings
- 🔄 Dynamic protocol pie with auto-discovery + timeout-based retirement
- 🔬 Wireshark-style packet inspector (MAC, TTL, flags, DNS/TLS/HTTP, hex+ASCII)
- 🔍 Instant syntax search/filter without interrupting capture
- 🪟 Horizontal packet timeline (colour-coded, zoom, pause, auto-scroll)
- 🚀 Socket.IO batching + memoized UI for flicker-free high-throughput capture

### v2.0.0 - NETSENTRY
- 🌐 Dynamic Wireshark-style interface selection (`GET /interfaces`, `POST /capture/start`)
- 🔍 Modern URL detection: HTTP URL reconstruction + HTTPS SNI (TLS) extraction
- ⚡ QUIC / UDP-443 capture and detection
- 📈 Real-time traffic spike detection (per-IP packets/sec & bytes/sec)
- 🚨 Suspicious host registry with NORMAL / WARNING / CRITICAL status
- 🔔 Live alert panel + dedicated spike and URL feeds
- 💡 Light / dark theme toggle (Tailwind `darkMode: "class"`, localStorage)
- 🔌 Socket.IO streaming with separate events (`new_packet`, `new_url`, `spike_detected`, `statistics_update`, `new_alert`)
- 🧩 Modular backend (`capture/`, `analysis/`, `alerts/`, `routes/`, `services/`) and frontend (`components/`, `pages/`, `services/`, `context/`, `hooks/`)
- ⚡ Flicker-free UI: `React.memo`, rAF-batched packet buffer, capped rolling history

### v1.1.0
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
