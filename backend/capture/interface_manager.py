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


def get_default_real():
    """Pick a sane default interface (prefer physical over loopback/virtual)."""
    _refresh()
    reals = list(_real_to_display.keys())
    preferred = [
        r
        for r in reals
        if r
        and "loopback" not in r.lower()
        and "virtual" not in r.lower()
        and "vmware" not in r.lower()
        and "vbox" not in r.lower()
    ]
    if preferred:
        # Prefer the one whose display mentions Wi-Fi/Ethernet.
        for r in preferred:
            disp = _real_to_display[r].lower()
            if "wi-fi" in disp or "ethernet" in disp or "local area" in disp:
                return r
        return preferred[0]
    return reals[0] if reals else None


def get_default_interface():
    """Return the friendly display name of the default interface."""
    return _real_to_display.get(get_default_real(), get_default_real())
