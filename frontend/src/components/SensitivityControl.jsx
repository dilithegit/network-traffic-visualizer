// Spike-detection sensitivity selector (req 3). Switching the level retunes
// the dynamic statistical engine on the backend in real time.
import { memo, useCallback, useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import { api } from "../services/api";
import { useStats } from "../context/StatsContext";
import { useSensitivity } from "../hooks/useSocketEvents";

const LEVELS = ["low", "medium", "high"];

const DESCRIPTIONS = {
  low: "Only large deviations (z ≥ 5)",
  medium: "Balanced (z ≥ 3.5)",
  high: "Sensitive (z ≥ 2)",
};

function SensitivityControlBase() {
  const stats = useStats();
  const liveLevel = useSensitivity();
  const current = liveLevel || stats?.spike_sensitivity || "medium";
  const [busy, setBusy] = useState(false);

  const select = useCallback(
    async (level) => {
      if (level === current || busy) return;
      setBusy(true);
      try {
        await api.setSensitivity(level);
      } catch (err) {
        console.error("setSensitivity failed:", err);
      } finally {
        setBusy(false);
      }
    },
    [current, busy]
  );

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
        <SlidersHorizontal size={14} /> Spike Sensitivity
      </div>
      <div className="flex gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-800">
        {LEVELS.map((lvl) => (
          <button
            key={lvl}
            type="button"
            disabled={busy}
            onClick={() => select(lvl)}
            title={DESCRIPTIONS[lvl]}
            className={
              "flex-1 rounded-md px-2 py-1.5 text-xs font-semibold capitalize transition " +
              (lvl === current
                ? "bg-brand text-white"
                : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-700")
            }
          >
            {lvl}
          </button>
        ))}
      </div>
      <p className="text-[10px] text-slate-400">{DESCRIPTIONS[current]}</p>
    </div>
  );
}

export const SensitivityControl = memo(SensitivityControlBase);
export default SensitivityControl;
