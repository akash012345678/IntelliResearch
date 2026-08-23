import React from 'react';

export default function ClaimEvidencePanel({ activeSection, onViewPaper }) {
  if (!activeSection) return null;

  const isRecorded = activeSection.evidence_level === 'RECORDED';
  const isDerived = activeSection.evidence_level === 'DERIVED';
  const isProposed = activeSection.evidence_level === 'PROPOSED';

  return (
    <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3 text-xs text-slate-300">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>🔎</span> Claim Evidence Traceability ("Where did this come from?")
        </h4>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
          isRecorded ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
          isDerived ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' :
          isProposed ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
          'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}>
          {activeSection.evidence_badge_text}
        </span>
      </div>

      <div className="space-y-2">
        <p className="text-slate-200 italic font-medium bg-slate-950/60 p-3 rounded-2xl border border-slate-800">
          "{activeSection.content.substring(0, 140)}..."
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
          <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Source Type</span>
            <span className="font-bold text-indigo-300">
              {isRecorded ? '🟢 Recorded DB Evidence' : isDerived ? '🟡 Project-Derived Synthesis' : isProposed ? '🔵 Proposed Architecture' : '🔴 Missing Evidence'}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Verification Scope</span>
            <span className="font-bold text-slate-300">Collection-Scoped Project Data</span>
          </div>
        </div>

        {activeSection.bullet_points && activeSection.bullet_points.length > 0 && (
          <div className="space-y-1 pt-1">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">Traceable Source References</span>
            <div className="space-y-1">
              {activeSection.bullet_points.map((bp, idx) => (
                <div key={idx} className="p-2 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px] text-slate-300 flex items-center justify-between">
                  <span>{bp}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
