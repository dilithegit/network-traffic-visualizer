import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider } from "./context/ThemeContext";
import { StatsProvider } from "./context/StatsContext";
import Dashboard from "./pages/Dashboard";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider>
      <StatsProvider>
        <Dashboard />
      </StatsProvider>
    </ThemeProvider>
  </React.StrictMode>
);
