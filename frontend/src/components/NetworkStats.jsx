// Real-time network statistics dashboard (req 4): current / peak / average
// bandwidth plus packets-per-second, bytes-per-second, active connections and
// active devices. Derives everything from the latest statistics payload.
import { memo } from "react";
import { Gauge, Activity, Radio, Users, TrendingUp, Wifi } from "lucide-react";
import { useStats } from "../context/StatsContext";

function Metric({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${accent}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="truncate text-base font-bold text-slate-800 dark:text-white">{value}</p>
        {sub && <p className="truncate text-[10px] text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}

function NetworkStatsBase() {
  const stats = useStats();
  const m = stats?.metrics || {};
  const bw = stats?.bandwidth || {};

  const fmtBps = (bps) => {
    if (!bps) return "0 b/s";
    if (bps >= 1e9) return `${(bps / 1e9).toFixed(2)} Gb/s`;
    if (bps >= 1e6) return `${(bps / 1e6).toFixed(2)} Mb/s`;
    if (bps >= 1e3) return `${(bps / 1e3).toFixed(1)} Kb/s`;
    return `${Math.round(bps)} b/s`;
  };

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <Metric
        icon={Gauge}
        label="Bandwidth (cur)"
        value={`${bw.total_mbps ?? 0} Mb/s`}
        sub={`peak ${bw.peak_mbps ?? 0}`}
        accent="bg-sky-100 text-sky-600 dark:bg-sky-500/20 dark:text-sky-300"
      />
      <Metric
        icon={TrendingUp}
        label="Avg Bandwidth"
        value={`${bw.avg_mbps ?? 0} Mb/s`}
        sub={`avg ${(bw.avg_bps ?? 0) >= 1e6 ? (bw.avg_bps / 1e6).toFixed(1) + " Mb/s" : fmtBps(bw.avg_bps ?? 0)}`}
        accent="bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300"
      />
      <Metric
        icon={Activity}
        label="Packets / sec"
        value={m.current_pps ?? 0}
        sub={`peak ${m.peak_pps ?? 0}`}
        accent="bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-300"
      />
      <Metric
        icon={Radio}
        label="Bytes / sec"
        value={fmtBps(m.current_bps ?? 0)}
        sub={`avg ${fmtBps(m.avg_bps ?? 0)}`}
        accent="bg-violet-100 text-violet-600 dark:bg-violet-500/20 dark:text-violet-300"
      />
      <Metric
        icon={Wifi}
        label="Active Conns"
        value={m.active_connections ?? 0}
        sub={`${m.active_devices ?? 0} devices`}
        accent="bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-300"
      />
      <Metric
        icon={Users}
        label="Avg Pkt Size"
        value={`${m.avg_packet_size ?? 0} B`}
        sub={`${m.total_packets ?? 0} total`}
        accent="bg-rose-100 text-rose-600 dark:bg-rose-500/20 dark:text-rose-300"
      />
    </div>
  );
}

export const NetworkStats = memo(NetworkStatsBase);
export default NetworkStats;
