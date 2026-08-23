import React from 'react';

export default function SubmissionReadinessCard({ items = [] }) {
  if (!items || items.length === 0) return null;

  const passedCount = items.filter(i => i.status === 'PASSED').length;
  const isAllPassed = passedCount === items.length;

  return (
    <div className={`p-6 rounded-3xl border space-y-4 text-xs ${
      isAllPassed ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200' : 'bg-slate-900/80 border-slate-800 text-slate-300'
    }`}>
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{isAllPassed ? '🎉' : '📦'}</span>
          <div>
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-100">
              {isAllPassed ? 'RESEARCH PROJECT COMPLETE & SUBMISSION READY' : 'FINAL SUBMISSION READINESS AUDIT'}
            </h4>
            <p className="text-[11px] text-slate-400">Itemized verification checks required before downloading final ZIP submission package.</p>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold border ${
          isAllPassed ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' : 'bg-amber-500/20 border-amber-500/40 text-amber-300'
        }`}>
          {passedCount} / {items.length} COMPLETED
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((item, idx) => (
          <div key={idx} className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-2">
            <div className="space-y-0.5">
              <span className="font-extrabold text-slate-200 block text-xs">{item.check_name}</span>
              <span className="text-[11px] text-slate-400 block">{item.explanation}</span>
            </div>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border shrink-0 ${
              item.status === 'PASSED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
              'bg-amber-500/10 border-amber-500/30 text-amber-300'
            }`}>
              {item.badge_text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
