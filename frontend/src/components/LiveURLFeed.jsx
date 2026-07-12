// Live URL activity feed: shows detected HTTP URLs and HTTPS SNI values.
// Seeds from the REST /alerts endpoint then listens for `new_url` events.
import { memo, useEffect, useState } from "react";
import { Globe } from "lucide-react";
import { useSocketEvent } from "../hooks/useSocketEvents";
import { api } from "../services/api";
import Panel from "./Panel";

function LiveURLFeedBase() {
  const liveUrls = useSocketEvent("new_url", 100);
  const [seed, setSeed] = useState([]);

  useEffect(() => {
    api
      .getAlerts()
      .then((data) => setSeed(data.url_history || []))
      .catch(() => {});
  }, []);

  const items = liveUrls.length ? liveUrls : seed;

  return (
    <Panel
      title="Live URL Activity"
      description="HTTP hosts and HTTPS SNI (TLS) detections"
    >
      <div className="netsentry-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
        {items.length === 0 && (
          <p className="text-sm text-slate-400">No URLs detected yet.</p>
        )}
        {items.map((item, idx) => (
          <div
            key={`${item.timestamp}-${idx}`}
            className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/50"
          >
            <div className="mb-1 flex items-center gap-2 text-slate-500 dark:text-slate-400">
              <Globe size={13} className="text-brand" />
              <span className="font-mono">{item.timestamp}</span>
              <span
                className={
                  "ml-auto rounded px-1.5 py-0.5 text-[10px] font-semibold " +
                  (item.protocol === "HTTPS"
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                    : "bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300")
                }
              >
                {item.protocol}
              </span>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-slate-700 dark:text-slate-200">
              <span>{item.src_ip}</span>
              <span className="text-slate-400">→</span>
              <span>{item.dst_ip}</span>
            </div>
            <p className="mt-1 break-all font-medium text-brand">{item.url}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export const LiveURLFeed = memo(LiveURLFeedBase);
export default LiveURLFeed;
