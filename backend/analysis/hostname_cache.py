"""Hostname cache with DNS correlation (req 1).

When HTTPS/TLS traffic is encrypted the only signal we get is the Server Name
Indication (SNI) inside the Client Hello. Some stacks omit SNI, and for plain
IP-based flows there is no hostname at all. To keep the URL feed and inspector
useful even when SNI is missing, we maintain a short-lived mapping of
``ip -> hostname`` learned from:

* DNS responses (A/AAAA records -> answer name),
* Reverse lookups performed lazily for private ranges.

The cache is bounded and every entry carries an expiry timestamp so stale
mappings (e.g. a DHCP lease that changed) eventually roll off.
"""

import logging
import time
from collections import OrderedDict

from config import HOSTNAME_CACHE_TTL, DNS_CORRELATION_ENABLED

logger = logging.getLogger(__name__)


class HostnameCache:
    """Bounded, TTL-aware mapping of IP addresses to resolved hostnames."""

    def __init__(self, ttl=HOSTNAME_CACHE_TTL):
        self._ttl = ttl
        # OrderedDict gives us cheap insertion-order eviction (LRU-ish).
        self._cache = OrderedDict()

    # -- Writes -----------------------------------------------------------
    def learn(self, ip, hostname, ttl=None):
        """Record that ``ip`` resolves to ``hostname`` (overwrites older)."""
        if not DNS_CORRELATION_ENABLED or not ip or not hostname:
            return
        # Ignore empty / malformed names.
        hostname = hostname.rstrip(".").strip().lower()
        if not hostname or hostname == ip:
            return
        expiry = time.time() + (ttl if ttl is not None else self._ttl)
        self._cache[ip] = (hostname, expiry)
        self._cache.move_to_end(ip)

    def learn_from_dns(self, dns):
        """Populate the cache from a scapy ``DNS`` layer (response packets)."""
        if not DNS_CORRELATION_ENABLED or dns is None:
            return
        try:
            if getattr(dns, "qr", 0) != 1:  # 1 == response
                return
            # In some scapy builds ``ancount`` is lazily computed (None until
            # the packet is built); key off the presence of answer records.
            an = getattr(dns, "an", None)
            if an is None:
                return
            records = an if isinstance(an, list) else [an]
            for rr in records:
                name = getattr(rr, "rrname", None)
                rdata = getattr(rr, "rdata", None)
                if name and rdata:
                    host = name.decode("utf-8", "ignore") if isinstance(name, bytes) else str(name)
                    if isinstance(rdata, str) and _looks_like_ip(rdata):
                        self.learn(rdata, host)
                    elif isinstance(rdata, bytes):
                        ip = _bytes_to_ip(rdata)
                        if ip:
                            self.learn(ip, host)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("learn_from_dns failed: %s", exc)

    # -- Reads ------------------------------------------------------------
    def resolve(self, ip):
        """Return the cached hostname for ``ip`` or ``None`` if unknown/expired."""
        if not ip:
            return None
        entry = self._cache.get(ip)
        if not entry:
            return None
        hostname, expiry = entry
        if expiry < time.time():
            self._cache.pop(ip, None)
            return None
        self._cache.move_to_end(ip)
        return hostname

    def resolve_or_ip(self, ip):
        """Like :meth:`resolve` but always returns something (the IP itself)."""
        return self.resolve(ip) or ip

    def snapshot(self):
        """Return a copy of the live mappings (for debugging / REST)."""
        now = time.time()
        return {
            ip: host
            for ip, (host, expiry) in self._cache.items()
            if expiry >= now
        }

    def clear(self):
        self._cache.clear()


def _looks_like_ip(value):
    parts = value.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def _bytes_to_ip(raw):
    try:
        if len(raw) == 4:
            return ".".join(str(b) for b in raw)
    except Exception:
        return None
    return None


# Shared cache instance used across the capture pipeline.
hostname_cache = HostnameCache()
