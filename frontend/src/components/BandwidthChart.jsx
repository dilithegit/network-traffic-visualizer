// Live bandwidth line chart. Maintains its own rolling history from the
// `statistics_update` payload so it animates smoothly without re-fetching.
import { memo, useEffect, useRef, useState } from "react";
import { Line } from "react-chartjs-2";
import "../services/chartSetup";
import { useStats } from "../context/StatsContext";

function BandwidthChartBase() {
  const stats = useStats();
  const [history, setHistory] = useState([]);
  const historyRef = useRef([]);

  useEffect(() => {
    if (!stats?.bandwidth) return;
    const point = {
      time: new Date().toLocaleTimeString([], { hour12: false }),
      mbps: stats.bandwidth.total_mbps ?? 0,
      threshold: stats.bandwidth.threshold_mbps ?? 0,
    };
    const next = [...historyRef.current, point].slice(-30);
    historyRef.current = next;
    setHistory(next);
  }, [stats]);

  const data = {
    labels: history.map((h) => h.time),
    datasets: [
      {
        label: "Mbps",
        data: history.map((h) => h.mbps),
        borderColor: "#6366f1",
        backgroundColor: "rgba(99,102,241,0.15)",
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: "Threshold",
        data: history.map((h) => h.threshold),
        borderColor: "#f97316",
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
        borderWidth: 1.5,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: "#94a3b8", maxTicksLimit: 6 },
      },
      y: {
        beginAtZero: true,
        grid: { color: "rgba(148,163,184,0.15)" },
        ticks: { color: "#94a3b8" },
      },
    },
    plugins: {
      legend: { labels: { color: "#94a3b8", boxWidth: 12 } },
      tooltip: { enabled: true },
    },
  };

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  );
}

export const BandwidthChart = memo(BandwidthChartBase);
export default BandwidthChart;
