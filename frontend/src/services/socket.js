// Singleton Socket.IO client. Reused across all components so we keep a
// single connection to the backend.
import { io } from "socket.io-client";
import { SOCKET_URL } from "./api";

export const socket = io(SOCKET_URL, {
  transports: ["websocket", "polling"],
  autoConnect: true,
  reconnection: true,
  reconnectionDelay: 1000,
});
