import React from 'react';

export default function AcademicDocumentValidator({ validationData, onRevalidate }) {
  if (!validationData) return null;

  const issues = validationData.issues || [];
  const errors = issues.filter(i => i.severity === 'ERROR');
  const warnings = issues.filter(i => i.severity === 'WARNING');

  return (
    <div className="space-y-6 text-xs text-slate-300">

      {/* VALIDATION OVERVIEW HEADER */}
      <div className={`p-6 rounded-3xl border flex items-center justify-between gap-4 ${
        validationData.is_valid_for_submission
          ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
          : 'bg-rose-950/20 border-rose-500/40 text-rose-300'
      }`}>
        <div className="flex items-center gap-4">
          <span className="text-3xl">{validationData.is_valid_for_submission ? '🟢' : '🔴'}</span>
          <div>
            <h3 className="text-base font-black uppercase tracking-wider">
              {validationData.is_valid_for_submission ? 'DOCUMENT READY FOR FINAL SUBMISSION' : 'VALIDATION ERRORS DETECTED PRIOR TO EXPORT'}
            </h3>
            <p className="text-xs opacity-90 mt-0.5">
              {validationData.is_valid_for_submission
                ? 'All mandatory sections, citations, and empirical metric checks passed.'
                : 'Please resolve remaining structural or metric validation issues before submitting.'}
            </p>
          </div>
        </div>

        <button onClick={onRevalidate} className="btn-secondary py-2 px-4 text-xs font-bold shrink-0">
          Re-validate Document 🔄
        </button>
      </div>

      {/* METRIC BADGES */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-bold">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase block">Passed Checks</span>
          <span className="text-2xl font-black text-emerald-400">{validationData.passed_checks_count}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase block">Placeholders Found</span>
          <span className={`text-2xl font-black ${validationData.placeholders_found_count > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            {validationData.placeholders_found_count}
          </span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase block">Warnings</span>
          <span className="text-2xl font-black text-amber-400">{validationData.warnings_count}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase block">Blocking Errors</span>
          <span className={`text-2xl font-black ${validationData.errors_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {validationData.errors_count}
          </span>
        </div>
      </div>

      {/* DETAILED ISSUES LIST */}
      <div className="space-y-3">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">Document Validation Report</h4>

        {issues.length === 0 ? (
          <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-400">
            ✓ Zero validation issues detected in document layout or text.
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((iss) => (
              <div key={iss.issue_id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-slate-200 text-xs">{iss.title}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                    iss.severity === 'ERROR' ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' :
                    'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  }`}>
                    {iss.severity}
                  </span>
                </div>

                <p className="text-slate-300 text-xs">{iss.description}</p>
                <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 font-mono">
                  Location: {iss.location}
                </div>
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
