# Testing & Validation Guide

## 🧪 Pre-Deployment Checklist

### Backend Tests

#### 1. API Health Check
```bash
curl http://127.0.0.1:5000/
# Expected: {"status": "CNS Project 1 Backend Running", "sniffer_active": true, "version": "1.1.0"}
```

#### 2. Traffic Endpoint
```bash
curl http://127.0.0.1:5000/traffic
# Expected: Array of recent packets with src_ip, dst_ip, protocol, size
```

#### 3. Statistics Endpoint
```bash
curl http://127.0.0.1:5000/stats | jq .
# Expected: Comprehensive stats with bandwidth section
```

#### 4. Database Check
```bash
cd backend
python -c "from database.db import init_db; init_db()"
# Expected: "Database initialized at ..."
```

#### 5. Bandwidth Calculation
```bash
cd backend
python -c "
from analysis.bandwidth import bandwidth_monitor
bandwidth_monitor.update()
print(bandwidth_monitor.get_bandwidth_status())
"
# Expected: JSON with total_mbps, is_high, high_consumers
```

### Frontend Tests

#### 1. Build Check
```bash
cd frontend
npm run build
# Expected: dist/ folder created without errors
```

#### 2. Lint Check
```bash
npm run lint
# Expected: No errors (warnings OK)
```

#### 3. Dev Server
```bash
npm run dev
# Expected: "Local: http://localhost:5173/"
```

#### 4. Manual Verification
1. Open http://localhost:5173
2. Check header displays "PacketMon v1.1"
3. Verify metrics cards appear
4. Check charts load
5. Verify data updates every 2 seconds

---

## 📊 Load Testing

### Simulate Network Traffic

#### Windows - PowerShell
```powershell
# Generate test traffic to multiple destinations
$destinations = "8.8.8.8", "1.1.1.1", "8.8.4.4"
foreach ($dest in $destinations) {
    for ($i=0; $i -lt 100; $i++) {
        Test-Connection -ComputerName $dest -Count 1 -ErrorAction SilentlyContinue
    }
}

# Check dashboard for spike in:
# - Total Packets
# - Bandwidth Usage
# - ICMP protocol distribution
```

#### Linux/Mac - Bash
```bash
#!/bin/bash
# Generate ICMP traffic
for i in {1..100}; do
    ping -c 1 8.8.8.8 &
    ping -c 1 1.1.1.1 &
    ping -c 1 8.8.4.4 &
done
wait

# Or use iperf for TCP/UDP
iperf -c server.example.com -t 30
```

### Expected Results
- Packet count increases
- Protocol distribution updates
- Bandwidth graph shows spike
- Top talkers list updates

---

## 🎯 Bandwidth Alert Testing

### Test Network-Wide Alert

**Objective:** Trigger bandwidth threshold alert

#### Step 1: Lower Threshold
Edit `backend/config.py`:
```python
BANDWIDTH_THRESHOLD_MBPS = 0.5  # Very low for testing
```

#### Step 2: Generate Traffic
```bash
# Download a large file in background
# or use iperf
iperf -c <server> -P 4 -t 60  # 4 parallel streams

# Monitor dashboard for:
# - Red banner appearing
# - Bandwidth card turning red
# - Alert message showing current Mbps
```

#### Step 3: Verify Alert Clears
Stop traffic and verify:
- Red banner disappears
- Card returns to normal color
- Alert clears within 5 seconds

### Test Per-IP Alert

**Objective:** Trigger per-IP consumer alert

#### Step 1: Adjust Threshold
```python
HIGH_TRAFFIC_IP_THRESHOLD = 0.1  # Very low for testing
```

#### Step 2: Generate Single-IP Traffic
```bash
# Generate traffic from/to specific IP
iperf -c <specific-ip> -P 2 -t 30
```

#### Step 3: Verify Consumer List
Check dashboard for:
- 🚨 High Bandwidth Consumers section appears
- Specific IP listed with Mbps
- Severity indicator (WARNING/CRITICAL)

---

## 🔒 Validation Tests

