// Top-level dashboard layout. Capture state lives here (via useCaptureControl)
// and is passed only to the Navbar, so high-frequency packet/stat updates
// never re-render the navigation or its controls.
import { memo } from "react";
import Navbar from "../components/Navbar";
import StatsCards from "../components/StatsCards";
import BandwidthChart from "../components/BandwidthChart";
import ProtocolChart from "../components/ProtocolChart";
import LiveURLFeed from "../components/LiveURLFeed";
import SpikeAlertPanel from "../components/SpikeAlertPanel";
import PacketTable from "../components/PacketTable";
import SuspiciousHosts from "../components/SuspiciousHosts";
import AlertPanel from "../components/AlertPanel";
import Panel from "../components/Panel";
import { useCaptureControl } from "../hooks/useCaptureControl";

function DashboardBase() {
  const capture = useCaptureControl();

  return (
    <div className="mx-auto flex min-h-screen max-w-[1400px] flex-col gap-4 p-4">
      <Navbar capture={capture} />

      <StatsCards />

      {/* Top row: bandwidth + protocol analytics */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Bandwidth Analytics" description="Throughput over time (Mb/s)">
          <BandwidthChart />
        </Panel>
        <Panel title="Protocol Distribution" description="Traffic share by protocol">
          <ProtocolChart />
        </Panel>
      </div>

      {/* Middle row: URL activity + spike alerts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <LiveURLFeed />
        <SpikeAlertPanel />
      </div>

      {/* Bottom row: live packet log + suspicious hosts + live alerts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <PacketTable />
        <SuspiciousHosts />
        <AlertPanel />
      </div>
    </div>
  );
}

export const Dashboard = memo(DashboardBase);
export default Dashboard;
