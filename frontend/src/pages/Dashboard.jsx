// Top-level dashboard layout (req 4, 5, 8, 9, 10). Capture state lives here
// (via useCaptureControl) and is passed only to the Navbar, so packet/stat
// updates never re-render the navigation. The live packet stream, selection
// and search live inside <PacketAnalysis>, keeping high-frequency updates
// isolated from the rest of the UI.
import { memo } from "react";
import Navbar from "../components/Navbar";
import StatsCards from "../components/StatsCards";
import NetworkStats from "../components/NetworkStats";
import BandwidthChart from "../components/BandwidthChart";
import ProtocolChart from "../components/ProtocolChart";
import LiveURLFeed from "../components/LiveURLFeed";
import SpikeAlertPanel from "../components/SpikeAlertPanel";
import SuspiciousHosts from "../components/SuspiciousHosts";
import AlertPanel from "../components/AlertPanel";
import SensitivityControl from "../components/SensitivityControl";
import InterfaceWarningBanner from "../components/InterfaceWarningBanner";
import PacketAnalysis from "../components/PacketAnalysis";
import Panel from "../components/Panel";
import { useCaptureControl } from "../hooks/useCaptureControl";

function DashboardBase() {
  const capture = useCaptureControl();

  return (
    <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-4 p-4">
      <Navbar capture={capture} />

      <StatsCards />
      <NetworkStats />
      <InterfaceWarningBanner />

      {/* Analytics row: bandwidth + dynamic protocol distribution */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Bandwidth Analytics" description="Throughput over time (Mb/s)">
          <BandwidthChart />
        </Panel>
        <Panel title="Protocol Distribution" description="Auto-discovered traffic share">
          <ProtocolChart />
        </Panel>
      </div>

      {/* URL activity + spike alerts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <LiveURLFeed />
        <SpikeAlertPanel />
      </div>

      {/* Live packet workspace: search, timeline, table + inspector */}
      <PacketAnalysis />

      {/* Hosts, alerts and detector tuning */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SuspiciousHosts />
        <AlertPanel />
        <Panel title="Detection Settings" description="Tune the statistical spike engine">
          <SensitivityControl />
        </Panel>
      </div>
    </div>
  );
}

export const Dashboard = memo(DashboardBase);
export default Dashboard;
