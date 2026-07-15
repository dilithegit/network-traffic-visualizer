// Packet analysis workspace (req 8, 9, 10). Owns the live packet stream, the
// search filter, the selected-packet state and the inspector. Keeping all of
// this local means high-frequency capture updates only re-render this subtree
// — the navbar, stats cards and charts never re-render on packet activity.
import { memo, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import { usePacketStream } from "../hooks/useSocketEvents";
import { filterPackets } from "../utils/filterParser";
import Panel from "./Panel";
import SearchBar from "./SearchBar";
import PacketTimeline from "./PacketTimeline";
import PacketTable from "./PacketTable";
import PacketInspector from "./PacketInspector";

function PacketAnalysisBase() {
  const [seed, setSeed] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api
      .getTraffic()
      .then((data) => setSeed(data || []))
      .catch(() => {});
  }, []);

  // Single source of truth for the live stream (batched Socket.IO frames).
  const packets = usePacketStream("packet_batch", 400, seed);

  const filtered = useMemo(() => filterPackets(packets, query), [packets, query]);
  const selected = useMemo(
    () => packets.find((p) => p.id === selectedId) || null,
    [packets, selectedId]
  );

  const onSelect = (id) => setSelectedId((prev) => (prev === id ? null : id));

  return (
    <div className="flex flex-col gap-3">
      <SearchBar onChange={setQuery} />
      <PacketTimeline packets={packets} selectedId={selectedId} onSelect={onSelect} />
      <Panel
        title="Live Packet Log"
        description="Click a row or timeline event to inspect"
        actions={
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            {filtered.length}
            {query ? ` / ${packets.length}` : ""} shown
          </span>
        }
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PacketTable packets={filtered} selectedId={selectedId} onSelect={onSelect} />
          </div>
          <div className="lg:col-span-1">
            <div className="max-h-96">
              <PacketInspector packet={selected} onClose={() => setSelectedId(null)} />
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

export const PacketAnalysis = memo(PacketAnalysisBase);
export default PacketAnalysis;
