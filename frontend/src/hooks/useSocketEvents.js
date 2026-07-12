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
 * High-frequency packet stream. Incoming packets are buffered and flushed to
 * React state once per animation frame, which keeps the live table smooth
 * even under heavy capture rates and avoids re-render storms.
 */
export function usePacketStream(eventName = "new_packet", maxLen = 200, seed = []) {
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

    const handler = (pkt) => {
      bufferRef.current.push(pkt);
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
