import Navbar from "../components/Navbar";
import BandwidthChart from "../components/BandwidthChart";
import ProtocolChart from "../components/ProtocolChart";
import LiveLogTable from "../components/LiveLogTable";

function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-100 p-2 font-mono text-sm">
      <div className="border border-black bg-white">

        <Navbar />

        {/* Analytics Section */}
        <div className="grid grid-cols-2 border-t border-black">
          <div className="border-r border-black p-2">
            <h2 className="uppercase text-xs mb-2">Bandwidth Analytics</h2>
            <div className="border border-dashed border-gray-500 h-48 p-2">
              <BandwidthChart />
            </div>
          </div>

          <div className="p-2">
            <h2 className="uppercase text-xs mb-2">Protocol Distribution</h2>
            <div className="border border-dashed border-gray-500 h-48 p-2">
              <ProtocolChart />
            </div>
          </div>
        </div>

        {/* Live Log Feed */}
        <div className="border-t border-black p-2">
          <h2 className="uppercase text-xs mb-2">Live Log Feed</h2>
          <LiveLogTable />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;