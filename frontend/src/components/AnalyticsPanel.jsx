import { Line, Doughnut } from "react-chartjs-2";

function AnalyticsPanel({ type }) {
  const lineData = {
    labels: ["", "", "", "", "", ""],
    datasets: [
      {
        data: [12, 30, 18, 40, 28, 50],
        borderColor: "black",
        tension: 0,
      },
    ],
  };

  const doughnutData = {
    labels: ["TCP", "UDP", "DNS"],
    datasets: [
      {
        data: [60, 25, 15],
        backgroundColor: ["#111", "#777", "#ccc"],
      },
    ],
  };

  return (
    <div className="border border-gray-500 p-3 h-[250px]">
      <h2 className="text-sm mb-2 uppercase">
        {type === "bandwidth"
          ? "Bandwidth Analytics"
          : "Protocol Distribution"}
      </h2>

      <div className="border border-dashed h-[180px] flex items-center justify-center">
        {type === "bandwidth" ? (
          <Line data={lineData} />
        ) : (
          <Doughnut data={doughnutData} />
        )}
      </div>
    </div>
  );
}

export default AnalyticsPanel;