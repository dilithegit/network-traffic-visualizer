// Reusable dashboard panel with a title, optional description and actions.
import { memo } from "react";

function PanelBase({ title, description, actions, children, className = "" }) {
  return (
    <section
      className={
        "flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm " +
        "dark:border-slate-700 dark:bg-slate-900 " +
        className
      }
    >
      {(title || actions) && (
        <header className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4 dark:border-slate-800">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-200">
              {title}
            </h3>
            {description && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {description}
              </p>
            )}
          </div>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export const Panel = memo(PanelBase);
export default Panel;
