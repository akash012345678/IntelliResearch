import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ExperimentResultsAnalysisModal from './ExperimentResultsAnalysisModal';
import RecordResultModal from './RecordResultModal';

export default function ResearchResultsAnalysis({ projectId, directionId, onOpenExperiments }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeDirId, setActiveDirId] = useState(directionId || null);

  // Modals state
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [experimentToRecord, setExperimentToRecord] = useState(null);

  useEffect(() => {
    if (directionId) {
      setActiveDirId(directionId);
    }
  }, [directionId]);

  useEffect(() => {
    fetchResultsAnalysis(activeDirId);
  }, [projectId, activeDirId]);

  const fetchResultsAnalysis = async (dirId = activeDirId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getProjectResultsAnalysis(projectId, dirId);
      setSummary(res.data);
      if (!activeDirId && res.data?.opportunity_id) {
        setActiveDirId(res.data.opportunity_id);
      }
    } catch (err) {
      console.error('Failed to load results analysis summary:', err);
      setError('Unable to analyze project experiment results.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecordSuccess = () => {
    fetchResultsAnalysis(activeDirId);
  };

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 mx-auto flex items-center justify-center text-indigo-400 font-bold animate-spin">
          📊
        </div>
        <p className="text-xs text-slate-400 font-bold">Synthesizing Opportunity Results Analysis...</p>
      </div>
    );
  }

  const experiments = summary?.experiments_analysis || [];
  const hasRecordedResults = summary?.has_recorded_results;
  const savedDirections = summary?.saved_directions || [];

  return (
    <div className="space-y-8 animate-fade-in text-xs text-slate-300">

      {/* HEADER & OPPORTUNITY SCOPING */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
              📊 RESEARCH RESULTS ANALYSIS
            </span>

            {/* OPPORTUNITY PLAN SELECTOR */}
            {savedDirections.length > 0 && (
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1 text-[11px]">
                <span className="text-slate-400 font-bold">Opportunity Plan:</span>
                <select
                  value={activeDirId || ''}
                  onChange={(e) => setActiveDirId(e.target.value)}
                  className="bg-transparent font-bold text-indigo-300 outline-none cursor-pointer"
                >
                  {savedDirections.map((sd) => (
                    <option key={sd.id} value={sd.source_direction_id} className="bg-slate-950 text-slate-200">
                      {sd.title} ({sd.source_direction_id})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <h2 className="text-xl font-black text-slate-100">Evidence-Based Conclusion Engine</h2>
            <p className="text-xs text-slate-400">
              Evidence-based analysis of verified experimental results for the selected research opportunity.
            </p>
          </div>

          {/* ACTIVE OPPORTUNITY & PLAN CONTEXT BAR */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] bg-slate-900/60 p-2.5 rounded-2xl border border-slate-800 text-slate-300">
            <div>
              <span className="text-slate-500 font-bold">Opportunity:</span>{' '}
              <strong className="text-indigo-300">{summary?.opportunity_title || 'Selected Research Opportunity'}</strong>
            </div>
            <span className="text-slate-700">•</span>
            <div>
              <span className="text-slate-500 font-bold">Opp ID:</span>{' '}
              <code className="text-slate-300 font-mono">{summary?.opportunity_id || 'N/A'}</code>
            </div>
            <span className="text-slate-700">•</span>
            <div>
              <span className="text-slate-500 font-bold">Plan ID:</span>{' '}
              <code className="text-slate-300 font-mono">{summary?.research_plan_id || 'N/A'}</code>
            </div>
            <span className="text-slate-700">•</span>
            <div>
              <span className="text-slate-500 font-bold">Project:</span>{' '}
              <strong className="text-slate-200">{summary?.project_name || `Project #${projectId}`}</strong>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenExperiments && onOpenExperiments(activeDirId)}
            className="px-4 py-2 rounded-2xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-bold text-xs transition-all flex items-center gap-1.5"
          >
            <span>🧪</span> Open Experiment Workspace
          </button>
        </div>
      </div>

      {/* OPPORTUNITY DASHBOARD SUMMARY CARDS */}
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

      {/* SECTION 1: EXPERIMENTS & RESULTS CARDS LIST */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <span>🧪</span> Experiments & Results ({experiments.length})
          </h3>
          <span className="text-[10px] text-slate-400 font-bold">Planned for {summary?.opportunity_title || 'Selected Opportunity'}</span>
        </div>

        {experiments.length === 0 ? (
          <div className="p-10 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
            <span className="text-3xl block">🧪</span>
            <p className="text-xs font-bold text-slate-300">No planned experiments found for this opportunity plan.</p>
            <p className="text-[11px] text-slate-500">Go to Methodology Planner to generate and save a research methodology plan for this opportunity.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {experiments.map((ea, idx) => {
              const hasRunData = ea.run_count > 0;
              const expNum = ea.experiment_number || (idx + 1);

              return (
                <div
                  key={ea.experiment_id}
                  className="glass-card rounded-3xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between space-y-4 bg-slate-900/60"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[10px]">
                          EXP #{expNum}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono font-bold text-[9px]">
                          {ea.experiment_type}
                        </span>
                      </div>

                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                        ea.status === 'COMPLETED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        ea.status === 'IN_PROGRESS' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                        'bg-slate-800 border-slate-700 text-slate-300'
                      }`}>
                        {ea.status}
                      </span>
                    </div>

                    <h4 className="text-sm font-extrabold text-slate-100 line-clamp-2">{ea.experiment_name}</h4>
                    <p className="text-xs text-slate-400 line-clamp-2">{ea.purpose || 'No purpose description entered.'}</p>

                    <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1 font-mono text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Baseline:</span>
                        <span className="text-slate-300 font-bold truncate">{ea.baseline_alg}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Proposed:</span>
                        <span className="text-indigo-300 font-bold truncate">{ea.proposed_arch}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Dataset:</span>
                        <span className="text-slate-200 font-bold truncate">{ea.dataset_name}</span>
                      </div>
                    </div>

                    {/* METRICS & RUNS INFO */}
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono bg-slate-950/30 p-2 rounded-xl border border-slate-850">
                      <div>
                        <strong>Configured Metrics:</strong> {ea.configured_metrics?.length ? ea.configured_metrics.join(', ') : 'Precision, Recall, f1, mAP'}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 border-t border-slate-800 pt-3">
                    <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-2 h-2 rounded-full ${hasRunData ? 'bg-emerald-400' : 'bg-slate-600'}`}></span>
                        <span className="font-bold text-slate-300">
                          {hasRunData ? `${ea.run_count} Run(s) Recorded` : 'Results not recorded'}
                        </span>
                      </div>

                      {hasRunData && (
                        <button
                          onClick={() => setSelectedAnalysis(ea)}
                          className="text-indigo-400 hover:text-indigo-300 font-bold underline"
                        >
                          Analysis →
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => setExperimentToRecord(ea)}
                        className="btn-primary py-1.5 px-3 text-[11px] font-bold text-center flex items-center justify-center gap-1 shadow-md shadow-indigo-500/20"
                      >
                        <span>📝</span> Record Results
                      </button>

                      <button
                        onClick={() => onOpenExperiments && onOpenExperiments(activeDirId)}
                        className="btn-secondary py-1.5 px-3 text-[11px] font-bold text-center flex items-center justify-center gap-1"
                      >
                        <span>🧪</span> Open Exp
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: EMPTY STATE vs RECORDED RESULTS ANALYSIS */}
      {!hasRecordedResults ? (
        <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto text-2xl">
            📊
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-bold text-slate-100">
              Your experiments are planned, but no empirical results have been recorded yet.
            </h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Run the experiments externally using Python, PyTorch, Colab, MATLAB, or your preferred environment. Then record verified measurements on any experiment card above to unlock baseline comparison matrix, trade-off detection, and evidence-based conclusions.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            {experiments.length > 0 && (
              <button
                onClick={() => setExperimentToRecord(experiments[0])}
                className="btn-primary py-2.5 px-6 text-xs font-bold shadow-lg shadow-indigo-500/20"
              >
                📝 Record Experiment Results
              </button>
            )}
            <button
              onClick={() => onOpenExperiments && onOpenExperiments(activeDirId)}
              className="btn-secondary py-2.5 px-6 text-xs font-bold"
            >
              🧪 Open Experiment Workspace
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">

          {/* PROJECT OVERALL SAFE CONCLUSION CARD */}
          <div className="p-6 rounded-3xl bg-indigo-950/20 border border-indigo-500/30 space-y-3">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-2">
              <h3 className="text-sm font-extrabold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <span>📝</span> Evidence-Based Plain-Language Conclusion
              </h3>
              <span className="text-[10px] text-slate-400 font-bold font-mono">Grounded strictly in student empirical data</span>
            </div>
            <p className="text-slate-200 leading-relaxed font-medium text-xs">
              {summary?.project_overall_conclusion}
            </p>
          </div>

          {/* VISUAL BASELINE VS PROPOSED METRICS COMPARISON CHART */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <span>📈</span> Visual Empirical Comparison (Baseline vs Proposed)
              </h3>
              <div className="flex items-center gap-4 text-[10px] font-bold">
                <span className="flex items-center gap-1 text-slate-400"><span className="w-2.5 h-2.5 rounded bg-slate-700 inline-block"></span> Baseline</span>
                <span className="flex items-center gap-1 text-indigo-300"><span className="w-2.5 h-2.5 rounded bg-indigo-500 inline-block"></span> Proposed Model</span>
              </div>
            </div>

            <div className="space-y-4">
              {experiments.filter(e => e.metrics_analysis?.length > 0).map((ea) => (
                <div key={ea.experiment_id} className="space-y-3 p-4 rounded-2xl bg-slate-950/50 border border-slate-850">
                  <div className="flex items-center justify-between font-bold text-xs">
                    <span className="text-slate-200">{ea.experiment_name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{ea.dataset_name}</span>
                  </div>

                  <div className="space-y-2.5">
                    {ea.metrics_analysis.map((m, mIdx) => {
                      const bVal = parseFloat(m.baseline_value);
                      const pVal = parseFloat(m.proposed_value);
                      const hasVal = !isNaN(bVal) && !isNaN(pVal);
                      const maxVal = hasVal ? Math.max(bVal, pVal, 0.001) : 1;
                      const bPct = hasVal ? Math.min(100, Math.max(5, (bVal / maxVal) * 100)) : 0;
                      const pPct = hasVal ? Math.min(100, Math.max(5, (pVal / maxVal) * 100)) : 0;

                      return (
                        <div key={mIdx} className="space-y-1 text-[11px]">
                          <div className="flex justify-between font-mono">
                            <span className="font-bold text-slate-300">{m.metric_name}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-400">Baseline: <strong>{m.baseline_value || 'N/A'}</strong></span>
                              <span className="text-indigo-400">Proposed: <strong>{m.proposed_value || 'N/A'}</strong></span>
                              {m.rel_difference_pct && (
                                <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold ${m.is_improved ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                                  {m.rel_difference_pct}
                                </span>
                              )}
                            </div>
                          </div>

                          {hasVal && (
                            <div className="space-y-1">
                              <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden flex">
                                <div className="h-full bg-slate-700 transition-all rounded-full" style={{ width: `${bPct}%` }}></div>
                              </div>
                              <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden flex">
                                <div className="h-full bg-indigo-500 transition-all rounded-full" style={{ width: `${pPct}%` }}></div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
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
                      <th className="p-3">Evaluated Metrics</th>
                      <th className="p-3">Hypothesis Assessment</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-950/60">
                    {experiments.map((ea) => (
                      <tr key={ea.experiment_id} className="hover:bg-slate-900/50 transition-all">
                        <td className="p-3 font-bold text-slate-200">{ea.experiment_name}</td>
                        <td className="p-3 text-slate-400 font-mono">{ea.dataset_name}</td>
                        <td className="p-3 text-slate-300 font-mono">{ea.baseline_alg} → <strong className="text-indigo-400">{ea.proposed_arch}</strong></td>
                        <td className="p-3 font-mono font-bold text-purple-300">{ea.metrics_count} Metrics ({ea.run_count} Runs)</td>
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

          {/* WHAT SHOULD I DO NEXT DECISION SUPPORT */}
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

      {/* MODAL 1: RECORD RESULTS ENTRY FOR A SPECIFIC EXPERIMENT */}
      {experimentToRecord && (
        <RecordResultModal
          experiment={experimentToRecord}
          projectId={projectId}
          onClose={() => setExperimentToRecord(null)}
          onSaveSuccess={handleRecordSuccess}
        />
      )}

      {/* MODAL 2: SINGLE EXPERIMENT RESULTS ANALYSIS MODAL */}
      {selectedAnalysis && (
        <ExperimentResultsAnalysisModal
          analysis={selectedAnalysis}
          onClose={() => setSelectedAnalysis(null)}
        />
      )}
    </div>
  );
}
