import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts';
import { Activity, Database, Wifi, Globe, ShieldAlert } from 'lucide-react';
import './index.css';

const COLORS = ['#c084fc', '#0088FE', '#00C49F', '#FF8042'];

const Dashboard = () => {
  const [traffic, setTraffic] = useState([]);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);

  const fetchData = async () => {
    try {
      const trafficRes = await fetch('http://127.0.0.1:5000/traffic');
      const statsRes = await fetch('http://127.0.0.1:5000/stats');
      
      const trafficData = await trafficRes.json();
      const statsData = await statsRes.json();

      setTraffic(trafficData);
      setStats(statsData);

      // Create a moving history for the Line Chart
      setHistory(prev => {
        const newPoint = {
          time: new Date().toLocaleTimeString().split(' ')[0],
          count: statsData?.metrics?.total_packets || 0
        };
        return [...prev, newPoint].slice(-20); // Keep last 20 seconds
      });
    } catch (error) {
      console.error("Error fetching data:", error);
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

  return (
    <div id="root">
      <header className="brand-container">
        <h1 className="brand-title">PacketMon</h1>
        <div className="status-badge">
          <Wifi size={14} className={traffic.length > 0 ? "text-green" : "text-red"} />
          <span>{traffic.length > 0 ? "LIVE CAPTURE" : "AWAITING DATA"}</span>
        </div>
      </header>

      {/* Top Metrics Cards */}
      <div className="metrics-grid">
        <div className="stat-card blue">
          <div className="stat-header">
            <span>Total Packets</span>
            <Activity size={18} />
          </div>
          <p className="stat-value">{stats?.metrics?.total_packets || 0}</p>
        </div>
        
        <div className="stat-card purple">
          <div className="stat-header">
            <span>Network Throughput</span>
            <Database size={18} />
          </div>
          <p className="stat-value">{stats?.metrics?.kbps || 0} <small>kbps</small></p>
        </div>

        <div className="stat-card green">
          <div className="stat-header">
            <span>Active Ports</span>
            <Globe size={18} />
          </div>
          <p className="stat-value">{(stats?.active_ports?.length) || 0}</p>
        </div>
      </div>

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
                  <th>Size</th>
                </tr>
              </thead>
              <tbody>
                {traffic.slice().reverse().map((pkt, i) => (
                  <tr key={i}>
                    <td className="ip-text">{pkt.src_ip}</td>
                    <td className="ip-text">{pkt.dst_ip}</td>
                    <td><span className={`proto-tag ${pkt.protocol}`}>{pkt.protocol}</span></td>
                    <td className="mono">{pkt.size}B</td>
                  </tr>
                ))}
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
            <h3 className="panel-title">Traffic Activity (PPS)</h3>
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
        </div>
      </div>
    </div>
  );
};

export default Dashboard;