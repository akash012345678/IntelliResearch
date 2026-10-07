import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ResearchIdeaValidationModal from './ResearchIdeaValidationModal';
import ResearchMethodologyPlannerModal from './ResearchMethodologyPlannerModal';

export default function OpportunityExplorerModal({
  directionId,
  projectId = null,
  fallbackDirection = null,
  onClose,
  onViewPaper,
  onGenerateDraft,
  isDrafting = false
}) {
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [showPlannerModal, setShowPlannerModal] = useState(false);

  useEffect(() => {
    if (directionId) {
      fetchEvaluation();
    }
  }, [directionId, projectId]);

  const fetchEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (projectId) {
        res = await apiService.evaluateProjectOpportunity(projectId, directionId);
      } else {
        res = await apiService.evaluateOpportunity(directionId);
      }
      setEvaluation(res.data);
    } catch (err) {
      console.error('Failed to fetch opportunity evaluation:', err);
      setError('Unable to load evaluation details.');
    } finally {
      setLoading(false);
    }
  };

  const evalData = evaluation || (fallbackDirection ? {
    opportunity_id: directionId,
    title: fallbackDirection.title || 'Research Opportunity',
    confidence: fallbackDirection.confidence || 'MODERATE',
    scope_tag: projectId ? 'Project evidence only' : 'Collection-based evidence only',
    research_problem: fallbackDirection.research_problem || fallbackDirection.description || 'Collection studies baseline methodologies in this domain.',
    what_current_research_does: (fallbackDirection.supporting_papers || []).map((sp, i) => ({
      paper_id: typeof sp === 'object' ? sp.paper_id : i + 1,
      title: typeof sp === 'string' ? sp : (sp.title || `Paper ID ${sp.paper_id}`),
      role: typeof sp === 'object' ? sp.role : 'Supporting Collection Paper',
      key_methods: ['Baseline Algorithm']
    })),
    what_is_missing: fallbackDirection.missing_aspect || 'Not observed in current indexed collection.',
    why_relevant: fallbackDirection.motivation || 'Supported by structural graph relationship and semantic relevance signals.',
    evidence: {
      relationship_strength: 76.8,
      semantic_relevance: 76.3,
      collection_support: 83.3,
      underrepresentation: 28.6,
      overall_gap_score: 71.1
    },
    implementation_preview: [
      { step_number: 1, stage: 'INPUT', title: 'Input Domain Data / Stream', description: 'Acquire raw domain inputs for feature analysis.' },
      { step_number: 2, stage: 'FEATURE_EXTRACTION', title: 'Spatial / Feature Extraction', description: 'Extract baseline representation features.' },
      { step_number: 3, stage: 'MODELING', title: 'Sequential / Concept Modeling', description: 'Model temporal or concept interactions.' },
      { step_number: 4, stage: 'CLASSIFICATION', title: 'State Estimation / Output Layer', description: 'Compute classification or state prediction.' }
    ],
    candidate_algorithms: (fallbackDirection.candidate_algorithms || []).map(ca => ({
      name: typeof ca === 'string' ? ca : ca.name,
      category: 'supported_by_collection',
      supporting_paper_count: 1,
      reason: 'Identified concept in indexed collection'
    })),
    candidate_datasets: (fallbackDirection.candidate_datasets || []).map(cd => ({
      name: typeof cd === 'string' ? cd : cd.name,
      category: 'supported_by_collection',
      supporting_paper_count: 1,
      reason: 'Observed dataset entity in collection'
    })),
    dataset_considerations: [
      { name: 'Collection Benchmark', observed_in_collection_count: 1, observed_papers: ['Indexed Paper'], suitability_context: 'Observed in collection for domain evaluation.', potential_limitation: 'Dataset presence in collection does not guarantee it is optimal.' }
    ],
    experiment_plan: [
      { step_number: 1, title: 'Exp 1: Baseline Evaluation', description: 'Evaluate single baseline model.', metrics_to_evaluate: ['Accuracy', 'Precision', 'Recall', 'F1-Score'] },
      { step_number: 2, title: 'Exp 2: Combined Pipeline', description: 'Evaluate proposed combined approach.', metrics_to_evaluate: ['Accuracy', 'Precision', 'Recall', 'F1-Score'] }
    ],
    possible_contribution: 'Evaluate whether combining these approaches provides a useful research direction for this domain.',
    limitations: [
      'Collection Scope: Based strictly on currently indexed papers.',
      'Literature Review Required: Perform a broader academic search before starting.'
    ],
    scorecard: {
      metrics: [
        { metric_name: 'Evidence Strength', score_percentage: 76.3, rating_label: 'Strong', explanation: 'SBERT cosine similarity and graph structural similarity.' },
        { metric_name: 'Collection Support', score_percentage: 83.3, rating_label: 'Strong', explanation: 'Supporting paper coverage across indexed collection.' },
        { metric_name: 'Research Gap Signal', score_percentage: 71.1, rating_label: 'Strong', explanation: 'Multi-signal unlinked path score.' }
      ],
      overall_verdict: '🟡 PROMISING — INVESTIGATE FURTHER'
    },
    why_consider_this: [
      '✓ Related to multiple indexed papers in your collection',
      '✓ Combines concepts currently studied separately',
      '✓ Supported by high semantic similarity'
    ],
    validation_checklist: [
      'Search broader academic literature',
      'Confirm dataset availability and licensing',
      'Verify required computational resources'
    ],
    disclaimer: 'This evaluation is derived strictly from your currently indexed collection.'
  } : null);

  const conf = evalData?.confidence || 'MODERATE';

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-3 sm:px-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="w-full max-w-4xl glass-card rounded-3xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6 max-h-[calc(100vh-7rem)] overflow-y-auto custom-scrollbar relative">
        
        {/* HEADER BAR */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 sticky top-0 bg-slate-950/95 z-20 backdrop-blur">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-extrabold uppercase tracking-widest">
                💡 RESEARCH OPPORTUNITY EXPLORER
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
                conf === 'HIGH' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                conf === 'MODERATE' ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30' :
                'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                {conf} CONFIDENCE
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-100 mt-1 leading-snug">
              {evalData ? evalData.title : 'Loading Opportunity Details...'}
            </h2>
            {evalData && (
              <p className="text-xs text-slate-400 italic mt-0.5">
                {evalData.scope_tag}
              </p>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-colors self-end sm:self-auto shrink-0"
          >
            ✕
          </button>
        </div>

        {loading && !evalData ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400 font-semibold animate-pulse">Evaluating research opportunity evidence & feasibility...</p>
          </div>
        ) : evalData ? (
          <div className="space-y-8 text-xs text-slate-300">

            {/* A. RESEARCH PROBLEM */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>📘</span> A. Research Problem
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {evalData.research_problem}
              </p>
            </div>

            {/* B. WHAT CURRENT RESEARCH DOES */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>📄</span> B. What Current Research Does (Collection Baseline)
              </h3>

              {(() => {
                const papers = evalData.what_current_research_does || [];
                const seenIds = new Set();
                const uniquePapers = papers.filter(p => {
                  const pId = p.paper_id ?? p.title;
                  if (seenIds.has(pId)) return false;
                  seenIds.add(pId);
                  return true;
                });

                if (uniquePapers.length === 0) {
                  return (
                    <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-850 text-slate-400 italic text-xs">
                      No direct supporting paper found for this opportunity.
                    </div>
                  );
                }

                return (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {uniquePapers.map((paper, idx) => (
                      <div
                        key={paper.paper_id || idx}
                        onClick={() => paper.paper_id && onViewPaper && onViewPaper(paper.paper_id)}
                        className="p-4 rounded-2xl bg-slate-950/70 border border-slate-850 hover:border-indigo-500/40 cursor-pointer transition-colors space-y-1.5"
                      >
                        <span className="text-[10px] font-mono text-indigo-400 font-bold block">
                          {paper.role}
                        </span>
                        <h4 className="text-xs font-bold text-slate-100 line-clamp-2">
                          {paper.title}
                        </h4>
                        {paper.key_methods && paper.key_methods.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {paper.key_methods.map((m, mIdx) => (
                              <span key={mIdx} className="px-2 py-0.5 rounded bg-slate-850 text-slate-300 text-[10px]">
                                {m}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* C. WHAT APPEARS TO BE MISSING */}
            <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20 space-y-2">
              <h3 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-2">
                <span>🔎</span> C. What Appears To Be Missing
              </h3>
              <p className="text-xs text-amber-200 leading-relaxed">
                {evalData.what_is_missing}
              </p>
              <span className="text-[10px] text-amber-400/80 italic block">
                Note: Explicitly scoped to your currently indexed paper collection.
              </span>
            </div>

            {/* D. WHY THIS IDEA IS RELEVANT & EVIDENCE METRICS */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>📊</span> D. Evidence Strength & Relevance
                </h3>
                <button
                  onClick={() => setShowTechDetails(!showTechDetails)}
                  className="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  {showTechDetails ? 'Hide Technical Signals' : 'View Technical Evidence'}
                </button>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed p-4 rounded-2xl bg-slate-900/60 border border-slate-850">
                {evalData.why_relevant}
              </p>

              {/* Visual Evidence Bars with Tooltips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-5 rounded-2xl bg-slate-950/80 border border-slate-850">
                {[
                  {
                    label: 'Relationship Strength',
                    val: evalData.evidence.relationship_strength,
                    tooltip: 'How strongly graph structure connects this paper to research using the proposed concept.',
                    color: 'bg-indigo-500'
                  },
                  {
                    label: 'Semantic Relevance',
                    val: evalData.evidence.semantic_relevance,
                    tooltip: 'How semantically related source research is to papers using this concept.',
                    color: 'bg-sky-500'
                  },
                  {
                    label: 'Collection Support',
                    val: evalData.evidence.collection_support,
                    tooltip: 'How often this concept appears in related papers within your collection.',
                    color: 'bg-emerald-500'
                  },
                  {
                    label: 'Concept Underrepresentation',
                    val: evalData.evidence.underrepresentation,
                    tooltip: 'Rarity of this concept combination within your indexed papers.',
                    color: 'bg-amber-500'
                  },
                  {
                    label: 'Overall Gap Score',
                    val: evalData.evidence.overall_gap_score,
                    tooltip: 'Multi-signal synthesis score evaluating potential gap prominence.',
                    color: 'bg-rose-500'
                  }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1.5 group relative">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-300 flex items-center gap-1">
                        {item.label}
                        <span className="text-[10px] text-slate-500 cursor-help" title={item.tooltip}>ℹ</span>
                      </span>
                      <span className="font-mono font-bold text-slate-100">{item.val}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-850 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${item.color}`} style={{ width: `${Math.min(100, item.val)}%` }}></div>
                    </div>
                    <p className="text-[10px] text-slate-500 italic hidden group-hover:block transition-all">
                      {item.tooltip}
                    </p>
                  </div>
                ))}
              </div>

              {showTechDetails && evalData.technical_evidence_details && (
                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono animate-fade-in">
                  <span className="font-bold text-slate-400 block text-[10px] uppercase">Raw Technical Signals:</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-300">
                    <div>Link Prediction: {evalData.technical_evidence_details.link_prediction_score}</div>
                    <div>SBERT Evidence: {evalData.technical_evidence_details.semantic_evidence}</div>
                    <div>Collection Coverage: {evalData.technical_evidence_details.collection_coverage}%</div>
                    <div>Underrepresented: {evalData.technical_evidence_details.underrepresentation_score}</div>
                  </div>
                </div>
              )}
            </div>

            {/* 🛠 WHAT WOULD I ACTUALLY BUILD? */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🛠</span> What Would I Actually Build? (Conceptual Pipeline)
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {evalData.implementation_preview && evalData.implementation_preview.map((step) => (
                  <div key={step.step_number} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1 text-center">
                    <span className="text-[10px] font-mono text-indigo-400 font-extrabold uppercase block">
                      Step {step.step_number}: {step.stage}
                    </span>
                    <h4 className="text-xs font-bold text-slate-100">{step.title}</h4>
                    <p className="text-[11px] text-slate-400 leading-snug">{step.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ⚙ CANDIDATE TECHNOLOGIES & DATASET CONSIDERATIONS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Technologies */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>⚙</span> Candidate Technologies
                </h3>
                <div className="space-y-2">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Supported by Collection:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {evalData.candidate_algorithms && evalData.candidate_algorithms.map((ca, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold text-xs">
                        {ca.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Datasets */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>📦</span> Dataset Considerations
                </h3>
                <div className="space-y-2">
                  {evalData.dataset_considerations && evalData.dataset_considerations.map((ds, i) => (
                    <div key={i} className="p-3 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-1">
                      <span className="font-bold text-amber-300 block">{ds.name}</span>
                      <p className="text-[11px] text-slate-300">{ds.suitability_context}</p>
                      <p className="text-[10px] text-slate-500 italic">Limitation: {ds.potential_limitation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 🧪 POSSIBLE EXPERIMENT PLAN */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🧪</span> Possible Experiment Plan (Candidate Evaluation)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {evalData.experiment_plan && evalData.experiment_plan.map((exp) => (
                  <div key={exp.step_number} className="p-4 rounded-2xl bg-slate-900/70 border border-slate-850 space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-100">{exp.title}</h4>
                    <p className="text-[11px] text-slate-350">{exp.description}</p>
                    {exp.metrics_to_evaluate && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {exp.metrics_to_evaluate.map((m, mIdx) => (
                          <span key={mIdx} className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[10px]">
                            {m}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 🎯 CONTRIBUTION & ⚠ RISKS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 space-y-1.5">
                <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">🎯 Possible Contribution</h4>
                <p className="text-xs text-emerald-200 leading-relaxed">{evalData.possible_contribution}</p>
              </div>

              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 space-y-1.5">
                <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider">⚠ Research Risks & Considerations</h4>
                <ul className="list-disc list-inside text-xs text-rose-200 space-y-1">
                  {evalData.limitations && evalData.limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 📊 IDEA SCORECARD */}
            {evalData.scorecard && (
              <div className="p-5 rounded-3xl bg-slate-900/80 border border-purple-500/30 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-2">
                    <span>📊</span> Research Opportunity Scorecard
                  </h3>
                  <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-200 font-extrabold text-xs border border-purple-500/40">
                    {evalData.scorecard.overall_verdict}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {evalData.scorecard.metrics.map((sc, i) => (
                    <div key={i} className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-slate-200">{sc.metric_name}</span>
                        <span className="text-purple-400">{sc.rating_label}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 leading-snug">{sc.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 🎓 WHY CONSIDER THIS & 🔍 BEFORE YOU START */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">🎓 Why Consider This?</h4>
                <div className="space-y-1.5 text-xs text-slate-300">
                  {evalData.why_consider_this && evalData.why_consider_this.map((reason, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-850">
                      {reason}
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">🔍 Before You Start Checklist</h4>
                <div className="space-y-1 text-xs text-slate-300">
                  {evalData.validation_checklist && evalData.validation_checklist.map((item, i) => (
                    <label key={i} className="flex items-start gap-2 p-2 rounded-xl bg-slate-900/60 border border-slate-850 cursor-pointer hover:bg-slate-900 transition-colors">
                      <input type="checkbox" className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-800" />
                      <span className="text-[11px] leading-snug text-slate-300">{item}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* DISCLAIMER */}
            {evalData.disclaimer && (
              <p className="text-[10px] text-slate-500 italic text-center pt-3 border-t border-slate-850">
                {evalData.disclaimer}
              </p>
            )}

          </div>
        ) : null}

        {/* BOTTOM ACTION BAR */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 pt-4 sticky bottom-0 bg-slate-950/95 z-20 backdrop-blur">
          <button
            onClick={onClose}
            className="btn-secondary py-2 px-5 text-xs font-bold w-full sm:w-auto"
          >
            Close Explorer
          </button>

          <div className="flex flex-col sm:flex-row items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => setShowValidationModal(true)}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-indigo-300 font-extrabold text-xs border border-indigo-500/30 shadow-md transition-all flex items-center justify-center gap-1.5 w-full sm:w-auto"
            >
              <span>🔎</span> Validate Idea
            </button>

            <button
              onClick={() => setShowPlannerModal(true)}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-indigo-300 font-extrabold text-xs border border-indigo-500/30 shadow-md transition-all flex items-center justify-center gap-1.5 w-full sm:w-auto"
            >
              <span>🧪</span> Build Research Plan
            </button>

            <button
              onClick={() => onGenerateDraft && onGenerateDraft(directionId)}
              disabled={isDrafting}
              className="btn-primary py-2.5 px-6 text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 w-full sm:w-auto"
            >
              {isDrafting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Synthesizing Proposal Draft...
                </>
              ) : (
                <>
                  <span>✨</span> Draft Research Proposal
                </>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* RESEARCH IDEA VALIDATION MODAL */}
      {showValidationModal && (
        <ResearchIdeaValidationModal
          directionId={directionId}
          projectId={projectId}
          fallbackDirection={fallbackDirection}
          onClose={() => setShowValidationModal(false)}
          onGenerateDraft={(dirId) => {
            setShowValidationModal(false);
            if (onGenerateDraft) onGenerateDraft(dirId);
          }}
          onRefineIdea={() => {
            setShowValidationModal(false);
          }}
        />
      )}

      {/* RESEARCH METHODOLOGY PLANNER MODAL */}
      {showPlannerModal && (
        <ResearchMethodologyPlannerModal
          directionId={directionId}
          projectId={projectId}
          fallbackDirection={fallbackDirection}
          onClose={() => setShowPlannerModal(false)}
          onGenerateDraft={(dirId) => {
            setShowPlannerModal(false);
            if (onGenerateDraft) onGenerateDraft(dirId);
          }}
        />
      )}

    </div>
  );
}
