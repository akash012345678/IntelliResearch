import React from 'react';

export default function AcademicQualityPanel({ qualityData }) {
  if (!qualityData) return null;

  const issues = qualityData.issues || [];
  const mismatches = qualityData.metric_mismatches || [];

  return (
    <div className="space-y-6 text-xs text-slate-300">

      {/* QUALITY METRIC SCORES */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Citation Traceability</span>
          <span className="text-xl font-black text-indigo-400">{qualityData.citation_traceability_score}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Evidence Coverage</span>
          <span className="text-xl font-black text-emerald-400">{qualityData.evidence_coverage_percentage}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Result Consistency</span>
          <span className={`text-xl font-black ${qualityData.result_consistency_score === 100 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {qualityData.result_consistency_score}%
          </span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Reference Integrity</span>
          <span className="text-xl font-black text-purple-400">{qualityData.reference_integrity_score}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Novelty Safety</span>
          <span className={`text-xs font-black block mt-1 ${qualityData.novelty_claim_safety === 'PASS' ? 'text-emerald-400' : 'text-amber-400'}`}>
            {qualityData.novelty_claim_safety}
          </span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Dataset Verification</span>
          <span className="text-xl font-black text-indigo-300">{qualityData.dataset_verification_score}%</span>
        </div>
      </div>

      {/* METRIC MISMATCH ALERTS */}
      {mismatches.length > 0 && (
        <div className="p-5 rounded-3xl bg-rose-950/20 border border-rose-500/40 space-y-3">
          <h4 className="text-xs font-extrabold text-rose-300 uppercase tracking-wider flex items-center gap-1.5">
            <span>🔴</span> Result Metric Mismatches Detected ({mismatches.length})
          </h4>
          <p className="text-xs text-rose-200/90">
            Draft manuscript text contains numbers that conflict with actual empirical values stored in your project database.
          </p>

          <div className="space-y-2">
            {mismatches.map((m, idx) => (
              <div key={idx} className="p-3 rounded-2xl bg-slate-950 border border-rose-500/30 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-slate-200 block">{m.metric_name}</span>
                  <span className="text-[11px] text-slate-400">{m.description}</span>
                </div>
                <div className="font-mono text-right shrink-0 space-y-0.5">
                  <span className="text-emerald-400 block font-bold">DB: {m.recorded_value}</span>
                  <span className="text-rose-400 block font-bold">Text: {m.manuscript_value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ACADEMIC QUALITY ISSUES & NOVELTY WARNINGS */}
      <div className="space-y-3">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>⚠️</span> Academic Review Warnings & Suggested Fixes ({issues.length})
        </h4>

        {issues.length === 0 ? (
          <div className="p-6 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-center font-bold">
            ✓ Zero academic review issues detected! Your manuscript adheres to cautious academic framing.
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((iss) => (
              <div key={iss.issue_id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-300">{iss.title}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                    iss.severity === 'CRITICAL' ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' :
                    'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  }`}>
                    {iss.severity}
                  </span>
                </div>

                <p className="text-slate-300 text-xs">{iss.description}</p>
                <p className="text-[11px] text-slate-400 font-mono italic bg-slate-950 p-2 rounded-xl border border-slate-800">
                  {iss.problematic_text}
                </p>

                <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-indigo-200 text-[11px]">
                  <strong>💡 Suggested Fix:</strong> {iss.suggested_fix}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
