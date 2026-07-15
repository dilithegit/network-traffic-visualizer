// Central API configuration. The backend runs on 127.0.0.1:5000 by default
// (see backend/config.py). Adjust here if deployed elsewhere.
export const API_BASE_URL = "http://127.0.0.1:5000";
export const SOCKET_URL = API_BASE_URL;

async function request(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  health: () => request("/"),

  getInterfaces: () => request("/interfaces"),

  getStatus: () => request("/capture/status"),

  startCapture: (interfaceName) =>
    request("/capture/start", {
      method: "POST",
      body: JSON.stringify({ interface: interfaceName }),
    }),

  stopCapture: () =>
    request("/capture/stop", { method: "POST" }),

  getTraffic: () => request("/traffic"),

  getStats: () => request("/stats"),

  getAlerts: () => request("/alerts"),

  getInterfaceStatuses: () => request("/interfaces"),

  getSensitivity: () => request("/sensitivity"),

  setSensitivity: (level) =>
    request("/sensitivity", {
      method: "POST",
      body: JSON.stringify({ level }),
    }),
};
