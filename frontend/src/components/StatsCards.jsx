// Summary metric cards derived from the latest statistics payload.
import { memo } from "react";
import { Activity, Gauge, Radio, TrendingUp, Users, Wifi } from "lucide-react";
import { useStats } from "../context/StatsContext";

function Card({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accent}`}>
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="truncate text-lg font-bold text-slate-800 dark:text-white">
          {value}
        </p>
        {sub && <p className="truncate text-[11px] text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}

function StatsCardsBase() {
  const stats = useStats();
  const metrics = stats?.metrics || {};
  const bandwidth = stats?.bandwidth || {};
  const iface = stats?.active_interface || "—";

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <Card
        icon={Activity}
        label="Packets"
        value={metrics.total_packets ?? 0}
        sub={`${metrics.buffered_packets ?? 0} buffered`}
        accent="bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300"
      />
      <Card
        icon={Gauge}
        label="Throughput"
        value={`${bandwidth.total_mbps ?? 0} Mb/s`}
        sub={`peak ${bandwidth.peak_mbps ?? 0}`}
        accent="bg-sky-100 text-sky-600 dark:bg-sky-500/20 dark:text-sky-300"
      />
      <Card
        icon={TrendingUp}
        label="Avg Pkt"
        value={`${metrics.avg_packet_size ?? 0} B`}
        sub={`${(metrics.kbps ?? 0).toFixed(1)} Kb/s`}
        accent="bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-300"
      />
      <Card
        icon={Users}
        label="High IPs"
        value={bandwidth.consumer_count ?? 0}
        sub={`${stats?.suspicious_hosts?.length ?? 0} suspicious`}
        accent="bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-300"
      />
      <Card
        icon={Wifi}
        label="Interface"
        value={iface}
        sub={stats?.capture_active ? "capturing" : "idle"}
        accent="bg-violet-100 text-violet-600 dark:bg-violet-500/20 dark:text-violet-300"
      />
      <Card
        icon={Radio}
        label="Host"
        value={stats?.hostname || "—"}
        accent="bg-rose-100 text-rose-600 dark:bg-rose-500/20 dark:text-rose-300"
      />
    </div>
  );
}

export const StatsCards = memo(StatsCardsBase);
export default StatsCards;
