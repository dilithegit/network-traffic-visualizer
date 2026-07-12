// Protocol distribution doughnut chart, built from the statistics payload.
import { memo } from "react";
import { Doughnut } from "react-chartjs-2";
import "../services/chartSetup";
import { useStats } from "../context/StatsContext";

const PALETTE = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#06b6d4",
  "#a855f7",
  "#84cc16",
];

function ProtocolChartBase() {
  const stats = useStats();
  const distribution = stats?.protocol_distribution || {};

  const labels = Object.keys(distribution);
  const values = Object.values(distribution);

  const data = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: PALETTE,
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
