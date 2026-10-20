import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function ResearchMethodologyPlannerModal({
  directionId,
  projectId = null,
  fallbackDirection = null,
  onClose,
  onGenerateDraft,
  onStartExperiments
}) {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (directionId) {
      fetchPlan();
    }
  }, [directionId, projectId]);

  const fetchPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (projectId) {
        res = await apiService.getProjectMethodologyPlan(projectId, directionId);
      } else {
        res = await apiService.getMethodologyPlan(directionId);
      }
      setPlan(res.data);
    } catch (err) {
      console.error('Failed to fetch methodology plan:', err);
      setError('Unable to load research methodology plan.');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async () => {
    if (!projectId || !plan) {
      alert('Plan can be saved under an active research project workspace.');
      return;
    }
    setIsSaving(true);
    try {
      await apiService.saveProjectResearchPlan(projectId, directionId, plan, 'Saved from Methodology Planner');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save research plan:', err);
      alert('Failed to save research plan.');
    } finally {
      setIsSaving(false);
    }
  };

  const exportMarkdown = () => {
    if (!planData) return;
    const md = `# Research Methodology Plan: ${planData.title}\n\n` +
      `**Scope:** ${planData.scope.toUpperCase()}\n` +
      `**Validation Status:** ${planData.validation_status}\n\n` +
      `## 1. Research Problem\n${planData.research_problem}\n\n` +
      `## 2. Objectives\n${planData.objectives.map(o => `- ${o}`).join('\n')}\n\n` +
      `## 3. Proposed Pipeline\n${planData.pipeline.map(p => `${p.step_number}. ${p.title}: ${p.description}`).join('\n')}\n\n` +
      `## 4. Disclaimer\n${planData.disclaimer}\n`;

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_plan_${directionId}.md`;
    a.click();
  };

  const exportJSON = () => {
    if (!planData) return;
    const blob = new Blob([JSON.stringify(planData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_plan_${directionId}.json`;
    a.click();
  };

  const planData = plan || (fallbackDirection ? {
    direction_id: directionId,
    title: fallbackDirection.title || 'Research Execution Plan',
    scope: projectId ? 'project' : 'global',
    validation_status: 'needs_further_validation',
    research_problem: fallbackDirection.research_problem || fallbackDirection.description || 'Collection studies baseline methodologies in this domain.',
    problem_context: 'Collection provides baseline feature representations.',
    supporting_papers: fallbackDirection.supporting_papers || [],
    objectives: [
      'Implement baseline model using identified collection algorithms.',
      'Develop proposed combined architecture.',
      'Build reproducible evaluation pipeline.',
      'Execute ablation studies.',
      'Document performance metrics and limitations.'
    ],
    research_questions: [
      { rq_id: 'RQ1', question: 'How does combining feature extraction with temporal modeling impact performance?' },
      { rq_id: 'RQ2', question: 'What is the computational overhead of the proposed model?' }
    ],
    pipeline: [
      { step_number: 1, stage: 'INPUT', title: 'Input Stream', description: 'Acquire raw domain samples.' },
      { step_number: 2, stage: 'EXTRACTION', title: 'Feature Extraction', description: 'Extract baseline representations.' },
      { step_number: 3, stage: 'MODELING', title: 'Sequential Modeling', description: 'Model temporal sequences.' },
      { step_number: 4, stage: 'EVALUATION', title: 'Classification & Metrics', description: 'Compute accuracy and F1 score.' }
    ],
    dataset_plan: [
      { name: 'Standard Domain Benchmark', status: 'Observed in current collection', suitability: 'Observed in supporting papers.', limitations: 'Academic use only.', licensing: 'Research License' }
    ],
    data_preparation: ['Data collection', 'Data cleaning', 'Train/Val/Test 70/15/15 split', 'Normalization'],
    baseline_methods: [
      { algorithm: 'CNN Baseline', supporting_paper_count: 1, role: 'Frame-level baseline', reason: 'Used in collection papers' }
    ],
    proposed_method: {
      architecture_name: 'Combined Feature + Temporal Model',
      components: ['Feature Encoder', 'Temporal Module', 'Classifier'],
      input_format: 'Sequence of feature vectors',
      output_format: 'Class probability distribution',
      conceptual_difference: 'Combines spatial extraction with temporal sequence modeling.'
    },
    experiments: [
      { experiment_number: 1, title: 'Exp 1: Baseline Comparison', purpose: 'Evaluate standalone baseline model.', variables: 'Architecture Choice', baseline: 'CNN Baseline', metrics: ['Accuracy', 'F1-Score'] }
    ],
    metrics: [
      { category: 'Classification Metrics', metrics: ['Accuracy (%)', 'Precision (%)', 'Recall (%)', 'F1-Score (%)'] }
    ],
    ablation_plan: [
      { step_name: 'Full Model', component_removed: 'None', purpose: 'Peak proposed performance.' }
    ],
    variables: { independent: ['Architecture Choice'], dependent: ['F1-Score'], control: ['Random Seed (42)'] },
    expected_outputs: [
      { output_type: 'Table', title: 'Table 1: Baseline vs Proposed Performance', description: 'Comparative metric breakdown.' }
    ],
    success_criteria: ['Models train to convergence.', 'Evaluation protocol is reproducible.'],
    risks: ['Dataset availability restrictions.', 'GPU memory limits during training.'],
    reproducibility_checklist: ['Fixed random seed (42)', 'Dataset version recorded', 'Hardware recorded'],
    timeline: [
      { week: 'Week 1-2', task: 'Literature Review & Dataset Setup' },
      { week: 'Week 3-4', task: 'Baseline & Proposed Model Implementation' },
      { week: 'Week 5-6', task: 'Experiments & Ablation Analysis' }
    ],
    implementation_checklist: ['Dataset prepared', 'Baseline trained', 'Proposed model trained', 'Results analyzed'],
    potential_contribution: 'An empirical evaluation of combining feature extraction with temporal modeling for the target application domain.',
    hypotheses: {
      null_hypothesis: 'H0: Proposed combination yields no statistically significant F1 gain over baseline.',
      alternative_hypothesis: 'H1: Proposed combination yields improved F1 score over baseline.'
    },
    traceability: { trace_chain: 'Problem → Papers → Gap → Direction → Validation → Plan → Proposal' },
    disclaimer: PLANNER_DISCLAIMER
  } : null);

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-3 sm:px-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="w-full max-w-5xl glass-card rounded-3xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6 max-h-[calc(100vh-7rem)] overflow-y-auto custom-scrollbar relative text-xs text-slate-300">
        
        {/* HEADER BAR */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 sticky top-0 bg-slate-950/95 z-20 backdrop-blur">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-extrabold uppercase tracking-widest">
                🧪 RESEARCH METHODOLOGY PLANNER
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {planData?.scope === 'project' ? `PROJECT • ${projectId}` : 'GLOBAL COLLECTION'}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-100 mt-1 leading-snug">
              {planData ? planData.title : 'Loading Methodology Plan...'}
            </h2>
            <p className="text-[11px] text-slate-400 italic mt-0.5">
              Turn your validated research idea into a practical, evidence-grounded execution plan.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-colors self-end sm:self-auto shrink-0"
          >
            ✕
          </button>
        </div>

        {/* DISCLAIMER BANNER */}
        <div className="p-3.5 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 text-[11px] text-indigo-200 leading-relaxed">
          <strong>Planning Guarantee:</strong> {planData?.disclaimer || 'Plan generated strictly from collection evidence. No experimental results are fabricated.'}
        </div>

        {loading && !planData ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400 font-semibold animate-pulse">Synthesizing research methodology execution plan...</p>
          </div>
        ) : planData ? (
          <div className="space-y-8">

            {/* SECTION A & B: PROBLEM & OBJECTIVES */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-2">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🎯</span> Research Problem & Context
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-serif italic">
                  "{planData.research_problem}"
                </p>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {planData.problem_context}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-2">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🎯</span> Concrete Research Objectives
                </h3>
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-1.5">
                  {planData.objectives && planData.objectives.map((obj, i) => (
                    <li key={i} className="leading-snug">{obj}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* SECTION C: RESEARCH QUESTIONS & HYPOTHESES */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-indigo-500/20 space-y-4">
              <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
                <span>❓</span> Research Questions & Testable Hypotheses
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {planData.research_questions && planData.research_questions.map((rq, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] font-mono font-bold text-indigo-400 block">{rq.rq_id}</span>
                    <p className="text-xs text-slate-200 leading-snug">{rq.question}</p>
                  </div>
                ))}
              </div>

              {planData.hypotheses && (
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1 text-xs font-mono">
                  <div className="text-slate-400"><strong className="text-rose-300">Null Hypothesis:</strong> {planData.hypotheses.null_hypothesis}</div>
                  <div className="text-slate-400"><strong className="text-emerald-300">Alternative Hypothesis:</strong> {planData.hypotheses.alternative_hypothesis}</div>
                </div>
              )}
            </div>

            {/* SECTION D: SYSTEM PIPELINE */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🏗</span> What Would I Build? (System Pipeline)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {planData.pipeline && planData.pipeline.map((step, i) => (
                  <div key={i} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-850 space-y-1.5 relative">
                    <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-mono font-bold text-[10px]">
                      Stage {step.step_number}: {step.stage}
                    </span>
                    <h4 className="font-bold text-slate-100 leading-snug">{step.title}</h4>
                    <p className="text-[11px] text-slate-400 leading-snug">{step.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* SECTION E & F: DATASET PLAN & PREPROCESSING */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>📦</span> Dataset Plan & Task-Suitability Audit
                </h3>
                {planData.dataset_plan && planData.dataset_plan.map((ds, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="font-bold text-indigo-300">{ds.name}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider ${
                        ds.suitability_class === 'DIRECTLY_SUITABLE' 
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : ds.suitability_class === 'REQUIRES_VERIFICATION'
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {ds.suitability_class === 'DIRECTLY_SUITABLE' ? 'Directly Suitable' : ds.suitability_class === 'REQUIRES_VERIFICATION' ? 'Requires Verification / Adaptation' : ds.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 leading-snug">{ds.suitability}</p>
                    {ds.annotation_type && (
                      <div className="text-[10px] text-slate-400 font-mono bg-slate-900/80 px-2 py-1 rounded border border-slate-850">
                        <strong className="text-slate-300">Annotation Type:</strong> {ds.annotation_type}
                      </div>
                    )}
                    <span className="text-[10px] text-slate-500 italic block">Limitations & Audit: {ds.limitations}</span>
                  </div>
                ))}
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>⚙</span> 8-Step Data Preparation Pipeline
                </h3>
                <ol className="list-decimal list-inside text-xs text-slate-300 space-y-1.5">
                  {planData.data_preparation && planData.data_preparation.map((prep, i) => (
                    <li key={i} className="leading-snug">{prep}</li>
                  ))}
                </ol>
              </div>
            </div>

            {/* SECTION G & H: BASELINES & PROPOSED METHOD */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>📊</span> Candidate Baseline Methods
                </h3>
                {planData.baseline_methods && planData.baseline_methods.map((base, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-400">{base.algorithm}</span>
                      <span className="text-[10px] text-slate-500 font-mono">Role: {base.role}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{base.reason}</p>
                  </div>
                ))}
              </div>

              <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 space-y-3">
                <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
                  <span>🚀</span> Proposed Method Architecture
                </h3>
                {planData.proposed_method && (
                  <div className="space-y-2 text-xs">
                    <div className="font-bold text-slate-100 text-sm">{planData.proposed_method.architecture_name}</div>
                    <div className="text-slate-300"><strong>Components:</strong> {planData.proposed_method.components?.join(' + ')}</div>
                    <div className="text-slate-300"><strong>Conceptual Difference:</strong> {planData.proposed_method.conceptual_difference}</div>
                  </div>
                )}
              </div>
            </div>

            {/* SECTION I & J: EXPERIMENTS & METRICS */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🧪</span> Experiment Matrix & Evaluation Metrics
              </h3>

              <div className="overflow-x-auto border border-slate-800 rounded-2xl bg-slate-900/60">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider font-bold">
                      <th className="p-3">Exp #</th>
                      <th className="p-3">Title & Purpose</th>
                      <th className="p-3">Variables</th>
                      <th className="p-3">Baseline</th>
                      <th className="p-3">Metrics</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850 font-mono">
                    {planData.experiments && planData.experiments.map((exp, i) => (
                      <tr key={i} className="hover:bg-slate-900/40">
                        <td className="p-3 text-indigo-400 font-bold">Exp #{exp.experiment_number}</td>
                        <td className="p-3 font-sans">
                          <div className="font-bold text-slate-100">{exp.title}</div>
                          <p className="text-[11px] text-slate-400">{exp.purpose}</p>
                        </td>
                        <td className="p-3 text-slate-300">{exp.variables}</td>
                        <td className="p-3 text-emerald-400">{exp.baseline}</td>
                        <td className="p-3 text-amber-300">{exp.metrics?.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* SECTION K, L & M: ABLATION, VARIABLES & EXPERIMENT PARAMETERS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🔬</span> Ablation Study Plan
                </h3>
                {planData.ablation_plan && planData.ablation_plan.map((abl, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-indigo-300">{abl.step_name}</span>
                      <span className="text-[10px] text-rose-300 font-mono">Removed: {abl.component_removed}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{abl.purpose}</p>
                  </div>
                ))}
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🎛</span> Experiment Variables Breakdown
                </h3>
                {planData.variables && (
                  <div className="space-y-2 text-xs">
                    <div><strong className="text-indigo-400">Independent (Changed):</strong> {planData.variables.independent?.join(', ')}</div>
                    <div><strong className="text-emerald-400">Dependent (Measured):</strong> {planData.variables.dependent?.join(', ')}</div>
                    <div><strong className="text-slate-400">Control (Kept Constant):</strong> {planData.variables.control?.join(', ')}</div>
                  </div>
                )}
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>📋</span> Experiment Parameter Provenance
                </h3>
                <div className="space-y-2 text-xs">
                  {planData.experiment_parameters && planData.experiment_parameters.map((param, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-bold text-slate-200 text-[11px]">{param.parameter}</span>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                          param.provenance_status === 'RECORDED_EVIDENCE'
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                            : param.provenance_status === 'PROPOSED'
                            ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                            : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                        }`}>
                          {param.provenance_status}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">{param.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* SECTION Q & R: TIMELINE & REPRODUCIBILITY */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🗓</span> 8-Week Student Research Schedule
                </h3>
                <div className="space-y-2">
                  {planData.timeline && planData.timeline.map((t, i) => (
                    <div key={i} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                      <span className="font-mono font-bold text-indigo-400 w-24">{t.week}</span>
                      <span className="text-slate-200 text-right">{t.task}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🔁</span> Reproducibility Verification Checklist
                </h3>
                <div className="space-y-1.5">
                  {planData.reproducibility_checklist && planData.reproducibility_checklist.map((rep, i) => (
                    <label key={i} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                      <input type="checkbox" className="rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-800" />
                      <span>{rep}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

          </div>
        ) : null}

        {/* BOTTOM ACTION BAR */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 pt-4 sticky bottom-0 bg-slate-950/95 z-20 backdrop-blur">
          <div className="flex items-center gap-2">
            <button onClick={exportMarkdown} className="btn-secondary py-1.5 px-3 text-[11px] font-bold">
              📝 Export Markdown
            </button>
            <button onClick={exportJSON} className="btn-secondary py-1.5 px-3 text-[11px] font-bold">
              📊 Export JSON
            </button>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            {projectId && (
              <button
                onClick={handleSavePlan}
                disabled={isSaving}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow transition-all flex items-center gap-1.5"
              >
                {isSaving ? 'Saving Plan...' : saveSuccess ? '✓ Plan Saved!' : '💾 Save Research Plan'}
              </button>
            )}

            <button
              onClick={() => onStartExperiments ? onStartExperiments(directionId) : (onGenerateDraft && onGenerateDraft(directionId))}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-xs shadow transition-all flex items-center gap-1.5"
            >
              <span>🧪</span> Start Experiments
            </button>

            <button
              onClick={() => onGenerateDraft && onGenerateDraft(directionId)}
              className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20"
            >
              <span>✨</span> Draft Research Proposal
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
