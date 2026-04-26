import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, Shield, Database, Wifi } from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const Dashboard = () => {
  const [traffic, setTraffic] = useState([]);
  const [stats, setStats] = useState(null);

  const fetchData = async () => {
    try {
      const trafficRes = await fetch('http://127.0.0.1:5000/traffic');
      const statsRes = await fetch('http://127.0.0.1:5000/stats');
      
      const trafficData = await trafficRes.json();
      const statsData = await statsRes.json();

      setTraffic(trafficData);
      setStats(statsData);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const protocolData = stats?.protocol_distribution 
    ? Object.entries(stats.protocol_distribution).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white font-sans">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="text-blue-500" /> CNS Traffic Monitor
        </h1>
        <div className="flex gap-4">
          <div className="flex items-center gap-2 bg-gray-800 px-4 py-2 rounded-lg">
            <Wifi size={18} className="text-green-500" />
            <span>Status: Live</span>
          </div>
        </div>
      </header>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border-l-4 border-blue-500">
          <div className="flex justify-between items-center">
            <p className="text-gray-400">Total Packets</p>
            <Activity className="text-blue-500" />
          </div>
          <h2 className="text-3xl font-bold mt-2">{stats?.metrics?.total_packets || 0}</h2>
        </div>
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border-l-4 border-green-500">
          <div className="flex justify-between items-center">
            <p className="text-gray-400">Throughput</p>
            <Database className="text-green-500" />
          </div>
          <h2 className="text-3xl font-bold mt-2">{stats?.metrics?.kbps || 0} <span className="text-sm">kbps</span></h2>
        </div>
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border-l-4 border-yellow-500">
          <p className="text-gray-400">Avg Packet Size</p>
          <h2 className="text-3xl font-bold mt-2">{stats?.metrics?.avg_packet_size || 0} <span className="text-sm">B</span></h2>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Live Table */}
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
          <h3 className="text-xl font-semibold mb-4">Live Traffic Feed</h3>
          <div className="overflow-x-auto h-80">
            <table className="w-full text-left">
              <thead className="border-b border-gray-700">
                <tr>
                  <th className="py-2">Source</th>
                  <th className="py-2">Dest</th>
                  <th className="py-2">Proto</th>
                  <th className="py-2">Size</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {traffic.slice().reverse().map((pkt, i) => (
                  <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-2 text-blue-400">{pkt.src_ip}</td>
                    <td className="py-2 text-green-400">{pkt.dst_ip}</td>
                    <td className="py-2 font-mono">{pkt.protocol}</td>
                    <td className="py-2">{pkt.size} B</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Charts */}
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg flex flex-col items-center">
          <h3 className="text-xl font-semibold mb-4 self-start">Protocol Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={protocolData}
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {protocolData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-4">
            {protocolData.map((d, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }}></div>
                <span className="text-sm text-gray-300">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;