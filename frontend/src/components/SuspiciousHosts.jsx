// Suspicious hosts panel. Driven by the `suspicious_hosts` array inside the
// statistics payload; updated every ~2s without per-packet churn.
import { memo } from "react";
import { ShieldAlert } from "lucide-react";
import { useStats } from "../context/StatsContext";
import Panel from "./Panel";

const STATUS_STYLES = {
  CRITICAL: "bg-rose-500",
  WARNING: "bg-amber-500",
  NORMAL: "bg-emerald-500",
};

function SuspiciousHostsBase() {
  const stats = useStats();
  const hosts = stats?.suspicious_hosts || [];

  return (
    <Panel
      title="Suspicious Hosts"
      description="IPs that exceeded traffic thresholds"
      actions={
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
          {hosts.length}
        </span>
      }
    >
      <div className="netsentry-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
        {hosts.length === 0 && (
          <p className="text-sm text-slate-400">No suspicious hosts.</p>
        )}
        {hosts.map((host) => (
          <div
            key={host.ip}
            className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/50"
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${STATUS_STYLES[host.current_status] || STATUS_STYLES.NORMAL}`}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono font-semibold text-slate-700 dark:text-slate-200">
                {host.ip}
              </p>
              <p className="text-[11px] text-slate-400">
                {host.spike_count} spikes · peak {host.highest_bandwidth_mbps} Mb/s · {host.last_activity || "—"}
              </p>
            </div>
            <span
              className={
                "rounded px-2 py-0.5 text-[10px] font-bold " +
                (host.current_status === "CRITICAL"
                  ? "bg-rose-500 text-white"
                  : host.current_status === "WARNING"
                  ? "bg-amber-500 text-white"
                  : "bg-emerald-500 text-white")
              }
            >
              {host.current_status}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export const SuspiciousHosts = memo(SuspiciousHostsBase);
export default SuspiciousHosts;
