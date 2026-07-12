// Manages capture lifecycle: interface list, active interface, running state
// and the start/stop/select actions. Switching interfaces transparently
// restarts capture on the backend without reloading the page.
import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";

export function useCaptureControl() {
  const [interfaces, setInterfaces] = useState([]);
  const [activeInterface, setActiveInterface] = useState(null);
  const [running, setRunning] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .getInterfaces()
      .then((data) => {
        setInterfaces(data.interfaces || []);
        setActiveInterface(data.active_interface || null);
      })
      .catch(() => {});
    api
      .getStatus()
      .then((data) => setRunning(!!data.running))
      .catch(() => {});
  }, []);

  const start = useCallback(async (iface) => {
    setBusy(true);
    try {
      const data = await api.startCapture(iface);
      setRunning(!!data.running);
      if (data.active_interface) setActiveInterface(data.active_interface);
    } catch (err) {
      console.error("startCapture failed:", err);
    } finally {
      setBusy(false);
    }
  }, []);

  const stop = useCallback(async () => {
    setBusy(true);
    try {
      const data = await api.stopCapture();
      setRunning(!!data.running);
    } catch (err) {
      console.error("stopCapture failed:", err);
    } finally {
      setBusy(false);
    }
  }, []);

  // Changing the interface stops the previous capture and restarts on the new
  // one. Returns to a stopped state if the start call fails.
  const selectInterface = useCallback(
    async (iface) => {
      setActiveInterface(iface);
      setBusy(true);
      try {
        await api.stopCapture().catch(() => {});
        const data = await api.startCapture(iface);
        setRunning(!!data.running);
      } catch (err) {
        console.error("selectInterface failed:", err);
        setRunning(false);
      } finally {
        setBusy(false);
      }
    },
    []
  );

  return {
    interfaces,
    activeInterface,
    running,
    busy,
    start,
    stop,
    selectInterface,
  };
}
