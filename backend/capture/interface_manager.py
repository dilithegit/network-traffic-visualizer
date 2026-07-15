"""Network interface enumeration and selection.

Exposes friendly, Wireshark-style display names (e.g. "Wi-Fi") to the UI while
keeping the real Scapy interface identifier (the NPF device path on Windows)
internally so capture actually works. A bidirectional map lets us resolve a
display name back to the real name when the user starts a capture.
"""

from scapy.all import conf, get_if_list


# display name  ->  real scapy name
_display_to_real = {}
# real scapy name ->  display name
_real_to_display = {}


def _refresh():
    """Rebuild the name maps from Scapy's interface registry."""
    _display_to_real.clear()
    _real_to_display.clear()

    items = []
    try:
        for iface in conf.ifaces.values():
            real = getattr(iface, "name", None) or str(iface)
            friendly = getattr(iface, "description", None) or real
            items.append((real, friendly))
    except Exception:
        items = [(n, n) for n in get_if_list()]

    for real, friendly in items:
        if not real:
            continue
        display = friendly or real
        # Disambiguate duplicate display names.
        if display in _display_to_real:
            display = f"{display} ({real})"
        _display_to_real[display] = real
        _real_to_display[real] = display


def get_interface_list():
    """Return Wireshark-style display names for all interfaces."""
    _refresh()
    return sorted(_display_to_real.keys())


def resolve_interface(identifier):
    """Resolve a display name (or raw name) to the real Scapy interface name."""
    if not identifier:
        return None
    if identifier in _display_to_real:
        return _display_to_real[identifier]
    if identifier in _real_to_display:
        return identifier
    # Fall back to best-effort match (case-insensitive substring).
    lowered = identifier.lower()
    for display, real in _display_to_real.items():
        if lowered in display.lower():
            return real
    return identifier


_active_real = None


def set_active_interface(identifier):
    """Select an interface by display name or real name (internal: real)."""
    global _active_real
    _active_real = resolve_interface(identifier)


def get_active_interface_name():
    """Return the real Scapy interface name used for capture."""
    global _active_real
    if _active_real:
        return _active_real
    default = get_default_real()
    _active_real = default
    return default


def get_active_interface():
    """Return the real Scapy interface name (used for capture)."""
    return get_active_interface_name()


def get_active_interface_display():
    """Return the friendly display name of the active interface (for the UI)."""
    name = get_active_interface_name()
    return _real_to_display.get(name, name)


def get_default_interface():
    """Return the friendly display name of the default interface."""
    return _real_to_display.get(get_default_real(), get_default_real())


# Virtual / loopback markers used for classification + default selection.
_VIRTUAL_MARKERS = ("vmware", "vbox", "virtual", "docker", "npcap", "loopback")


def _is_virtual(real):
    return any(marker in real.lower() for marker in _VIRTUAL_MARKERS)


def get_interface_statuses():
    """Return detailed status for every interface (req 5).

    Each entry is a dict with the friendly ``display`` name, the real Scapy
    name, and booleans describing whether the adapter is up, a loopback, or a
    virtual/VMware adapter. This lets the UI surface informative warnings
    (e.g. a VMware adapter that is present but receives no traffic) instead of
    failing silently.
    """
    _refresh()
    statuses = []
    for real, display in _real_to_display.items():
        iface = None
        try:
            iface = conf.ifaces.get(real)
        except Exception:
            iface = None
        # scapy's NetworkInterface exposes ``status`` (1 == up, 0 == down).
        raw_status = getattr(iface, "status", None)
        is_up = raw_status in (None, 1, "up", "UP")
        is_loopback = bool(getattr(iface, "is_loopback", False)) or "loopback" in real.lower()
        statuses.append({
            "display": display,
            "real": real,
            "is_up": is_up,
            "is_loopback": is_loopback,
            "is_virtual": _is_virtual(real) and not is_loopback,
        })
    return statuses


def get_interface_details(active_real=None, active_idle=False, capture_running=False):
    """Return rich, UI-ready details for every interface (req 1, 5).

    Each entry includes the friendly/real name, up/down status, IPv4, MAC
    address, packets received/sent (via psutil when resolvable), whether Scapy
    can open the adapter, and a live ``traffic`` state for the active adapter.
    """
    try:
        import psutil
        io_counters = psutil.net_io_counters(pernic=True) or {}
    except Exception:
        io_counters = {}

    details = []
    for real, display in _real_to_display.items():
        iface = None
        try:
            iface = conf.ifaces.get(real)
        except Exception:
            iface = None

        raw_status = getattr(iface, "status", None)
        is_up = raw_status in (None, 1, "up", "UP")
        is_loopback = bool(getattr(iface, "is_loopback", False)) or "loopback" in real.lower()
        is_virtual = _is_virtual(real) and not is_loopback

        # IPv4 / MAC from scapy's interface object (best-effort).
        ipv4 = getattr(iface, "ip", "") or ""
        mac = getattr(iface, "mac", "") or ""

        # Resolve psutil per-NIC counters by real name, then friendly name.
        io = io_counters.get(real) or _find_psutil_io(io_counters, display)
        packets_recv = getattr(io, "packets_recv", None) if io else None
        packets_sent = getattr(io, "packets_sent", None) if io else None

        # Scapy lists the adapter, so it is openable in principle.
        can_capture = True

        # Live traffic state only makes sense for the adapter being captured.
        if capture_running and real == active_real:
            traffic = "Idle" if active_idle else "Active"
        else:
            traffic = "Not monitored"

        details.append({
            "display": display,
            "real": real,
            "is_up": is_up,
            "is_loopback": is_loopback,
            "is_virtual": is_virtual,
            "ipv4": ipv4,
            "mac": mac,
            "packets_recv": packets_recv,
            "packets_sent": packets_sent,
            "can_capture": can_capture,
            "traffic": traffic,
        })
    return details


def _find_psutil_io(io_counters, display):
    """Best-effort match of a scapy friendly name to a psutil NIC key."""
    if not display:
        return None
    lowered = display.lower()
    for key, val in io_counters.items():
        if key and key.lower() == lowered:
            return val
    return None


def get_default_real():
    """Pick a sane default interface, preferring an *up* physical adapter."""
    _refresh()
    statuses = get_interface_statuses()
    candidates = [s for s in statuses if s["is_up"] and not s["is_loopback"] and not s["is_virtual"]]
    preferred = candidates or [s for s in statuses if not s["is_loopback"]]
    if preferred:
        for s in preferred:
            disp = s["display"].lower()
            if "wi-fi" in disp or "ethernet" in disp or "local area" in disp:
                return s["real"]
        return preferred[0]["real"]
    reals = list(_real_to_display.keys())
    return reals[0] if reals else None
