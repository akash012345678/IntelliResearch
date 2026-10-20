import React from 'react';

export default function ClaimEvidencePanel({ activeSection, onViewPaper }) {
  if (!activeSection) return null;

  const trace = activeSection.claim_traceability || {};
  const lvl = activeSection.evidence_level || trace.source_type || 'PROPOSED';

  const isRecorded = lvl === 'RECORDED_EVIDENCE' || lvl === 'RECORDED';
  const isDerived = lvl === 'DERIVED';
  const isProposed = lvl === 'PROPOSED';
  const isResult = lvl === 'EXPERIMENTAL_RESULT';
  const isMissing = lvl === 'MISSING';

  return (
    <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3 text-xs text-slate-300">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>🔎</span> Claim Evidence Traceability ("Where did this come from?")
        </h4>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
          isRecorded ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
          isResult ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' :
          isDerived ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' :
          isProposed ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
          'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}>
          {activeSection.evidence_badge_text || lvl}
        </span>
      </div>

      <div className="space-y-3">
        <p className="text-slate-200 italic font-medium bg-slate-950/60 p-3 rounded-2xl border border-slate-800">
          "{activeSection.content ? activeSection.content.substring(0, 160) + '...' : 'No section content.'}"
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px]">
          <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Source Type</span>
            <span className="font-bold text-indigo-300">
              {isRecorded ? '🟢 Recorded DB Evidence' : isResult ? '📊 Empirical Results DB' : isDerived ? '🟡 Derived Synthesis' : isProposed ? '🔵 Proposed Architecture' : '🔴 Missing Evidence'}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Provenance Summary</span>
            <span className="font-bold text-slate-300">
              {trace.provenance_summary || 'Derived from project database evidence.'}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-1">
            <span className="text-[9px] text-slate-500 font-bold uppercase block">Verification Scope</span>
            <span className="font-bold text-slate-300">Collection-Scoped Project Data</span>
          </div>
        </div>

        {/* SOURCE PAPERS */}
        {trace.source_paper_titles && trace.source_paper_titles.length > 0 && (
          <div className="space-y-1 pt-1">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">Source Literature Papers ({trace.source_paper_titles.length})</span>
            <div className="space-y-1">
              {trace.source_paper_titles.map((title, idx) => {
                const paperId = trace.source_papers ? trace.source_papers[idx] : null;
                return (
                  <div key={idx} className="p-2 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px] text-slate-300 flex items-center justify-between">
                    <span className="truncate">📄 Paper #{paperId || idx+1}: {title}</span>
                    {paperId && onViewPaper && (
                      <button onClick={() => onViewPaper(paperId)} className="text-[10px] text-indigo-400 font-bold hover:underline shrink-0 ml-2">
                        View Paper
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* BULLET POINTS */}
        {activeSection.bullet_points && activeSection.bullet_points.length > 0 && (
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">Traceable Section Highlights</span>
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
