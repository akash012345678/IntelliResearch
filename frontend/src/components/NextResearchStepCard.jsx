import React from 'react';

export default function NextResearchStepCard({ nextStep, onTakeAction }) {
  if (!nextStep) return null;

  return (
    <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-950/60 via-slate-900/90 to-purple-950/50 border border-indigo-500/30 space-y-4 shadow-xl text-xs text-slate-300">

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-indigo-500/20 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎯</span>
          <div>
            <span className="text-[10px] text-indigo-300 font-extrabold uppercase tracking-wider block">RECOMMENDED NEXT STEP</span>
            <h3 className="text-base font-black text-slate-100">{nextStep.recommended_action_title}</h3>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-bold text-[10px]">
          {nextStep.stage_title}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-slate-200 leading-relaxed font-medium">
          "{nextStep.why_this_matters}"
        </p>

        {nextStep.completed_prerequisites && nextStep.completed_prerequisites.length > 0 && (
          <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800 text-[11px] space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Prerequisites Completed</span>
            <div className="flex flex-wrap gap-2">
              {nextStep.completed_prerequisites.map((pr, idx) => (
                <span key={idx} className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span>✓</span> {pr}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="text-[11px] text-slate-400">
            Expected Outcome: <strong className="text-slate-200">{nextStep.expected_outcome}</strong>
          </div>

          <button
            onClick={() => onTakeAction && onTakeAction(nextStep.target_tab)}
            className="btn-primary py-2.5 px-5 text-xs font-bold shadow-lg shadow-indigo-500/20 flex items-center gap-2"
          >
            <span>🚀</span> {nextStep.action_button_label}
          </button>
        </div>
      </div>

    </div>
  );
}
