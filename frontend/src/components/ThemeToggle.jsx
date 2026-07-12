// Light / dark theme toggle button. State is owned by ThemeContext so it
// persists across reloads via localStorage.
import { memo } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

function ThemeToggleBase() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="flex items-center justify-center rounded-lg border border-slate-200 bg-slate-50 p-2 text-slate-600 transition hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export const ThemeToggle = memo(ThemeToggleBase);
export default ThemeToggle;
