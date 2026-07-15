// Live packet log table. Receives the (already filtered) packet list and the
// selected id from its parent so selection + filtering never re-render the
// rest of the dashboard (req 9). Rows are memoized; clicking a row selects it
// for the inspector and the timeline (req 7, 10).
import { memo } from "react";
import { protocolColor, protocolBadge } from "../utils/protocolColors";

const PacketRow = memo(function PacketRow({ pkt, selected, onSelect }) {
  const protoClass = protocolBadge(pkt.layer || pkt.protocol);
  return (
    <tr
      onClick={() => onSelect(pkt.id)}
      className={
        "cursor-pointer border-b border-slate-100 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50 " +
        (selected ? "bg-brand/10 dark:bg-brand/20" : "")
      }
    >
      <td className="whitespace-nowrap py-1.5 pl-2 font-mono text-slate-400">{pkt.time}</td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-600 dark:text-slate-300">
        <span className="inline-block h-2 w-2 rounded-full align-middle" style={{ backgroundColor: protocolColor(pkt.layer || pkt.protocol) }} />{" "}
        {pkt.src_ip}
      </td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-600 dark:text-slate-300">
        {pkt.dst_ip}
        {pkt.dst_port ? <span className="text-slate-400">:{pkt.dst_port}</span> : null}
      </td>
      <td className="px-2">
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${protoClass}`}>
          {pkt.layer || pkt.protocol}
        </span>
      </td>
      <td className="whitespace-nowrap px-2 font-mono text-slate-500 dark:text-slate-400">
        {pkt.size} B
      </td>
      <td className="max-w-[220px] truncate px-2 text-slate-500 dark:text-slate-400">
        {pkt.url || pkt.hostname || pkt.info || "—"}
      </td>
    </tr>
  );
});

function PacketTableBase({ packets, selectedId, onSelect }) {
  return (
    <div className="netsentry-scroll max-h-96 overflow-y-auto">
      <table className="w-full text-left text-xs">
        <thead className="sticky top-0 z-10 bg-white text-[10px] uppercase tracking-wide text-slate-400 dark:bg-slate-900">
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
            packets.map((pkt) => (
              <PacketRow key={pkt.id} pkt={pkt} selected={pkt.id === selectedId} onSelect={onSelect} />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export const PacketTable = memo(PacketTableBase);
export default PacketTable;
