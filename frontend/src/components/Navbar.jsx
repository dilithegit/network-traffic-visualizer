// Top navigation bar for NETSENTRY: brand, interface selector, status,
// start/stop controls and theme toggle. Capture state is provided by the
// parent (Dashboard) via the useCaptureControl hook so the navbar never
// re-renders on packet updates.
import { memo } from "react";
import { ShieldCheck, Play, Square } from "lucide-react";
import InterfaceSelector from "./InterfaceSelector";
import StatusIndicator from "./StatusIndicator";
import ThemeToggle from "./ThemeToggle";
import { useSocketStatus } from "../hooks/useSocketEvents";

function NavbarBase({ capture }) {
  const connected = useSocketStatus();
  const { interfaces, activeInterface, running, busy, start, stop, selectInterface } = capture;

  return (
    <header className="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/90 px-5 py-3 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white">
          <ShieldCheck size={22} />
        </div>
        <div>
          <h1 className="text-lg font-extrabold tracking-tight text-slate-800 dark:text-white">
            NET<span className="text-brand">SENTRY</span>
          </h1>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Real-time LAN traffic monitor
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <InterfaceSelector
          interfaces={interfaces}
          activeInterface={activeInterface}
          busy={busy}
          onSelect={selectInterface}
        />
        <StatusIndicator running={running} connected={connected} />
        {running ? (
          <button
            type="button"
            onClick={stop}
            disabled={busy}
            className="flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-60"
          >
            <Square size={15} /> STOP
          </button>
        ) : (
          <button
            type="button"
            onClick={() => start(activeInterface)}
            disabled={busy || !activeInterface}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
          >
            <Play size={15} /> START
          </button>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}

export const Navbar = memo(NavbarBase);
export default Navbar;
