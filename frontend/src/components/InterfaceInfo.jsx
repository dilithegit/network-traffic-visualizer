// Per-interface detail panel (req 1, 5). Shows every adapter with its status,
// IPv4, MAC, packet counts and whether Scapy can capture from it, plus a live
// traffic state for the active adapter. Surfaces VMware adapters clearly
// instead of failing silently.
import { memo, useEffect, useState } from "react";
import { Network, ArrowDownToLine, ArrowUpFromLine, WifiOff, CheckCircle2 } from "lucide-react";
import { api } from "../services/api";
import { useInterfaceStatus } from "../hooks/useSocketEvents";

function fmtPackets(n) {
  if (n == null) return "—";
  return n.toLocaleString();
}

function InterfaceCard({ iface }) {
  const up = iface.is_up;
  const traffic = iface.traffic || "Not monitored";
  const trafficColor =
    traffic === "Active"
      ? "text-emerald-600 dark:text-emerald-300"
      : traffic === "Idle" || traffic === "No packets"
      ? "text-amber-600 dark:text-amber-300"
      : "text-slate-400";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center gap-2">
        <Network size={14} className={up ? "text-brand" : "text-slate-400"} />
        <span className="truncate font-semibold text-slate-700 dark:text-slate-200">
          {iface.display}
        </span>
        <span
          className={
            "ml-auto rounded px-1.5 py-0.5 text-[10px] font-bold " +
            (up
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
              : "bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300")
          }
        >
          {up ? "UP" : "DOWN"}
        </span>
      </div>

      <dl className="mt-2 space-y-0.5 text-slate-500 dark:text-slate-400">
        <div className="flex justify-between gap-2">
          <dt>IPv4</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-200">{iface.ipv4 || "—"}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>MAC</dt>
          <dd className="truncate font-mono text-slate-700 dark:text-slate-200">{iface.mac || "—"}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="flex items-center gap-1">
            <ArrowDownToLine size={11} /> Recv
          </dt>
          <dd className="font-mono text-slate-700 dark:text-slate-200">{fmtPackets(iface.packets_recv)}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="flex items-center gap-1">
            <ArrowUpFromLine size={11} /> Sent
          </dt>
          <dd className="font-mono text-slate-700 dark:text-slate-200">{fmtPackets(iface.packets_sent)}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>Capture</dt>
          <dd className="flex items-center gap-1 text-slate-700 dark:text-slate-200">
            {iface.can_capture ? (
              <CheckCircle2 size={12} className="text-emerald-500" />
            ) : (
              <WifiOff size={12} className="text-rose-500" />
            )}
            {iface.can_capture ? "Yes" : "No"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>Traffic</dt>
          <dd className={`font-semibold ${trafficColor}`}>{traffic}</dd>
        </div>
      </dl>
    </div>
  );
}

function InterfaceInfoBase() {
  const statuses = useInterfaceStatus();
  const [seed, setSeed] = useState([]);

  useEffect(() => {
    api
      .getInterfaceStatuses()
      .then((data) => setSeed(data.statuses || []))
      .catch(() => {});
  }, []);

  const items = statuses.length ? statuses : seed;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {items.length === 0 ? (
        <p className="col-span-full text-sm text-slate-400">No interfaces found.</p>
      ) : (
        items.map((iface) => <InterfaceCard key={iface.real || iface.display} iface={iface} />)
      )}
    </div>
  );
}

export const InterfaceInfo = memo(InterfaceInfoBase);
export default InterfaceInfo;
