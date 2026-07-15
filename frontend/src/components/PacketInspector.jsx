// Advanced packet inspection side-panel (req 7). Triggered on packet select;
// shows full Wireshark-style metadata: endpoints, MACs, ports, TTL, protocol,
// length, TCP flags, DNS/TLS/HTTP detail and a hex + ASCII payload preview.
import { memo } from "react";
import { X, Network, Cpu, Hash, ScrollText } from "lucide-react";
import { protocolColor, protocolBadge } from "../utils/protocolColors";

function Row({ label, value, mono }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 py-1.5 text-xs dark:border-slate-800">
      <span className="shrink-0 text-slate-500 dark:text-slate-400">{label}</span>
      <span className={`text-right text-slate-700 dark:text-slate-200 ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}

function PacketInspectorBase({ packet, onClose }) {
  if (!packet) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400 dark:border-slate-700">
        <ScrollText size={28} className="opacity-50" />
        <p>Select a packet to inspect its full details.</p>
      </div>
    );
  }

  const color = protocolColor(packet.layer || packet.protocol);
  const flags = (packet.flags || []).join(", ") || "—";
  const dns = packet.dns;
  const tls = packet.tls;
  const http = packet.http;

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Packet Inspector
          </h3>
          <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${protocolBadge(packet.layer || packet.protocol)}`}>
            {packet.layer || packet.protocol}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          aria-label="Close inspector"
        >
          <X size={16} />
        </button>
      </header>

      <div className="netsentry-scroll flex-1 overflow-y-auto px-4 py-2">
        <section className="mb-3">
          <h4 className="mb-1 flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
            <Network size={12} /> Endpoints
          </h4>
          <Row label="Time" value={packet.time} mono />
          <Row label="Source IP" value={packet.src_ip} mono />
          <Row label="Dest IP" value={packet.dst_ip} mono />
          <Row label="Source MAC" value={packet.mac_src} mono />
          <Row label="Dest MAC" value={packet.mac_dst} mono />
          <Row label="Source Port" value={packet.src_port} mono />
          <Row label="Dest Port" value={packet.dst_port} mono />
          <Row label="Hostname" value={packet.hostname} mono />
          <Row label="URL" value={packet.url} mono />
        </section>

        <section className="mb-3">
          <h4 className="mb-1 flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
            <Cpu size={12} /> Packet
          </h4>
          <Row label="Protocol" value={packet.protocol} />
          <Row label="Layer" value={packet.layer} />
          <Row label="Transport" value={packet.transport} />
          <Row label="IP Version" value={packet.ip_version} />
          <Row label="TTL" value={packet.ttl} mono />
          <Row label="Length" value={`${packet.size} B`} mono />
          <Row label="TCP Flags" value={flags} mono />
          <Row label="Local" value={packet.is_local ? "yes" : "no"} />
        </section>

        {dns && (
          <section className="mb-3">
            <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">DNS</h4>
            <Row label="Type" value={dns.type} />
            <Row label="Query" value={dns.query} mono />
            <Row label="Answers" value={dns.answer_count} />
            {dns.answers?.length > 0 && (
              <Row label="Resolved" value={dns.answers.join(", ")} mono />
            )}
          </section>
        )}

        {tls && (
          <section className="mb-3">
            <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">TLS / HTTPS</h4>
            <Row label="SNI" value={tls.sni} mono />
            <Row label="Version" value={tls.version} mono />
            <Row label="Handshake" value={tls.handshake_type} />
            <Row label="Cipher Suites" value={tls.cipher_suites} />
          </section>
        )}

        {http && (
          <section className="mb-3">
            <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">HTTP</h4>
            <Row label="Method" value={http.method} />
            <Row label="Host" value={http.host} mono />
            <Row label="Path" value={http.path} mono />
            {http.headers?.length > 0 && (
              <div className="mt-1 rounded bg-slate-50 p-2 font-mono text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {http.headers.map((h, i) => (
                  <div key={i}>{h}</div>
                ))}
              </div>
            )}
          </section>
        )}

        <section>
          <h4 className="mb-1 flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
            <Hash size={12} /> Payload (Hex + ASCII)
          </h4>
          {packet.payload_hex ? (
            <pre className="overflow-x-auto rounded bg-slate-900 p-2 font-mono text-[10px] leading-tight text-emerald-300">
              {packet.payload_hex}
              {"\n"}
              <span className="text-slate-400">{packet.payload_ascii}</span>
            </pre>
          ) : (
            <p className="text-xs text-slate-400">No payload (e.g. ACK/empty segment).</p>
          )}
        </section>
      </div>
    </div>
  );
}

export const PacketInspector = memo(PacketInspectorBase);
export default PacketInspector;
