// Traffic spike alert panel. Listens for `spike_detected` events and shows
// the most recent per-IP spikes with severity colouring.
import { memo } from "react";
import { AlertTriangle } from "lucide-react";
import { useSocketEvent } from "../hooks/useSocketEvents";
import Panel from "./Panel";

const SEVERITY_STYLES = {
  CRITICAL: "border-rose-300 bg-rose-50 dark:border-rose-500/40 dark:bg-rose-500/10",
  WARNING: "border-amber-300 bg-amber-50 dark:border-amber-500/40 dark:bg-amber-500/10",
};

function SpikeAlertPanelBase() {
  const spikes = useSocketEvent("spike_detected", 50);

  return (
    <Panel
      title="Traffic Spike Alerts"
      description="Per-IP packet/bandwidth anomalies"
      actions={
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
          {spikes.length}
        </span>
      }
    >
      <div className="netsentry-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
        {spikes.length === 0 && (
          <p className="text-sm text-slate-400">No spikes detected.</p>
        )}
        {spikes.map((s, idx) => (
          <div
            key={`${s.timestamp}-${s.src_ip}-${idx}`}
            className={
              "rounded-lg border-l-4 p-3 text-xs " +
              (SEVERITY_STYLES[s.severity] ||
                "border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50")
            }
          >
            <div className="mb-1 flex items-center gap-2">
              <AlertTriangle size={14} className="text-rose-500" />
              <span className="font-semibold text-slate-700 dark:text-slate-200">
                {s.alert}
              </span>
              <span className="ml-auto font-mono text-slate-400">{s.timestamp}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 font-mono text-slate-600 dark:text-slate-300">
              <span>
                <span className="text-slate-400">src </span>
                {s.src_ip}
              </span>
              <span>
                <span className="text-slate-400">pps </span>
                {s.packets_per_second}
              </span>
              <span>
                <span className="text-slate-400">bw </span>
                {s.bandwidth_mbps} Mb/s
              </span>
            </div>
            <span
              className={
                "mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-bold " +
                (s.severity === "CRITICAL"
                  ? "bg-rose-500 text-white"
                  : "bg-amber-500 text-white")
              }
            >
              {s.severity}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export const SpikeAlertPanel = memo(SpikeAlertPanelBase);
export default SpikeAlertPanel;
