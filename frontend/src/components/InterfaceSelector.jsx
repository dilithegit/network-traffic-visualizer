// Wireshark-style interface dropdown. Selecting a new interface restarts
// capture on the backend via the parent's `onSelect` handler.
import { memo, useState } from "react";
import { ChevronDown, Network } from "lucide-react";

function InterfaceSelectorBase({ interfaces, activeInterface, busy, onSelect }) {
  const [open, setOpen] = useState(false);

  const handlePick = (iface) => {
    setOpen(false);
    if (iface !== activeInterface) onSelect(iface);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={busy}
        className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
      >
        <Network size={16} className="text-brand" />
        <span className="max-w-[160px] truncate">
          {activeInterface || "Select interface"}
        </span>
        <ChevronDown size={16} className="opacity-60" />
      </button>

      {open && (
        <ul className="netsentry-scroll absolute z-20 mt-2 max-h-64 w-64 overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-800">
          {interfaces.length === 0 && (
            <li className="px-3 py-2 text-xs text-slate-500">No interfaces found</li>
          )}
          {interfaces.map((iface) => (
            <li key={iface}>
              <button
                type="button"
                onClick={() => handlePick(iface)}
                className={
                  "block w-full truncate px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 " +
                  (iface === activeInterface
                    ? "font-semibold text-brand"
                    : "text-slate-700 dark:text-slate-200")
                }
              >
                {iface}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const InterfaceSelector = memo(InterfaceSelectorBase);
export default InterfaceSelector;
