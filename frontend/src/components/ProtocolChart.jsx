// Dynamic protocol distribution doughnut chart (req 6). Auto-discovers every
// observed protocol (TCP, UDP, ICMP, ARP, DNS, HTTPS, TLS, QUIC, SSH, ...)
// from the backend's `layer_distribution` and retires protocols that have been
// inactive longer than the configured timeout.
import { memo } from "react";
import { Doughnut } from "react-chartjs-2";
import "../services/chartSetup";
import { useStats } from "../context/StatsContext";
import { protocolColor } from "../utils/protocolColors";

const FALLBACK_PALETTE = [
  "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#06b6d4",
  "#a855f7", "#84cc16", "#ec4899", "#14b8a6", "#64748b",
];

function ProtocolChartBase() {
  const stats = useStats();
  // `layer_distribution` is the dynamic, timeout-aware view from the backend.
  const distribution = stats?.layer_distribution || stats?.protocol_distribution || {};

  const labels = Object.keys(distribution);
  const values = Object.values(distribution);
  const colors = labels.map((name, i) => protocolColor(name) || FALLBACK_PALETTE[i % FALLBACK_PALETTE.length]);

  const data = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors,
        borderWidth: 0,
        hoverOffset: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "62%",
    plugins: {
      legend: {
        position: "right",
        labels: { color: "#94a3b8", boxWidth: 12, padding: 12 },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.label}: ${ctx.parsed} pkts`,
        },
      },
    },
  };

  return (
    <div className="relative h-64">
      {labels.length === 0 ? (
        <div className="flex h-full items-center justify-center text-sm text-slate-400">
          Awaiting packets…
        </div>
      ) : (
        <Doughnut data={data} options={options} />
      )}
    </div>
  );
}

export const ProtocolChart = memo(ProtocolChartBase);
export default ProtocolChart;
