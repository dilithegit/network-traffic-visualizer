# Quick Start Guide

## ⚡ Fastest Way to Run the Project

### Windows (Recommended)
Double-click: `scripts/start_project.bat`

Or from PowerShell:
```powershell
cd "C:\Users\YourUsername\Documents\CNS Project 1"
.\scripts\start_project.bat
```

### macOS/Linux
```bash
cd ~/Documents/CNS\ Project\ 1
chmod +x scripts/start_project.sh
sudo scripts/start_project.sh  # sudo needed for packet capture
```

---

## 📋 Prerequisites Check

### 1. Python
```bash
python --version  # Should be 3.8 or higher
```

If not installed: https://www.python.org/downloads/

### 2. Node.js
```bash
node --version   # Should be 16+
npm --version    # Should be 8+
```

If not installed: https://nodejs.org/

### 3. Administrative Privileges
- **Windows:** Run CMD/PowerShell as Administrator
- **Linux/Mac:** Use `sudo` when running scripts

---

## 🚀 Manual Startup (If Scripts Don't Work)

### Terminal 1 - Backend
```bash
cd backend
pip install -r ../requirements.txt  # Only needed first time
python app.py
```

Expected output:
```
[*] Database initialized at .../packets.db
[*] Auto-starting capture on: <interface>
[*] Capture started on interface: <interface>
[*] NETSENTRY API + Socket.IO on http://127.0.0.1:5000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install  # Only needed first time
npm run dev
```

Expected output:
```
  VITE v8.0.10  ready in 100 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## 🌐 Access the Application

Once both terminal windows show the success messages:

1. Open browser and go to: **http://localhost:5173**
2. You should see the PacketMon dashboard loading
3. Wait ~5 seconds for first packets to arrive (depending on network activity)

---

## 🔍 Troubleshooting

### Issue: "Address already in use"
Port 5000 or 5173 is occupied.

**Solution:**
1. Find process using port 5000:
   - Windows: `netstat -ano | findstr 5000`
   - Linux: `lsof -i :5000`
2. Kill the process or change port in `backend/config.py`

### Issue: "No packets captured"
1. Ensure backend is running (check Terminal 1)
2. Check API is accessible: http://127.0.0.1:5000
3. Run as Administrator/sudo for full network access
4. On Windows, check Windows Defender Firewall isn't blocking

### Issue: "Module not found" errors
```bash
# Reinstall Python packages
cd backend
pip install --force-reinstall -r ../requirements.txt

# Reinstall Node packages
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Slow performance
Reduce buffer sizes in `backend/config.py`:
```python
SNIFFER_BUFFER_SIZE = 500
SNIFFER_BATCH_SIZE = 100
```

---

## 📊 Understanding the Dashboard

The NETSENTRY console (PacketMon) is a Wireshark-inspired LAN monitor.

### Top Bar
- **Interface dropdown:** Pick the capture interface (Wi-Fi, Ethernet, etc.). Switching stops the previous capture and restarts on the new one.
- **Status pill:** ACTIVE / IDLE / DISCONNECTED (Socket.IO connection state).
- **START / STOP:** Control live capture.
- **Theme toggle:** Switch light / dark (persisted in localStorage).

### Stat Cards
- **Packets / Throughput / Avg Pkt / High IPs / Interface / Host**

### Charts & Panels
- **Bandwidth Analytics:** Line graph of Mbps over time vs threshold.
- **Protocol Distribution:** Doughnut of TCP/UDP/ICMP/QUIC/etc.
- **Live URL Activity:** Detected HTTP URLs and HTTPS SNI (TLS).
- **Traffic Spike Alerts:** Per-IP packet/bandwidth anomalies.
- **Live Packet Log:** Real-time packet stream (rAF-batched, capped).
- **Suspicious Hosts:** IPs that exceeded thresholds (NORMAL/WARNING/CRITICAL).
- **Live Alerts:** Unified real-time alert feed.

---

## ⚙️ Configuration

Edit `backend/config.py` to customize:

```python
# Change bandwidth threshold (Mbps)
BANDWIDTH_THRESHOLD_MBPS = 50  # Alert when exceeded

# Change rolling window for bandwidth calculation
BANDWIDTH_WINDOW_SECONDS = 5

# Change per-IP alert threshold
HIGH_TRAFFIC_IP_THRESHOLD = 10

# Change API port
API_PORT = 5000

# Change buffer size
SNIFFER_BUFFER_SIZE = 1000
```

---

## 📈 API Endpoints (For Development)

Test these in your browser or with curl:

```bash
# Health check
curl http://127.0.0.1:5000/

# List interfaces (Wireshark-style friendly names)
curl http://127.0.0.1:5000/interfaces

# Start capture on an interface
curl -X POST http://127.0.0.1:5000/capture/start -H "Content-Type: application/json" -d "{\"interface\":\"Wi-Fi\"}"

# Stop capture
curl -X POST http://127.0.0.1:5000/capture/stop

# Get recent traffic
curl http://127.0.0.1:5000/traffic

# Get statistics
curl http://127.0.0.1:5000/stats

# Get alerts / URL history / suspicious hosts
curl http://127.0.0.1:5000/alerts
```

Real-time updates (bandwidth, URLs, spikes, alerts) are pushed over Socket.IO
events: `new_packet`, `new_url`, `spike_detected`, `statistics_update`, `new_alert`.

---

## 📦 Project Structure (Quick Reference)

```
📁 Backend (Python)
├── app.py              ← Start here: Main Flask server
├── config.py           ← Settings & thresholds
├── capture/sniffer.py  ← Packet capture engine
├── analysis/
│   ├── stats.py        ← Traffic statistics
│   └── bandwidth.py    ← NEW! Bandwidth monitoring
└── database/db.py      ← SQLite storage

📁 Frontend (React)
├── src/App.jsx         ← Main dashboard
├── src/index.css       ← Styles
└── package.json        ← Dependencies
```

---

## 🎯 Next Steps

After installation:
1. Generate network traffic (visit websites, download files, etc.)
2. Watch the dashboard update in real-time
3. Observe bandwidth consumption
4. Set custom bandwidth thresholds in config.py
5. Check database: `backend/database/packets.db`

---

## 🆘 Need Help?

1. Check backend terminal for error messages
2. Check browser console (F12) for frontend errors
3. Review README.md for full documentation
4. Ensure Python 3.8+ and Node.js 16+
5. Try running as Administrator/sudo

---

**Happy packet sniffing! 📡**