### 1. CORS Validation
```bash
# Test cross-origin requests
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     http://127.0.0.1:5000/

# Expected: Returns with appropriate CORS headers
```

### 2. Error Handling
```bash
# Test 404
curl http://127.0.0.1:5000/invalid-endpoint
# Expected: {"error": "Endpoint not found"}

# Test malformed requests (should not crash)
curl http://127.0.0.1:5000/stats?invalid=param
# Expected: Still returns valid stats
```

### 3. Data Integrity
```bash
# Verify database integrity
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('database/packets.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM packets')
print(f'Total packets in DB: {cursor.fetchone()[0]}')
"
```

### 4. Performance Check
```bash
# Measure API response time
time curl http://127.0.0.1:5000/stats > /dev/null

# Expected: <100ms on modern hardware
```

---

## 📱 Browser Compatibility

Test on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Known Issues
- None identified in v1.1.0

---

## 🔧 Regression Testing

### After Configuration Changes

1. **After changing thresholds:**
   - Alerts trigger at new threshold
   - No false positives/negatives

2. **After changing buffer sizes:**
   - Memory usage appropriate
   - No data loss
   - Performance unchanged

3. **After changing database:**
   - All data persists
   - Queries still fast
   - No corrupted records

### Test Matrix

| Change | Test | Expected |
|--------|------|----------|
| BANDWIDTH_THRESHOLD | Set 1 Mbps, generate traffic | Alert triggers |
| SNIFFER_BUFFER_SIZE | Reduce to 100, monitor RAM | Memory reduced |
| API_PORT | Change to 5001 | Frontend redirects |
| WINDOW_SECONDS | Change to 1 | Faster response |

---

## 📈 Production Readiness

### Pre-Production Checklist

- [ ] All endpoints return valid JSON
- [ ] Error handling works correctly
- [ ] Database operations are stable
- [ ] Frontend loads without console errors
- [ ] Charts render correctly
- [ ] Alerts trigger at configured thresholds
- [ ] Data persists across restarts
- [ ] Performance acceptable (API < 100ms)
- [ ] No memory leaks (monitor 1 hour)
- [ ] CORS working for frontend access

### Performance Baselines

Record these before deployment:

```bash
# API response time
time curl http://127.0.0.1:5000/stats

# Memory usage
ps aux | grep python | grep app.py

# Packet capture rate
curl http://127.0.0.1:5000/traffic | jq 'length'

# Database size
ls -lh backend/database/packets.db
```

---

## 🚀 Deployment Testing

### Staging Environment

1. Deploy to staging server
2. Run full test suite
3. Monitor for 24 hours
4. Document any issues
5. Get stakeholder sign-off
6. Deploy to production

### Production Monitoring

**First Week:**
- Monitor bandwidth alerts (false positive rate)
- Check API error logs
- Verify database growth rate
- Monitor memory/CPU

**Ongoing:**
- Weekly performance review
- Monthly alert threshold adjustment
- Quarterly security audit

---

## 📊 Performance Benchmarks

### System Requirements

Minimum:
- CPU: 2 cores
- RAM: 512 MB
- Disk: 1 GB free space

Recommended:
- CPU: 4 cores
- RAM: 2 GB
- Disk: 10 GB free space

### Expected Performance

| Metric | Value |
|--------|-------|
| Packets/Second | 1,000+ |
| API Response Time | <100ms |
| Memory Usage | <200 MB |
| Database Size (1 hour) | 50-100 MB |
| CPU Usage | <20% (single core) |

---

## 🐛 Issue Reporting Template

If you find issues, provide:

```
Title: [Brief description]

Environment:
- OS: [Windows/Linux/macOS]
- Python: [version]
- Node.js: [version]
- Browser: [name and version]

Steps to Reproduce:
1. [First step]
2. [Second step]
3. ...

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happened]

Error Message:
[If applicable]

Screenshots:
[If applicable]
```

---

## ✅ Sign-Off

- [ ] All tests passed
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Team trained
- [ ] Ready for deployment

**Date:** ___________
**Tester:** ___________
**Sign-off:** ___________

---

**Testing complete? Time to ship! 🚀**
