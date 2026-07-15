// Active network flow tracker panel (req 5). Shows grouped conversations with
// hostname, direction/type, duration, live speed and total transferred volume,
// so users can immediately see what is consuming bandwidth (downloads, streams).
import { memo } from "react";
import { ArrowDown, ArrowUp, Radio, Globe } from "lucide-react";
import { useStats } from "../context/StatsContext";
import { protocolColor } from "../utils/protocolColors";
import Panel from "./Panel";

const TYPE_STYLES = {
  Download: "bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300",
  Upload: "bg-violet-100 text-violet-700 dark:bg-violet-500/20 dark:text-violet-300",
  Streaming: "bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300",
  Transfer: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
};

function fmtBytes(bytes) {
  if (!bytes) return "0 B";
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
  return `${bytes} B`;
}

function fmtDuration(sec) {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  if (h) return `${h}:${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

function FlowRow({ flow }) {
  const isDown = flow.type === "Download" || flow.type === "Streaming";
  const color = protocolColor(flow.protocol);
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/50">
      <div className="mb-1 flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <span
          className={
            "rounded px-1.5 py-0.5 text-[10px] font-bold " +
            (TYPE_STYLES[flow.type] || TYPE_STYLES.Transfer)
          }
        >
          {flow.type}
        </span>
        <span className="flex items-center gap-1 truncate font-medium text-slate-700 dark:text-slate-200">
          <Globe size={12} className="shrink-0 text-brand" />
          {flow.hostname}
        </span>
        <span className="ml-auto flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-200">
          {isDown ? <ArrowDown size={13} className="text-sky-500" /> : <ArrowUp size={13} className="text-violet-500" />}
          {flow.current_mbps} Mb/s
        </span>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-0.5 font-mono text-[11px] text-slate-500 dark:text-slate-400">
        <span>{flow.src_ip} → {flow.dst_ip}</span>
        <span>{flow.protocol}</span>
        <span>⏱ {fmtDuration(flow.duration)}</span>
        <span>{fmtBytes(flow.total_bytes)}</span>
      </div>
    </div>
  );
}

function FlowTrackerPanelBase() {
  const stats = useStats();
  const flows = stats?.flows || [];

  return (
    <Panel
      title="Active Network Flows"
      description="Grouped conversations with live speed & volume"
      actions={
        <span className="flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
          <Radio size={12} /> {flows.length}
        </span>
      }
    >
      <div className="netsentry-scroll max-h-80 space-y-2 overflow-y-auto pr-1">
        {flows.length === 0 ? (
          <p className="text-sm text-slate-400">No active flows yet.</p>
        ) : (
          flows.map((flow, idx) => (
            <FlowRow key={`${flow.src_ip}-${flow.dst_ip}-${flow.service_port}-${idx}`} flow={flow} />
          ))
        )}
      </div>
    </Panel>
  );
}

export const FlowTrackerPanel = memo(FlowTrackerPanelBase);
export default FlowTrackerPanel;
