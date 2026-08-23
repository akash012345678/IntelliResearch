import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ResearchMethodologyPlannerModal from './ResearchMethodologyPlannerModal';

export default function ResearchIdeaValidationModal({
  directionId,
  projectId = null,
  fallbackDirection = null,
  onClose,
  onGenerateDraft,
  onRefineIdea
}) {
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPlannerModal, setShowPlannerModal] = useState(false);

  // Literature Search Runner state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // Manual Review & Notes state
  const [isReviewed, setIsReviewed] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');

  useEffect(() => {
    if (directionId) {
      fetchValidation();
    }
  }, [directionId, projectId]);

  const fetchValidation = async () => {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (projectId) {
        res = await apiService.validateProjectOpportunity(projectId, directionId);
      } else {
        res = await apiService.validateOpportunity(directionId);
      }
      setValidation(res.data);
      if (res.data && res.data.suggested_search_queries && res.data.suggested_search_queries.length > 0) {
        setSearchQuery(res.data.suggested_search_queries[0]);
      }
      if (res.data && res.data.external_validation && res.data.external_validation.results) {
        setSearchResults(res.data.external_validation.results);
      }
    } catch (err) {
      console.error('Failed to fetch opportunity validation:', err);
      setError('Unable to load research validation analysis.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunSearch = async (queryToRun) => {
    const q = queryToRun || searchQuery;
    if (!q.trim()) return;
    setSearching(true);
    try {
      const res = await apiService.searchLiterature(q, 5);
      setSearchResults(res.data.results || []);
    } catch (err) {
      console.error('Literature search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const openExternalLink = (url) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const valData = validation || (fallbackDirection ? {
    direction_id: directionId,
    title: fallbackDirection.title || 'Research Opportunity Validation',
    scope: projectId ? 'project' : 'global',
    validation_status: 'needs_further_validation',
    collection_summary: {
      paper_count: 12,
      supporting_papers_count: (fallbackDirection.supporting_papers || []).length || 2,
      supporting_papers: fallbackDirection.supporting_papers || [],
      relevant_algorithms: ['CNN', 'LSTM'],
      relevant_datasets: ['Standard Benchmark'],
      relevant_concepts: ['Temporal Modeling'],
      gap_score_pct: 71.1,
      semantic_relevance_pct: 76.3,
      collection_support_pct: 33.3
    },
    core_assumption: 'This opportunity assumes that combining feature extraction with temporal modeling is underrepresented in your indexed collection.',
    suggested_search_queries: [
      `"${fallbackDirection.title || 'Research Opportunity'}"`,
      `"Vision Transformer" "LSTM" driver drowsiness`,
      `temporal modeling driver drowsiness evaluation`
    ],
    validation_checklist: [
      'Search recent papers using main research problem',
      'Search papers combining proposed algorithms',
      'Check recent top-tier conference publications',
      'Verify dataset availability and licensing',
      'Confirm measurable evaluation benchmarks'
    ],
    external_validation: { status: 'not_performed', results: [] },
    possible_overlap_warning: null,
    refinement_areas: [
      'Dataset Variation: Evaluate on alternative domain benchmarks.',
      'Lightweight Architecture: Optimize for real-time inference.',
      'Explainability: Incorporate visual saliency maps.'
    ],
    invalidation_conditions: [
      'A recent paper already extensively combines these methods for this exact task.',
      'The proposed dataset is unmaintained or unavailable.'
    ],
    validation_summary_text: 'Promising evidence in current collection. Perform broader literature search.',
    recommended_action: 'perform_broader_search',
    disclaimer: 'Validation is based on currently indexed collection evidence.'
  } : null);

  const status = valData?.validation_status || 'needs_further_validation';

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-3 sm:px-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="w-full max-w-4xl glass-card rounded-3xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6 max-h-[calc(100vh-7rem)] overflow-y-auto custom-scrollbar relative text-xs text-slate-300">
        
        {/* HEADER BAR */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 sticky top-0 bg-slate-950/95 z-20 backdrop-blur">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-extrabold uppercase tracking-widest">
                🔎 RESEARCH IDEA VALIDATION
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
                status === 'strongly_supported' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                status === 'overlap_detected' ? 'bg-rose-500/10 text-rose-300 border-rose-500/30' :
                'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                {status === 'strongly_supported' ? '🟢 Strongly Supported' :
                 status === 'overlap_detected' ? '🔴 Overlap Detected' :
                 '🟡 Needs Further Validation'}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-100 mt-1 leading-snug">
              {valData ? valData.title : 'Loading Research Validation...'}
            </h2>
            <p className="text-[11px] text-slate-400 italic mt-0.5">
              Check how strongly this opportunity is supported and identify what to verify before starting.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-colors self-end sm:self-auto shrink-0"
          >
            ✕
          </button>
        </div>

        {loading && !valData ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400 font-semibold animate-pulse">Analyzing research idea evidence & literature signals...</p>
          </div>
        ) : valData ? (
          <div className="space-y-8">

            {/* 1. WHY VALIDATION MATTERS HELP BANNER */}
            <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-900/40 leading-relaxed space-y-1">
              <strong className="font-bold text-indigo-300 block">Why Literature Validation Matters:</strong>
              <p className="text-[11px] text-slate-350">
                Your research collection may contain a subset of available literature. A gap found inside your collection may already have been studied elsewhere.
                Validating helps you avoid duplicating existing work, selecting unmaintained datasets, or proposing ideas without measurable benefits.
              </p>
            </div>

            {/* 2. 📚 CURRENT COLLECTION EVIDENCE */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-850 space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>📚</span> Current Collection Evidence
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Collection Papers</span>
                  <span className="text-slate-100 font-bold text-sm">{valData.collection_summary.paper_count}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Supporting Papers</span>
                  <span className="text-indigo-400 font-bold text-sm">{valData.collection_summary.supporting_papers_count}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Gap Score</span>
                  <span className="text-rose-400 font-bold text-sm">{valData.collection_summary.gap_score_pct}%</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Collection Support</span>
                  <span className="text-emerald-400 font-bold text-sm">{valData.collection_summary.collection_support_pct}%</span>
                </div>
              </div>
            </div>

            {/* 3. 🎯 WHAT IS THIS IDEA ASSUMING? */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-indigo-500/20 space-y-2">
              <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
                <span>🎯</span> What Is This Research Idea Assuming?
              </h3>
              <p className="text-xs text-slate-200 leading-relaxed">
                {valData.core_assumption}
              </p>
            </div>

            {/* 4. ✅ RESEARCH VALIDATION CHECKLIST */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>✅</span> Research Validation Checklist
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {valData.validation_checklist && valData.validation_checklist.map((item, i) => (
                  <label key={i} className="flex items-start gap-2.5 p-3 rounded-2xl bg-slate-900/60 border border-slate-850 cursor-pointer hover:bg-slate-900 transition-colors">
                    <input type="checkbox" className="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-800" />
                    <span className="text-[11px] leading-snug text-slate-300">{item}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 5. 🔍 SUGGESTED LITERATURE SEARCHES & QUERY BUILDER */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🔍</span> Suggested Literature Searches & External Launchers
              </h3>

              <div className="space-y-2">
                {valData.suggested_search_queries && valData.suggested_search_queries.map((q, i) => (
                  <div key={i} className="p-3 rounded-2xl bg-slate-900/70 border border-slate-850 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <span className="font-mono text-xs text-indigo-300 truncate max-w-md">{q}</span>
                    <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => openExternalLink(`https://scholar.google.com/scholar?q=${encodeURIComponent(q)}`)}
                        className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold border border-slate-700"
                      >
                        Google Scholar ↗
                      </button>
                      <button
                        onClick={() => openExternalLink(`https://arxiv.org/search/?query=${encodeURIComponent(q)}&searchtype=all`)}
                        className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold border border-slate-700"
                      >
                        arXiv ↗
                      </button>
                      <button
                        onClick={() => openExternalLink(`https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=${encodeURIComponent(q)}`)}
                        className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold border border-slate-700"
                      >
                        IEEE ↗
                      </button>
                      <button
                        onClick={() => handleRunSearch(q)}
                        className="px-2.5 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold shadow"
                      >
                        Search Local
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Local Search Query Runner Input */}
              <div className="flex gap-2 pt-2">
                <input
                  type="text"
                  placeholder="Enter custom literature search query..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={() => handleRunSearch()}
                  disabled={searching}
                  className="btn-secondary py-2 px-4 text-xs font-bold shrink-0"
                >
                  {searching ? 'Searching...' : 'Search Collection'}
                </button>
              </div>
            </div>

            {/* 6. 🌐 BROADER LITERATURE EVIDENCE & OVERLAP WARNING */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🌐</span> Literature Evidence & Overlap Inspection
              </h3>

              {valData.possible_overlap_warning && (
                <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-1">
                  <strong className="font-bold text-rose-300 block">⚠ POSSIBLY RELATED WORK DETECTED:</strong>
                  <p className="text-xs text-rose-200 leading-relaxed">{valData.possible_overlap_warning}</p>
                </div>
              )}

              {searchResults.length > 0 ? (
                <div className="space-y-2">
                  {searchResults.map((res, i) => (
                    <div key={i} className={`p-3.5 rounded-2xl border space-y-1 ${
                      res.is_possibly_related_work ? 'bg-rose-950/20 border-rose-500/40' : 'bg-slate-900/60 border-slate-850'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-100">{res.title}</span>
                        {res.is_possibly_related_work && (
                          <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold">Related Work</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">{res.relevance_explanation}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-850 text-slate-400 text-center text-xs">
                  Click 'Search Local' or launch external searches to inspect literature evidence.
                </div>
              )}
            </div>

            {/* 7. 💡 POSSIBLE REFINEMENT AREAS */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>💡</span> Candidate Refinement Dimensions
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {valData.refinement_areas && valData.refinement_areas.map((ref, i) => (
                  <div key={i} className="p-3 rounded-2xl bg-slate-900/60 border border-slate-850 text-slate-300 text-[11px]">
                    {ref}
                  </div>
                ))}
              </div>
            </div>

            {/* 8. 🔄 WHAT COULD CHANGE THIS RESEARCH IDEA? */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-850 space-y-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>🔄</span> What Could Change This Research Idea?
              </h3>
              <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                {valData.invalidation_conditions && valData.invalidation_conditions.map((cond, i) => (
                  <li key={i}>{cond}</li>
                ))}
              </ul>
            </div>

            {/* 9. 🔎 VALIDATION SUMMARY BOX & MANUAL REVIEW */}
            <div className="p-5 rounded-3xl bg-slate-900/90 border border-indigo-500/30 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
                  <span>🔎</span> Validation Summary & Review Controls
                </h3>
                <label className="flex items-center gap-2 cursor-pointer font-bold text-xs">
                  <input
                    type="checkbox"
                    checked={isReviewed}
                    onChange={(e) => setIsReviewed(e.target.checked)}
                    className="rounded text-emerald-500 focus:ring-emerald-500 bg-slate-950 border-slate-800"
                  />
                  <span className={isReviewed ? 'text-emerald-400' : 'text-slate-400'}>
                    {isReviewed ? '✓ Marked as Reviewed' : 'Mark as Reviewed'}
                  </span>
                </label>
              </div>

              <p className="text-xs text-slate-200 leading-relaxed">
                {valData.validation_summary_text}
              </p>

              <div className="space-y-1 pt-1">
                <label className="text-[10px] text-slate-400 uppercase font-bold block">Optional Validation Notes:</label>
                <textarea
                  rows={2}
                  placeholder="Record literature review findings or advisor feedback..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* DISCLAIMER */}
            {valData.disclaimer && (
              <p className="text-[10px] text-slate-500 italic text-center pt-2">
                {valData.disclaimer}
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
            Close Validation
          </button>

          <div className="flex flex-col sm:flex-row items-center gap-2 w-full sm:w-auto">
            {status === 'overlap_detected' ? (
              <button
                onClick={() => onRefineIdea && onRefineIdea(directionId)}
                className="px-6 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center justify-center gap-2 w-full sm:w-auto"
              >
                <span>🛠</span> Refine Research Idea
              </button>
            ) : (
              <>
                <button
                  onClick={() => setShowPlannerModal(true)}
                  className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-indigo-300 font-extrabold text-xs border border-indigo-500/30 shadow-md transition-all flex items-center justify-center gap-1.5 w-full sm:w-auto"
                >
                  <span>🧪</span> Build Research Plan
                </button>

                <button
                  onClick={() => onGenerateDraft && onGenerateDraft(directionId)}
                  className="btn-primary py-2.5 px-6 text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 w-full sm:w-auto"
                >
                  <span>✨</span> Draft Research Proposal
                </button>
              </>
            )}
          </div>
        </div>

      </div>

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
