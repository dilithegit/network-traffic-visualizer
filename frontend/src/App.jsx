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

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const protocolData = stats?.protocol_distribution 
    ? Object.entries(stats.protocol_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const isBandwidthHigh = stats?.bandwidth?.is_high || false;
  const highConsumers = stats?.bandwidth?.high_consumers || [];

  return (
    <div id="root">
      <header className="brand-container">
        <h1 className="brand-title">NetMon</h1>
        <div className="status-badge">
          <Wifi size={14} className={traffic.length > 0 ? "text-green" : "text-red"} />
          <span>{traffic.length > 0 ? "LIVE CAPTURE" : "AWAITING DATA"}</span>
        </div>
      </header>

      {/* Alert Banner */}
      {isBandwidthHigh && (
        <div style={{
          background: '#ff4444',
          color: 'white',
          padding: '12px 20px',
          margin: '0 20px',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '20px'
        }}>
          <AlertTriangle size={20} />
          <span>⚠️ HIGH BANDWIDTH ALERT: {stats?.bandwidth?.total_mbps} Mbps (Threshold: {stats?.bandwidth?.threshold_mbps} Mbps)</span>
        </div>
      )}

      {/* Top Metrics Cards */}
      <div className="metrics-grid">
        <div className="stat-card blue">
          <div className="stat-header">
            <span>Packets (10-min)</span>
            <Activity size={18} />
          </div>
          <p className="stat-value">{stats?.metrics?.packets_since_reset || 0}</p>
        </div>

        <div className="stat-card teal">
          <div className="stat-header">
            <span>Device Host</span>
            <Globe size={18} />
          </div>
          <p className="stat-value">{stats?.hostname || 'Unknown'}</p>
        </div>
        
        <div className={`stat-card ${isBandwidthHigh ? 'red' : 'purple'}`}>
          <div className="stat-header">
            <span>Bandwidth Usage</span>
            <Database size={18} />
          </div>
          <p className="stat-value">{stats?.bandwidth?.total_mbps || 0} <small>Mbps</small></p>
          <p style={{ fontSize: '0.8em', marginTop: '5px', opacity: 0.8 }}>
            Peak: {stats?.bandwidth?.peak_mbps || 0} Mbps
          </p>
        </div>

        <div className="stat-card green">
          <div className="stat-header">
            <span>Active Ports</span>
            <ShieldAlert size={18} />
          </div>
          <p className="stat-value">{(stats?.active_ports?.length) || 0}</p>
        </div>
      </div>

      {/* High Bandwidth Consumers Alert */}
      {highConsumers.length > 0 && (
        <div className="panel">
          <h3 className="panel-title">🚨 High Bandwidth Consumers</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {highConsumers.map((consumer, idx) => (
              <div key={idx} style={{
                background: 'rgba(255, 68, 68, 0.1)',
                border: '1px solid #ff4444',
                padding: '10px',
                borderRadius: '6px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span>{consumer.ip}</span>
                <span style={{ fontWeight: 'bold', color: consumer.severity === 'CRITICAL' ? '#ff4444' : '#ffaa00' }}>
                  {consumer.mbps} Mbps ({consumer.severity})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="main-content-grid">
        {/* Live Packet Table */}
        <div className="panel overflow-hidden">
          <h3 className="panel-title">Live Traffic Feed</h3>
          <div className="table-container">
            <table className="traffic-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Destination</th>
                  <th>Proto</th>
                  <th>Info</th>
                  <th>Layer</th>
                  <th>Size</th>
                </tr>
              </thead>
              <tbody>
                {traffic.length > 0 ? (
                  traffic.slice().reverse().map((pkt, i) => (
                    <tr key={i}>
                      <td className="ip-text">{pkt.src_ip}</td>
                      <td className="ip-text">{pkt.dst_ip}</td>
                      <td><span className={`proto-tag ${pkt.protocol}`}>{pkt.protocol}</span></td>
                      <td>{pkt.info || '-'}</td>
                      <td>{pkt.layer || '-'}</td>
                      <td className="mono">{pkt.size}B</td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>Awaiting packets...</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Intelligence Charts */}
        <div className="panel flex flex-col gap-8">
          <div className="chart-section">
            <h3 className="panel-title">Protocol Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={protocolData}
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={8}
                  dataKey="value"
                >
                  {protocolData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1f2028', border: 'none', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-section">
            <h3 className="panel-title">Packet Activity (PPS)</h3>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e303a" vertical={false} />
                <XAxis dataKey="time" hide />
                <YAxis hide />
                <Tooltip contentStyle={{ backgroundColor: '#1f2028', border: 'none' }} />
                <Line type="monotone" dataKey="count" stroke="#c084fc" strokeWidth={3} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-section">
            <h3 className="panel-title">Bandwidth Usage (Mbps)</h3>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={bandwidthHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e303a" vertical={false} />
                <XAxis dataKey="time" hide />
                <YAxis hide />
                <Tooltip contentStyle={{ backgroundColor: '#1f2028', border: 'none' }} />
                <Line type="monotone" dataKey="mbps" stroke="#ff6b6b" strokeWidth={3} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="threshold" stroke="#ffaa00" strokeWidth={2} strokeDasharray="5 5" dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ color: 'red', padding: '10px', margin: '10px 0' }}>
          Error: {error}
        </div>
      )}
    </div>
  );
};

export default Dashboard;