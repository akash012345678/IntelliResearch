import React from 'react';
import StudentHelpTooltip from './StudentHelpTooltip';

export default function ResearchProjectHealth({ health }) {
  if (!health) return null;

  return (
    <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 text-xs text-slate-300">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <span>📊</span> Research Project Health & Readiness
          <StudentHelpTooltip
            title="Project Health Calculation"
            explanation={health.calculation_explanation || "Calculated as a deterministic weighted average of paper evidence coverage, citation completeness, and manuscript readiness."}
          />
        </h4>

        <div className="text-right">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Overall Readiness</span>
          <span className="text-xl font-black text-indigo-400">{health.overall_readiness_score}%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Evidence Completeness</span>
          <span className="text-lg font-black text-emerald-400">{health.evidence_completeness_percentage}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Citation Traceability</span>
          <span className="text-lg font-black text-indigo-400">{health.citation_completeness_percentage}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Results Consistency</span>
          <span className="text-lg font-black text-purple-400">{health.experiment_completeness_percentage}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Dataset Verification</span>
          <span className="text-lg font-black text-amber-400">{health.reproducibility_percentage}%</span>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Document Readiness</span>
          <span className="text-lg font-black text-emerald-300">{health.document_readiness_percentage}%</span>
        </div>
      </div>
    </div>
  );
}
