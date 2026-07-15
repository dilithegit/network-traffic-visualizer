// Shared protocol -> colour mapping for the table, charts and timeline (req 6, 10).
// Keys are the `layer` values produced by the backend classifier; unknown
// protocols fall back to a neutral slate so the chart/timeline auto-adapt.

export const PROTOCOL_COLORS = {
  HTTP: "#22c55e",     // green
  HTTPS: "#6366f1",    // indigo
  DNS: "#06b6d4",      // cyan / blue
  TLS: "#f97316",      // orange
  QUIC: "#a855f7",     // purple
  TCP: "#3b82f6",      // blue
  UDP: "#10b981",      // emerald
  ICMP: "#ef4444",     // red
  ICMPv6: "#ec4899",   // pink
  ARP: "#eab308",      // yellow
  SSH: "#14b8a6",      // teal
  DHCP: "#f59e0b",     // amber
  FTP: "#84cc16",      // lime
  SMTP: "#8b5cf6",     // violet
  SNMP: "#f43f5e",     // rose
  SMB: "#0891b2",      // cyan-700
  NTP: "#64748b",      // slate
};

const FALLBACK = "#94a3b8"; // slate-400

export function protocolColor(layer) {
  return PROTOCOL_COLORS[layer] || FALLBACK;
}

// Tailwind-ish badge classes (light + dark) for table chips.
export const PROTOCOL_BADGE = {
  HTTP: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
  HTTPS: "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300",
  DNS: "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-300",
  TLS: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300",
  QUIC: "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300",
  TCP: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
  UDP: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  ICMP: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
  ICMPv6: "bg-pink-100 text-pink-700 dark:bg-pink-500/20 dark:text-pink-300",
  ARP: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300",
  SSH: "bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-300",
};

export function protocolBadge(layer) {
  return (
    PROTOCOL_BADGE[layer] ||
    "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
  );
}
