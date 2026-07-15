// Syntax-based packet filter parser (req 8).
//
// Supports expressions such as:
//   protocol == DNS
//   ip == 192.168.1.10          (matches source OR destination)
//   src == 10.0.0.5
//   dst == 8.8.8.8
//   port == 443                 (matches source OR destination port)
//   srcport == 51234
//   dstport == 53
//   host contains youtube       (matches hostname or url)
//   mac == aa:bb:cc:dd:ee:ff
//   ttl > 64
//   size >= 1500
//
// Clauses may be combined with `and` / `or` (case-insensitive). An empty or
// invalid expression matches everything (so the live capture is never blocked).

const FIELD_ALIASES = {
  protocol: "protocol",
  proto: "protocol",
  ip: "ip",
  src: "src_ip",
  dst: "dst_ip",
  source: "src_ip",
  destination: "dst_ip",
  port: "port",
  srcport: "src_port",
  dstport: "dst_port",
  sport: "src_port",
  dport: "dst_port",
  host: "host",
  hostname: "host",
  url: "url",
  mac: "mac",
  ttl: "ttl",
  size: "size",
  len: "size",
  length: "size",
  info: "info",
  layer: "layer",
};

const OPERATORS = ["==", "!=", ">=", "<=", ">", "<", "contains", "matches", "~"];

function parseClause(token) {
  const opMatch = OPERATORS.find((op) => token.includes(` ${op} `) || token.startsWith(`${op} `));
  if (!opMatch) {
    // Allow `field value` as an implicit "contains"/"==" fallback.
    const parts = token.split(/\s+/);
    if (parts.length === 2) {
      return buildClause(parts[0], "==", parts[1]);
    }
    return null;
  }
  const [left, right] = token.split(opMatch).map((s) => s.trim());
  return buildClause(left, opMatch, right);
}

function buildClause(fieldRaw, op, valueRaw) {
  const field = FIELD_ALIASES[fieldRaw?.toLowerCase()];
  if (!field) return null;
  const value = valueRaw ?? "";
  const numeric = field === "ttl" || field === "size" || field === "src_port" || field === "dst_port" || field === "port";
  const num = numeric ? Number(value) : NaN;

  return (pkt) => {
    switch (field) {
      case "ip":
        return matchString(pkt.src_ip, op, value) || matchString(pkt.dst_ip, op, value);
      case "port":
        return matchString(String(pkt.src_port), op, value) || matchString(String(pkt.dst_port), op, value);
      case "host":
        return matchString((pkt.hostname || pkt.url || ""), op, value);
      case "mac":
        return matchString((pkt.mac_src || pkt.mac_dst || ""), op, value);
      case "src_port":
      case "dst_port":
      case "ttl":
      case "size": {
        const actual = Number(pkt[field]);
        if (Number.isNaN(num)) return false;
        return compareNumber(actual, op, num);
      }
      default:
        return matchString(String(pkt[field] ?? ""), op, value);
    }
  };
}

function matchString(actual, op, value) {
  const a = String(actual ?? "").toLowerCase();
  const v = String(value ?? "").toLowerCase();
  switch (op) {
    case "==":
      return a === v;
    case "!=":
      return a !== v;
    case "contains":
      return a.includes(v);
    case "matches":
    case "~":
      try {
        return new RegExp(v, "i").test(a);
      } catch {
        return false;
      }
    default:
      return a === v;
  }
}

function compareNumber(actual, op, value) {
  switch (op) {
    case "==":
      return actual === value;
    case "!=":
      return actual !== value;
    case ">":
      return actual > value;
    case "<":
      return actual < value;
    case ">=":
      return actual >= value;
    case "<=":
      return actual <= value;
    default:
      return actual === value;
  }
}

/**
 * Compile a filter expression into a predicate. Returns null on parse failure
 * (caller should treat null as "match all" and may surface the error).
 */
export function compileFilter(expression) {
  const expr = (expression || "").trim();
  if (!expr) return { predicate: null, error: null };

  // Split on and/or while keeping the joiner.
  const tokens = expr
    .split(/\s+(and|or)\s+/i)
    .map((t) => t.trim())
    .filter(Boolean);

  const clauses = [];
  let joiner = "and";
  for (let i = 0; i < tokens.length; i++) {
    const tok = tokens[i];
    if (tok.toLowerCase() === "and") {
      joiner = "and";
      continue;
    }
    if (tok.toLowerCase() === "or") {
      joiner = "or";
      continue;
    }
    const clause = parseClause(tok);
    if (!clause) {
      return { predicate: null, error: `Invalid clause: "${tok}"` };
    }
    clauses.push({ clause, joiner });
  }

  if (clauses.length === 0) return { predicate: null, error: null };

  const predicate = (pkt) => {
    let result = clauses[0].clause(pkt);
    for (let i = 1; i < clauses.length; i++) {
      const { clause, joiner: j } = clauses[i];
      const next = clause(pkt);
      result = j === "or" ? result || next : result && next;
    }
    return result;
  };
  return { predicate, error: null };
}

/** Convenience: filter a packet list by an expression string. */
export function filterPackets(packets, expression) {
  const { predicate } = compileFilter(expression);
  if (!predicate) return packets;
  return packets.filter(predicate);
}
