// Shows live connection + capture status as a colored pill.
import { memo } from "react";

function StatusIndicatorBase({ running, connected }) {
  const label = !connected ? "DISCONNECTED" : running ? "ACTIVE" : "IDLE";
  const color = !connected
    ? "bg-rose-500"
    : running
    ? "bg-emerald-500"
    : "bg-amber-500";

  return (
    <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold tracking-wide text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      STATUS&nbsp;●&nbsp;{label}
    </div>
  );
}

export const StatusIndicator = memo(StatusIndicatorBase);
export default StatusIndicator;
