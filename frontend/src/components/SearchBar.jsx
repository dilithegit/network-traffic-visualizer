// Instant search/filter bar with syntax support (req 8).
// Examples: `protocol == DNS`, `ip == 192.168.1.10`, `port == 443`,
//           `host contains youtube`, `ttl > 64 and size >= 1500`.
import { memo, useEffect, useRef, useState } from "react";
import { Search, X, AlertCircle } from "lucide-react";
import { compileFilter } from "../utils/filterParser";

function SearchBarBase({ onChange }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const { predicate, error: err } = compileFilter(value);
      setError(err);
      // A null predicate means "match all" -> pass empty string to parent.
      onChange(predicate ? value : "");
    }, 180);
    return () => clearTimeout(debounceRef.current);
  }, [value, onChange]);

  const clear = () => setValue("");

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 focus-within:border-brand dark:border-slate-700 dark:bg-slate-800">
        <Search size={16} className="text-slate-400" />
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder='Filter  e.g.  protocol == DNS  ·  ip == 192.168.1.10  ·  port == 443  ·  host contains youtube'
          className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
          aria-label="Packet filter"
        />
        {value && (
          <button
            type="button"
            onClick={clear}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            aria-label="Clear filter"
          >
            <X size={16} />
          </button>
        )}
      </div>
      {error && (
        <p className="flex items-center gap-1 text-[11px] text-rose-500">
          <AlertCircle size={12} /> {error}
        </p>
      )}
    </div>
  );
}

export const SearchBar = memo(SearchBarBase);
export default SearchBar;
