// Inactive-interface warning banner (req 5). Surfaces a clear, actionable
// message when a running adapter goes silent (e.g. a disconnected VMware
// adapter) instead of freezing silently.
import { memo } from "react";
import { AlertTriangle, WifiOff } from "lucide-react";
import { useInterfaceWarning } from "../hooks/useSocketEvents";

function InterfaceWarningBannerBase() {
  const warning = useInterfaceWarning();
  if (!warning) return null;
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
      <WifiOff size={18} className="mt-0.5 shrink-0" />
      <div>
        <p className="flex items-center gap-2 font-semibold">
          <AlertTriangle size={14} /> No traffic on {warning.interface}
        </p>
        <p className="text-xs opacity-90">{warning.message}</p>
      </div>
    </div>
  );
}

export const InterfaceWarningBanner = memo(InterfaceWarningBannerBase);
export default InterfaceWarningBanner;
