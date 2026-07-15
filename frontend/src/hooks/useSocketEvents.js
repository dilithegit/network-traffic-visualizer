// React hooks that subscribe to Socket.IO events without leaking listeners.
import { useEffect, useRef, useState } from "react";
import { socket } from "../services/socket";

/**
 * Subscribe to a named Socket.IO event and keep a bounded list of the most
 * recent payloads (newest first). Suitable for low/medium frequency events
 * such as alerts, URLs and suspicious-host updates.
 */
export function useSocketEvent(eventName, maxLen = 100) {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const handler = (payload) => {
      setItems((prev) => {
        const next = [payload, ...prev];
        return next.length > maxLen ? next.slice(0, maxLen) : next;
      });
    };
    socket.on(eventName, handler);
    return () => socket.off(eventName, handler);
  }, [eventName, maxLen]);

  return items;
}

/**
 * High-frequency packet stream. The backend pushes packets as a single
 * `packet_batch` array (req 9) which we buffer and flush to React state once
 * per animation frame. This keeps the live table smooth under heavy capture
 * rates and avoids re-render storms. A legacy single `new_packet` payload is
 * also accepted so the hook keeps working against older backends.
 */
export function usePacketStream(eventName = "packet_batch", maxLen = 300, seed = []) {
  const [packets, setPackets] = useState(seed || []);
  const bufferRef = useRef([]);
  const frameRef = useRef(null);
  const seededRef = useRef(false);

  useEffect(() => {
    const flush = () => {
      frameRef.current = null;
      if (bufferRef.current.length === 0) return;
      const incoming = bufferRef.current;
      bufferRef.current = [];
      setPackets((prev) => {
        const merged = [...incoming.reverse(), ...prev];
        return merged.length > maxLen ? merged.slice(0, maxLen) : merged;
      });
    };

    const handler = (payload) => {
      if (Array.isArray(payload)) {
        for (let i = 0; i < payload.length; i++) bufferRef.current.push(payload[i]);
      } else {
        bufferRef.current.push(payload);
      }
      if (frameRef.current == null) {
        frameRef.current = requestAnimationFrame(flush);
      }
    };

    socket.on(eventName, handler);

    // One-time merge of an initial REST seed (newest first).
    if (seed && seed.length && !seededRef.current) {
      seededRef.current = true;
      setPackets((prev) => {
        const merged = [...seed.slice().reverse(), ...prev];
        return merged.length > maxLen ? merged.slice(0, maxLen) : merged;
      });
    }

    return () => {
      socket.off(eventName, handler);
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
    };
  }, [eventName, maxLen, seed]);

  return packets;
}

/** Live interface statuses (req 5): up/down, virtual, loopback flags. */
export function useInterfaceStatus() {
  const [statuses, setStatuses] = useState([]);
  useEffect(() => {
    const handler = (payload) => setStatuses(Array.isArray(payload) ? payload : []);
    socket.on("interface_status", handler);
    return () => socket.off("interface_status", handler);
  }, []);
  return statuses;
}

/** Inactive-interface warning banner state (req 5). */
export function useInterfaceWarning() {
  const [warning, setWarning] = useState(null);
  useEffect(() => {
    const onWarn = (payload) => setWarning(payload);
    const onClear = () => setWarning(null);
    socket.on("interface_warning", onWarn);
    socket.on("interface_warning_cleared", onClear);
    return () => {
      socket.off("interface_warning", onWarn);
      socket.off("interface_warning_cleared", onClear);
    };
  }, []);
  return warning;
}

/** Spike-detection sensitivity level (req 3). */
export function useSensitivity() {
  const [level, setLevel] = useState(null);
  useEffect(() => {
    const onUpdate = (payload) => setLevel(payload?.level ?? level);
    socket.on("sensitivity_updated", onUpdate);
    return () => socket.off("sensitivity_updated", onUpdate);
  }, [level]);
  return level;
}

/** Connection status indicator for the navbar. */
export function useSocketStatus() {
  const [connected, setConnected] = useState(socket.connected);

  useEffect(() => {
    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);
    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
    };
  }, []);

  return connected;
}
