// Live alert feed: generic alerts (bandwidth threshold crossings, spikes and
// new domains). Newest first, auto-scrolling with a capped history.
import { memo, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { useSocketEvent } from "../hooks/useSocketEvents";
import { api } from "../services/api";
import Panel from "./Panel";

function AlertPanelBase() {
  const liveAlerts = useSocketEvent("new_alert", 100);
  const [seed, setSeed] = useState([]);

  useEffect(() => {
    api
      .getAlerts()
      .then((data) => setSeed(data.alerts || []))
      .catch(() => {});
  }, []);

  const items = liveAlerts.length ? liveAlerts : seed;

  return (
    <Panel
      title="Live Alerts"
      description="Real-time event feed"
      actions={
        <Bell size={16} className="text-slate-400" />
      }
    >
      <div className="netsentry-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
        {items.length === 0 && (
          <p className="text-sm text-slate-400">No alerts yet.</p>
        )}
        {items.map((a, idx) => (
          <div
            key={`${a.timestamp}-${idx}`}
            className="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50 p-2 text-xs dark:border-slate-800 dark:bg-slate-800/50"
          >
            <span className="font-mono text-slate-400">{a.timestamp}</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {a.alert}
            </span>
            <span className="ml-auto max-w-[50%] truncate text-right text-slate-500 dark:text-slate-400">
              {a.src_ip || a.url || `${a.mbps ?? ""} Mb/s` || ""}
            </span>
            {a.severity && (
              <span
                className={
                  "rounded px-1.5 py-0.5 text-[10px] font-bold " +
                  (a.severity === "CRITICAL"
                    ? "bg-rose-500 text-white"
                    : "bg-amber-500 text-white")
                }
              >
                {a.severity}
              </span>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

export const AlertPanel = memo(AlertPanelBase);
export default AlertPanel;
