// Live packet log table. Uses the rAF-batched packet stream so high capture
// rates stay smooth. Rows are memoized to avoid unnecessary re-renders.
import { memo, useEffect, useState } from "react";
import { usePacketStream } from "../hooks/useSocketEvents";
import { api } from "../services/api";
import Panel from "./Panel";

const PROTO_COLORS = {
  TCP: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
  UDP: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  ICMP: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
  QUIC: "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-500/20 dark:text-fuchsia-300",
};

const PacketRow = memo(function PacketRow({ pkt }) {
  const protoClass =
    PROTO_COLORS[pkt.protocol] ||
    "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300";
  return (
    <tr className="border-b border-slate-100 dark:border-slate-800">
      <td className="whitespace-nowrap py-1.5 pl-2 font-mono text-slate-400">
        {pkt.time}
      </td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-600 dark:text-slate-300">
        {pkt.src_ip}
      </td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-600 dark:text-slate-300">
        {pkt.dst_ip}
      </td>
      <td className="px-2">
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${protoClass}`}>
          {pkt.protocol}
        </span>
      </td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-500 dark:text-slate-400">
        {pkt.size} B
      </td>
      <td className="max-w-[220px] truncate px-2 text-slate-500 dark:text-slate-400">
        {pkt.info || pkt.layer || "—"}
      </td>
    </tr>
  );
});

function PacketTableBase() {
  const [seed, setSeed] = useState([]);

  useEffect(() => {
    api
      .getTraffic()
      .then((data) => setSeed(data || []))
      .catch(() => {});
  }, []);

  const packets = usePacketStream("new_packet", 200, seed);

  return (
    <Panel
      title="Live Packet Log"
      description="Real-time capture stream"
      actions={
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
          {packets.length} shown
        </span>
      }
    >
      <div className="netsentry-scroll max-h-96 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-white text-[10px] uppercase tracking-wide text-slate-400 dark:bg-slate-900">
            <tr>
              <th className="py-2 pl-2">Time</th>
              <th className="px-2">Source</th>
              <th className="px-2">Dest</th>
              <th className="px-2">Proto</th>
              <th className="px-2">Size</th>
              <th className="px-2">Info</th>
            </tr>
          </thead>
          <tbody>
            {packets.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-slate-400">
                  Awaiting packets…
                </td>
              </tr>
            ) : (
              packets.map((pkt) => <PacketRow key={pkt.id} pkt={pkt} />)
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

export const PacketTable = memo(PacketTableBase);
export default PacketTable;
