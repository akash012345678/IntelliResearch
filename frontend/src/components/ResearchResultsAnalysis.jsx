import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ExperimentResultsAnalysisModal from './ExperimentResultsAnalysisModal';

export default function ResearchResultsAnalysis({ projectId, onOpenExperiments }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);

  useEffect(() => {
    fetchResultsAnalysis();
  }, [projectId]);

  const fetchResultsAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getProjectResultsAnalysis(projectId);
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to load results analysis summary:', err);
      setError('Unable to analyze project experiment results.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 mx-auto flex items-center justify-center text-indigo-400 font-bold animate-spin">
          📊
        </div>
        <p className="text-xs text-slate-400 font-bold">Synthesizing Empirical Results Analysis...</p>
      </div>
    );
  }

  const experiments = summary?.experiments_analysis || [];
  const hasRecordedResults = summary?.has_recorded_results;

  return (
    <div className="space-y-8 animate-fade-in text-xs text-slate-300">

      {/* HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
              📊 RESEARCH RESULTS ANALYSIS
            </span>
          </div>
          <h2 className="text-xl font-black text-slate-100">Evidence-Based Conclusion Engine</h2>
          <p className="text-xs text-slate-400">
            {summary?.notice || 'Understand what your recorded experiments show strictly based on student-entered empirical measurements.'}
          </p>
        </div>

        <button
          onClick={onOpenExperiments}
          className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-500/20"
        >
          <span>🧪</span> Open Experiment Workspace
        </button>
      </div>

      {/* DASHBOARD METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Total Exps</span>
          <span className="text-xl font-black text-indigo-400">{summary?.total_experiments || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Completed</span>
          <span className="text-xl font-black text-emerald-400">{summary?.completed_experiments || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Results Recorded</span>
          <span className="text-xl font-black text-purple-400">{summary?.results_recorded_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Baselines</span>
          <span className="text-xl font-black text-indigo-300">{summary?.baseline_comparisons_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Ablations</span>
          <span className="text-xl font-black text-amber-400">{summary?.ablation_experiments_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Multi-Run</span>
          <span className="text-xl font-black text-indigo-300">{summary?.multi_run_experiments_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Hypotheses</span>
          <span className="text-xl font-black text-emerald-300">{summary?.hypotheses_evaluated_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Limitations</span>
          <span className="text-xl font-black text-rose-300">{summary?.limitations_recorded_count || 0}</span>
        </div>
      </div>

      {/* EMPTY / NO RESULTS STATE */}
      {!hasRecordedResults ? (
        <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto text-2xl">
            📊
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-bold text-slate-100">Your experiments are planned, but no experimental results have been recorded yet.</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Execute your experiments externally (in Python, PyTorch, Colab, or MATLAB), then record your verified baseline and proposed metrics in the Experiment Workspace to unlock results analysis.
            </p>
          </div>
          <button
            onClick={onOpenExperiments}
            className="btn-primary py-2.5 px-6 text-xs font-bold"
          >
            🧪 Open Experiment Workspace to Record Results
          </button>
        </div>
      ) : (
        <div className="space-y-6">

          {/* PROJECT OVERALL SAFE CONCLUSION CARD */}
          <div className="p-6 rounded-3xl bg-indigo-950/20 border border-indigo-500/30 space-y-3">
            <h3 className="text-sm font-extrabold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
              <span>📝</span> Project-Wide Evidence-Based Conclusion
            </h3>
            <p className="text-slate-200 leading-relaxed font-medium text-xs">
              {summary?.project_overall_conclusion}
            </p>
          </div>

          {/* EXPERIMENT RESULTS ANALYSIS GRID */}
          <div className="space-y-3">
            <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span>🧪</span> Analyzed Experiments ({experiments.length})
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {experiments.map((ea) => (
                <div
                  key={ea.experiment_id}
                  className="glass-card rounded-3xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between space-y-4 bg-slate-900/60"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono font-bold text-[10px]">
                        {ea.experiment_type}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                        ea.evidence_strength.rating === 'STRONGER' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        ea.evidence_strength.rating === 'MODERATE' ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' :
                        'bg-amber-500/10 border-amber-500/30 text-amber-300'
                      }`}>
                        {ea.evidence_strength.rating} ({ea.evidence_strength.score}/100)
                      </span>
                    </div>

                    <h4 className="text-sm font-extrabold text-slate-100 line-clamp-2">{ea.experiment_name}</h4>
                    <p className="text-xs text-slate-400 line-clamp-2">{ea.safe_conclusion}</p>

                    <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 font-mono text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Dataset:</span>
                        <span className="text-slate-200 font-bold">{ea.dataset_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Metrics Evaluated:</span>
                        <span className="text-indigo-400 font-bold">{ea.metrics_count} Metrics ({ea.run_count} Runs)</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedAnalysis(ea)}
                    className="btn-primary py-2 px-4 text-xs font-bold w-full text-center"
                  >
                    Analyze Experiment Results →
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* CROSS-EXPERIMENT COMPARISON MATRIX TABLE */}
          {experiments.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <span>⚖</span> Cross-Experiment Empirical Comparison Matrix
              </h3>

              <div className="overflow-x-auto rounded-2xl border border-slate-800">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-bold text-[10px] uppercase">
                      <th className="p-3">Experiment</th>
                      <th className="p-3">Dataset</th>
                      <th className="p-3">Baseline vs Proposed</th>
                      <th className="p-3">Recorded Metrics</th>
                      <th className="p-3">Hypothesis Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-950/60">
                    {experiments.map((ea) => (
                      <tr key={ea.experiment_id} className="hover:bg-slate-900/50 transition-all">
                        <td className="p-3 font-bold text-slate-200">{ea.experiment_name}</td>
                        <td className="p-3 text-slate-400 font-mono">{ea.dataset_name}</td>
                        <td className="p-3 text-slate-300 font-mono">{ea.baseline_alg} → <strong className="text-indigo-400">{ea.proposed_arch}</strong></td>
                        <td className="p-3 font-mono font-bold text-purple-300">{ea.metrics_count} Metrics</td>
                        <td className="p-3">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                            ea.hypothesis_assessment.assessment_status === 'CONSISTENT_WITH_H1' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                            ea.hypothesis_assessment.assessment_status === 'CONSISTENT_WITH_H0' ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' :
                            'bg-amber-500/10 border-amber-500/30 text-amber-300'
                          }`}>
                            {ea.hypothesis_assessment.assessment_status.replace(/_/g, ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* WHAT SHOULD I DO NEXT GUIDANCE */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3">
            <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span>🎯</span> What Should I Do Next? (Research Decision Support)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {summary?.decision_guidance?.map((g, idx) => (
                <div key={idx} className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 text-slate-300 flex items-start gap-2.5">
                  <span className="text-indigo-400 font-bold">{idx + 1}.</span>
                  <span className="text-xs font-medium">{g}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* SINGLE EXPERIMENT ANALYSIS MODAL */}
      {selectedAnalysis && (
        <ExperimentResultsAnalysisModal
          analysis={selectedAnalysis}
          onClose={() => setSelectedAnalysis(null)}
        />
      )}
    </div>
  );
}
