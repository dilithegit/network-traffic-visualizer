import Navbar from "../components/Navbar";
import AnalyticsPanel from "./AnalyticsPanel.jsx";
import LogTable from "./LogTable.jsx/index.js";

function Dashboard() {
  return (
    <div className="min-h-screen bg-[#f4f4f4] text-black font-mono p-3">
      <Navbar />

      <div className="grid grid-cols-2 border border-gray-500 mt-3">
        <AnalyticsPanel type="bandwidth" />
        <AnalyticsPanel type="protocol" />
      </div>

      <LogTable />
    </div>
  );
}

export default Dashboard;