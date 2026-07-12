// Provides the latest aggregated statistics (pushed every ~2s via the
// `statistics_update` Socket.IO event) to any component that needs it.
import { createContext, useContext, useEffect, useState } from "react";
import { socket } from "../services/socket";
import { api } from "../services/api";

const StatsContext = createContext(null);

export function StatsProvider({ children }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const handler = (payload) => setStats(payload);
    socket.on("statistics_update", handler);

    // Hydrate immediately so the UI is not empty before the first push.
    api
      .getStats()
      .then(setStats)
      .catch(() => {});

    return () => socket.off("statistics_update", handler);
  }, []);

  return <StatsContext.Provider value={stats}>{children}</StatsContext.Provider>;
}

export function useStats() {
  return useContext(StatsContext);
}
