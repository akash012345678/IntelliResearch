import React, { useState } from 'react';

export default function StudentHelpTooltip({ title, explanation }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="inline-block relative">
      <button
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-extrabold hover:bg-indigo-500/30 transition-all border border-indigo-500/30"
        title="What does this mean?"
      >
        ?
      </button>

      {open && (
        <div className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 p-3 rounded-2xl bg-slate-950 border border-slate-700 shadow-2xl text-slate-200 text-[11px] leading-relaxed animate-fade-in pointer-events-none">
          <strong className="text-indigo-300 font-bold block mb-0.5">{title}</strong>
          <p className="text-slate-300">{explanation}</p>
        </div>
      )}
    </span>
  );
}
