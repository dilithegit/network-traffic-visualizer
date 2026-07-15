// Wireshark-style real-time capture timeline (req 10).
// Horizontal stream of colour-coded events (one per packet) grouped by
// protocol. Selecting an event highlights the matching row in the table and
// opens the inspector. Supports Zoom, Pause/Resume and Auto-scroll.
import { memo, useEffect, useMemo, useRef, useState } from "react";
import { ZoomIn, ZoomOut, Pause, Play, ArrowDownToLine } from "lucide-react";
import { protocolColor } from "../utils/protocolColors";

const TimelineEvent = memo(function TimelineEvent({ packet, selected, onSelect, width }) {
  const color = protocolColor(packet.layer || packet.protocol);
  return (
    <button
      type="button"
      onClick={() => onSelect(packet.id)}
      title={`${packet.time}  ${packet.src_ip} → ${packet.dst_ip}  ${packet.layer}  ${packet.size}B`}
      style={{ width, backgroundColor: color }}
      className={
        "h-10 shrink-0 rounded-sm transition " +
        (selected ? "ring-2 ring-offset-1 ring-slate-900 dark:ring-white" : "hover:brightness-110")
      }
    />
  );
});

function PacketTimelineBase({ packets, selectedId, onSelect }) {
  const [paused, setPaused] = useState(false);
  const [zoom, setZoom] = useState(7);
  const [autoScroll, setAutoScroll] = useState(true);
  const [frozen, setFrozen] = useState(packets);
  const scrollRef = useRef(null);

  // Freeze the current view when pausing (snapshot taken in the event
  // handler, not an effect, so React's render-phase rules stay happy).
  const togglePause = () =>
    setPaused((prev) => {
      const next = !prev;
      if (next) setFrozen(packets);
      return next;
    });

  const view = paused ? frozen : packets;
  const ordered = useMemo(() => view.slice().reverse(), [view]); // oldest -> newest (left->right)

  // Auto-scroll to the newest event (right edge) when enabled.
  useEffect(() => {
    if (!autoScroll || paused) return;
    const el = scrollRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  }, [ordered, autoScroll, paused]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
          Capture Timeline
        </span>
        <span className="text-[11px] text-slate-400">{view.length} events</span>
        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(2, z - 2))}
            className="rounded border border-slate-200 p-1 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label="Zoom out"
          >
            <ZoomOut size={14} />
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(28, z + 2))}
            className="rounded border border-slate-200 p-1 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label="Zoom in"
          >
            <ZoomIn size={14} />
          </button>
          <button
            type="button"
            onClick={togglePause}
            className={
              "flex items-center gap-1 rounded border px-2 py-1 text-xs font-semibold " +
              (paused
                ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-300"
                : "border-slate-200 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800")
            }
          >
            {paused ? <Play size={14} /> : <Pause size={14} />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            type="button"
            onClick={() => setAutoScroll((a) => !a)}
            className={
              "flex items-center gap-1 rounded border px-2 py-1 text-xs font-semibold " +
              (autoScroll
                ? "border-brand bg-brand/10 text-brand"
                : "border-slate-200 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800")
            }
          >
            <ArrowDownToLine size={14} />
            Auto
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="netsentry-scroll flex h-12 items-center gap-[2px] overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-800/50"
      >
        {ordered.length === 0 ? (
          <p className="px-2 text-xs text-slate-400">Awaiting packets…</p>
        ) : (
          ordered.map((p) => (
            <TimelineEvent
              key={p.id}
              packet={p}
              selected={p.id === selectedId}
              onSelect={onSelect}
              width={Math.max(3, zoom)}
            />
          ))
        )}
      </div>
    </div>
  );
}

export const PacketTimeline = memo(PacketTimelineBase);
export default PacketTimeline;
