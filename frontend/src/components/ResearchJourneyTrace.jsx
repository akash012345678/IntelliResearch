import React from 'react';

export default function ResearchJourneyTrace({ traceNodes = [], onSelectTab }) {
  if (!traceNodes || traceNodes.length === 0) return null;

  return (
    <div className="p-4 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>🔗</span> End-to-End Evidence Traceability Flow
        </h4>
        <span className="text-[10px] text-slate-500 font-bold">Interactive Stage Trace</span>
      </div>

      <div className="flex border-b border-slate-800 overflow-x-auto gap-2 pb-2 scrollbar-none items-center">
        {traceNodes.map((node, idx) => {
          const isDone = node.status === 'COMPLETED';
          return (
            <React.Fragment key={node.id}>
              <button
                onClick={() => onSelectTab && onSelectTab(node.target_tab)}
                className={`px-3 py-1.5 rounded-2xl border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  isDone ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 font-bold hover:bg-emerald-500/20' :
                  'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${isDone ? 'bg-emerald-400' : 'bg-slate-600'}`}></span>
                <span>{node.label}</span>
                {node.count > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] font-mono">
                    {node.count}
                  </span>
                )}
              </button>
              {idx < traceNodes.length - 1 && (
                <span className="text-slate-600 font-bold text-xs">→</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
