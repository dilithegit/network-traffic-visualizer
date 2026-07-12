import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid, BarChart, Bar } from 'recharts';
import { Activity, Database, Wifi, Globe, ShieldAlert, AlertTriangle } from 'lucide-react';
import './index.css';

const COLORS = ['#c084fc', '#0088FE', '#00C49F', '#FF8042'];
const API_BASE_URL = 'http://127.0.0.1:5000';

const Dashboard = () => {
  const [traffic, setTraffic] = useState([]);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [bandwidthHistory, setBandwidthHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isCapturing, setIsCapturing] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [trafficRes, statsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/traffic`),
        fetch(`${API_BASE_URL}/stats`)
      ]);

      if (!trafficRes.ok || !statsRes.ok) {
        throw new Error('Failed to fetch data from API');
      }

      const trafficData = await trafficRes.json();
      const statsData = await statsRes.json();

      setTraffic(trafficData);
      setStats(statsData);

      // Create a moving history for the Line Chart (packets)
      setHistory(prev => {
        const newPoint = {
          time: new Date().toLocaleTimeString().split(' ')[0],
          count: statsData?.metrics?.total_packets || 0
        };
        return [...prev, newPoint].slice(-20);
      });

      // Create a moving history for bandwidth
      setBandwidthHistory(prev => {
        const newPoint = {
          time: new Date().toLocaleTimeString().split(' ')[0],
          mbps: statsData?.bandwidth?.total_mbps || 0,
          threshold: statsData?.bandwidth?.threshold_mbps || 0
        };
        return [...prev, newPoint].slice(-20);
      });
    } catch (error) {
      console.error("Error fetching data:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCaptureStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/capture/status`);
      if (!response.ok) {
        throw new Error('Failed to fetch capture status');
      }

      const data = await response.json();
      setIsCapturing(data.running);
    } catch (error) {
      console.error('Error fetching capture status:', error);
    }
  };

  const handleStopCapture = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/capture/stop`, { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to stop capture');
      }

      const data = await response.json();
      setIsCapturing(data.running);
      setError(null);
    } catch (error) {
      console.error('Error stopping capture:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchCaptureStatus();
    const interval = setInterval(() => {
      fetchData();
      fetchCaptureStatus();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const protocolData = stats?.protocol_distribution 
    ? Object.entries(stats.protocol_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const isBandwidthHigh = stats?.bandwidth?.is_high || false;
  const highConsumers = stats?.bandwidth?.high_consumers || [];

  return (
    <div id="root">
      <header className="page-header">
        <div className="brand-group">
          <div>
            <h1 className="brand-title">NetMon</h1>
            <p className="brand-subtitle">Real-time network monitoring for live traffic, bandwidth and protocol insights.</p>
            <p className="brand-subtitle muted">Host: {stats?.hostname || 'unknown'}</p>
          </div>
        </div>
        <div className="header-actions">
          <div className={`status-pill ${isCapturing && traffic.length > 0 ? 'status-active' : 'status-idle'}`}>
            <span className="status-dot" />
            {isCapturing && traffic.length > 0 ? 'Status: Active' : 'Status: Waiting'}
          </div>
          <button className="button stop-btn" onClick={handleStopCapture} disabled={!isCapturing || loading}>
            {loading ? 'Stopping...' : isCapturing ? 'Stop Capture' : 'Capture Stopped'}
          </button>
        </div>
      </header>

      {isBandwidthHigh && (
        <div className="alert-banner">
          <AlertTriangle size={20} />
          <span>High bandwidth detected: {stats?.bandwidth?.total_mbps} Mbps (threshold {stats?.bandwidth?.threshold_mbps} Mbps)</span>
        </div>
      )}

      <div className="chart-grid">
        <div className="panel chart-card">
          <div className="panel-heading">
            <div>
              <h3>Bandwidth Analytics</h3>
              <p className="panel-description">Recent throughput over time.</p>
            </div>
          </div>
          <div className="panel-body chart-panel">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={bandwidthHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="time" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
                <Line type="monotone" dataKey="mbps" stroke="#2563eb" strokeWidth={3} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="threshold" stroke="#f97316" strokeWidth={2} strokeDasharray="5 5" dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
            <div className="panel-note">[ line chart placeholder ]</div>
          </div>
        </div>

        <div className="panel chart-card">
          <div className="panel-heading">
            <div>
              <h3>Protocol Distribution</h3>
              <p className="panel-description">Traffic share by protocol.</p>
            </div>
          </div>
          <div className="panel-body chart-panel chart-right">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={protocolData}
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={6}
                  dataKey="value"
                >
                  {protocolData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="panel-note">[ doughnut chart placeholder ]</div>
          </div>
        </div>
      </div>

      <div className="panel table-panel">
        <div className="panel-heading table-heading">
          <div>
            <h3>Live Log Feed</h3>
            <p className="panel-description">Latest packet logs captured from the network.</p>
          </div>
          <div className="table-summary">{loading ? 'Refreshing...' : `${traffic.length} entries`}</div>
        </div>
        <div className="table-container">
          <table className="traffic-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source IP</th>
                <th>Dest IP</th>
                <th>Protocol</th>
                <th>Length</th>
                <th>Info</th>
              </tr>
            </thead>
            <tbody>
              {traffic.length > 0 ? (
                traffic.slice().reverse().map((pkt, i) => (
                  <tr key={i}>
                    <td>{pkt.timestamp ? new Date(pkt.timestamp * 1000).toLocaleTimeString([], { hour12: false }) : '-'}</td>
                    <td className="ip-text">{pkt.src_ip}</td>
                    <td className="ip-text">{pkt.dst_ip}</td>
                    <td><span className={`proto-tag ${pkt.protocol}`}>{pkt.protocol}</span></td>
                    <td className="mono">{pkt.size}B</td>
                    <td>{pkt.info || '-'}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>Awaiting packets...</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="table-footer">• • • scrolling • • •</div>
      </div>

      {error && (
        <div className="error-banner">
          Error: {error}
        </div>
      )}
    </div>
  );
};

export default Dashboard;