import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../services/api';

// Helper functions for paper view modal role grouping and provenance rendering
function getEntitiesByRole(paper, category, targetRoles) {
  if (!paper) return [];
  const detailKey = `${category}_details`;
  const legacyKey = category === 'keyword' ? 'keywords' : (category === 'domain' ? 'application_domains' : `${category}s`);

  if (paper[detailKey] && Array.isArray(paper[detailKey]) && paper[detailKey].length > 0) {
    return paper[detailKey].filter(item => {
      const r = (item.role || '').toLowerCase();
      return targetRoles.some(tr => r === tr.toLowerCase());
    });
  }

  // Fallback to legacy string arrays
  if (targetRoles.includes("primary") || targetRoles.includes("experimental")) {
    const legacyList = paper[legacyKey] || [];
    return legacyList.map(name => ({
      name,
      category,
      role: targetRoles[0],
      confidence: 0.90,
      evidence_section: "Abstract",
      source: "abstract",
      evidence_text: `${name} extracted from paper text.`
    }));
  }
  return [];
}

function hasAnyEntities(paper, category) {
  if (!paper) return false;
  const detailKey = `${category}_details`;
  const legacyKey = category === 'keyword' ? 'keywords' : (category === 'domain' ? 'application_domains' : `${category}s`);
  return (paper[detailKey] && paper[detailKey].length > 0) || (paper[legacyKey] && paper[legacyKey].length > 0);
}

function renderEntityPillGroup(groupLabel, items, colorTheme, badgeLabel, selectedEvidence, setSelectedEvidence) {
  if (!items || items.length === 0) return null;

  const themeStyles = {
    emerald: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20",
    amber: "bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20",
    indigo: "bg-indigo-500/10 border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20",
    rose: "bg-rose-500/10 border-rose-500/30 text-rose-300 hover:bg-rose-500/20",
    slate: "bg-slate-800/40 border-slate-700/40 text-slate-300 hover:bg-slate-800/60"
  };

  const badgeStyles = {
    emerald: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    amber: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    indigo: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
    rose: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    slate: "bg-slate-700/40 text-slate-400 border-slate-600/40"
  };

  return (
    <div className="space-y-1 pt-1">
      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
        {groupLabel} ({items.length})
      </span>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, idx) => {
          const isSelected = selectedEvidence && selectedEvidence.name === item.name;
          return (
            <button
              key={idx}
              onClick={() => setSelectedEvidence(isSelected ? null : item)}
              className={`px-2.5 py-1 rounded-lg border text-xs font-medium transition-all duration-200 flex items-center gap-1.5 cursor-pointer text-left ${
                themeStyles[colorTheme] || themeStyles.slate
              } ${isSelected ? 'ring-2 ring-indigo-400 scale-[1.02]' : ''}`}
              title="Click to view evidence text and provenance"
            >
              <span>{item.name}</span>
              <span className={`px-1.5 py-px rounded text-[9px] font-bold border uppercase tracking-tight ${badgeStyles[colorTheme] || badgeStyles.slate}`}>
                {badgeLabel}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function PaperViewModal({ paperId, onClose }) {
  const [currentPaperId, setCurrentPaperId] = useState(paperId);
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');
  const [matchCount, setMatchCount] = useState(0);

  // Active evidence item for provenance inspector
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Related Papers state
  const [relatedPapers, setRelatedPapers] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [relatedError, setRelatedError] = useState('');

  // Sync internal currentPaperId if prop changes
  useEffect(() => {
    if (paperId) {
      setCurrentPaperId(paperId);
    }
  }, [paperId]);

  // Lock body scroll when modal is active
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  // Fetch paper details and related papers on currentPaperId change
  useEffect(() => {
    if (!currentPaperId) return;

    const fetchPaperDetailAndRelated = async () => {
      setLoading(true);
      setError('');
      setRelatedLoading(true);
      setRelatedError('');
      setSearchText('');

      try {
        // 1. Fetch paper details
        const response = await apiService.getPaper(currentPaperId);
        setPaper(response.data);
      } catch (err) {
        console.error(err);
        setError('Failed to load paper details. The file or metadata may have been removed.');
        setPaper(null);
      } finally {
        setLoading(false);
      }

      try {
        // 2. Fetch related papers
        const relatedResp = await apiService.getRelatedPapers(currentPaperId, 5);
        setRelatedPapers(relatedResp.data.related_papers || []);
      } catch (err) {
        console.error(err);
        setRelatedError('Related papers could not be loaded.');
        setRelatedPapers([]);
      } finally {
        setRelatedLoading(false);
      }
    };

    fetchPaperDetailAndRelated();
  }, [currentPaperId]);

  // Update match count when search text or paper changes
  useEffect(() => {
    if (!paper || !searchText.trim()) {
      setMatchCount(0);
      return;
    }
    try {
      const escapedSearch = searchText.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
      const regex = new RegExp(escapedSearch, 'gi');
      const matches = paper.full_text.match(regex);
      setMatchCount(matches ? matches.length : 0);
    } catch (e) {
      setMatchCount(0);
    }
  }, [searchText, paper]);

  // Escape HTML and wrap matches in <mark> tags
  const getHighlightedText = (text, search) => {
    if (!text) return '';
    if (!search.trim()) return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    const escapedText = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    try {
      const escapedSearch = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
      const regex = new RegExp(`(${escapedSearch})`, 'gi');
      return escapedText.replace(regex, '<mark class="bg-indigo-500/50 text-indigo-100 rounded px-0.5 py-px border border-indigo-400/30">$1</mark>');
    } catch (e) {
      return escapedText;
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] overflow-y-auto">
      {/* Backdrop overlay */}
      <div 
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in"
        onClick={onClose} 
      />

      {/* Positioning wrapper: clear sticky navbar with breathing room */}
      <div className="relative flex min-h-screen items-start justify-center pt-20 sm:pt-24 pb-6 px-4 sm:px-6 pointer-events-none">
        {/* Outer Modal Frame */}
        <div className="relative flex h-[calc(100vh-7rem)] max-h-[calc(100vh-7rem)] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-slate-800 glass-card shadow-2xl pointer-events-auto z-10">
          
          {/* 1. FIXED HEADER (Never scrolls, never squishes, wraps title naturally) */}
          <header className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-800/80 bg-slate-900/95 backdrop-blur-md px-6 py-4 relative z-10">
            <div className="min-w-0 flex-1 pr-2">
              {loading ? (
                <div className="space-y-2">
                  <div className="h-6 w-3/4 bg-slate-800 rounded animate-pulse"></div>
                  <div className="h-4 w-1/2 bg-slate-850 rounded animate-pulse"></div>
                </div>
              ) : paper ? (
                <>
                  <h3 
                    className="m-0 block w-full text-[20px] font-bold leading-[1.35] text-slate-100 whitespace-normal break-words [overflow-wrap:anywhere]"
                    style={{ wordBreak: 'break-word' }}
                    title={paper.title}
                  >
                    {paper.title}
                  </h3>
                  <p className="mt-1 text-xs text-slate-400 truncate">
                    Filename: <span className="font-mono text-indigo-400">{paper.filename}</span>
                  </p>
                </>
              ) : (
                <h3 className="text-[20px] font-bold text-slate-100">Error Loading Details</h3>
              )}
            </div>
            
            {/* Close button (Fixed top-right, never squishes or overlaps title) */}
            <button
              onClick={onClose}
              className="shrink-0 p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors focus:outline-none"
              title="Close Viewer"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </header>

          {/* 2. SCROLLABLE CONTENT AREA (Only this area scrolls) */}
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar p-6 space-y-6">
          {loading ? (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="h-4 w-24 bg-slate-800 rounded animate-pulse"></div>
                <div className="h-24 bg-slate-800 rounded-2xl animate-pulse"></div>
              </div>
              <div className="space-y-3">
                <div className="h-4 w-32 bg-slate-800 rounded animate-pulse"></div>
                <div className="h-10 bg-slate-850 rounded-2xl animate-pulse"></div>
                <div className="h-40 bg-slate-850 rounded-2xl animate-pulse"></div>
              </div>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-rose-450 space-y-3">
              <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="font-medium">{error}</p>
              <button onClick={onClose} className="btn-secondary py-2 text-xs">Close Modal</button>
            </div>
          ) : paper ? (
            <>
              {/* Abstract Section */}
              {paper.abstract && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" />
                    </svg>
                    Abstract
                  </h4>
                  <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 text-slate-300 text-sm leading-relaxed select-text italic">
                    {paper.abstract}
                  </div>
                </div>
              )}

              {/* Extracted Metadata Grid with Role Classification & Provenance */}
              <div className="space-y-4 bg-slate-900/50 p-5 rounded-3xl border border-slate-800/80">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    Role-Aware Paper Metadata & Scientific Evidence
                  </h4>
                  <span className="text-[11px] text-slate-400 italic">Click entity to inspect provenance & evidence</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* ALGORITHMS */}
                  <div className="space-y-3 bg-slate-950/40 p-4 rounded-2xl border border-slate-850/60">
                    <h5 className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center justify-between">
                      <span>Algorithms</span>
                      <span className="text-[10px] text-slate-500 font-normal">Primary / Comparison / Mentioned</span>
                    </h5>

                    {renderEntityPillGroup(
                      "Primary / Proposed",
                      getEntitiesByRole(paper, "algorithm", ["primary", "proposed_model"]),
                      "emerald",
                      "PRIMARY",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {renderEntityPillGroup(
                      "Comparison / Baselines",
                      getEntitiesByRole(paper, "algorithm", ["comparison", "comparison_model", "baseline_model"]),
                      "amber",
                      "COMPARISON",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {renderEntityPillGroup(
                      "Mentioned / Reference",
                      getEntitiesByRole(paper, "algorithm", ["mentioned", "used_model", "mentioned_model"]),
                      "slate",
                      "MENTIONED",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {!hasAnyEntities(paper, "algorithm") && (
                      <span className="text-xs text-slate-500 italic block">None extracted</span>
                    )}
                  </div>

                  {/* DATASETS */}
                  <div className="space-y-3 bg-slate-950/40 p-4 rounded-2xl border border-slate-850/60">
                    <h5 className="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center justify-between">
                      <span>Datasets</span>
                      <span className="text-[10px] text-slate-500 font-normal">Experimental / Benchmark / Mentioned</span>
                    </h5>

                    {renderEntityPillGroup(
                      "Experimental Datasets",
                      getEntitiesByRole(paper, "dataset", ["experimental", "experimental_dataset", "training_dataset", "test_dataset"]),
                      "amber",
                      "EXPERIMENTAL",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {renderEntityPillGroup(
                      "Benchmark Datasets",
                      getEntitiesByRole(paper, "dataset", ["benchmark", "benchmark_dataset"]),
                      "indigo",
                      "BENCHMARK",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {renderEntityPillGroup(
                      "Mentioned Datasets",
                      getEntitiesByRole(paper, "dataset", ["mentioned", "background_dataset"]),
                      "slate",
                      "MENTIONED",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {!hasAnyEntities(paper, "dataset") && (
                      <span className="text-xs text-slate-500 italic block">None extracted</span>
                    )}
                  </div>

                  {/* METHODOLOGIES */}
                  <div className="space-y-3 bg-slate-950/40 p-4 rounded-2xl border border-slate-850/60">
                    <h5 className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
                      Methodologies
                    </h5>

                    {renderEntityPillGroup(
                      "Primary Methodologies",
                      getEntitiesByRole(paper, "methodology", ["primary", "primary_methodology"]),
                      "rose",
                      "PRIMARY",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {renderEntityPillGroup(
                      "Mentioned Methodologies",
                      getEntitiesByRole(paper, "methodology", ["mentioned", "used_methodology"]),
                      "slate",
                      "MENTIONED",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {!hasAnyEntities(paper, "methodology") && (
                      <span className="text-xs text-slate-500 italic block">None extracted</span>
                    )}
                  </div>

                  {/* KEYWORDS / RESEARCH CONCEPTS */}
                  <div className="space-y-3 bg-slate-950/40 p-4 rounded-2xl border border-slate-850/60">
                    <h5 className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                      Keywords & Research Concepts
                    </h5>

                    {renderEntityPillGroup(
                      "Research Concepts",
                      getEntitiesByRole(paper, "keyword", ["primary", "mentioned"]),
                      "indigo",
                      "CONCEPT",
                      selectedEvidence,
                      setSelectedEvidence
                    )}

                    {!hasAnyEntities(paper, "keyword") && (
                      <span className="text-xs text-slate-500 italic block">None extracted</span>
                    )}
                  </div>
                </div>

                {/* PROVENANCE EVIDENCE INSPECTOR CARD */}
                {selectedEvidence && (
                  <div className="mt-3 p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/40 text-xs space-y-2 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-indigo-200 text-sm">{selectedEvidence.name}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
                          {selectedEvidence.role ? selectedEvidence.role.toUpperCase() : 'EXTRACTED'}
                        </span>
                        <span className="text-slate-400 text-[11px]">
                          Category: <strong className="text-slate-200 capitalize">{selectedEvidence.category || 'Metadata'}</strong>
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedEvidence(null)}
                        className="text-slate-400 hover:text-slate-200 text-xs px-2 py-0.5 rounded bg-slate-800/60"
                      >
                        Close
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 border-t border-indigo-900/40 text-slate-300">
                      <div>
                        <span className="text-slate-500">Section:</span>{' '}
                        <strong className="text-indigo-300">{selectedEvidence.evidence_section || selectedEvidence.source || 'Abstract'}</strong>
                      </div>
                      <div>
                        <span className="text-slate-500">Confidence:</span>{' '}
                        <strong className="text-emerald-400">
                          {selectedEvidence.confidence ? `${(selectedEvidence.confidence * 100).toFixed(0)}%` : 'High'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-slate-500">Source:</span>{' '}
                        <strong className="text-slate-300 capitalize">{selectedEvidence.source || 'Text context'}</strong>
                      </div>
                    </div>

                    {selectedEvidence.evidence_text && (
                      <div className="mt-2 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 italic leading-relaxed">
                        "{selectedEvidence.evidence_text}"
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* --- RELATED RESEARCH PAPERS SECTION --- */}
              <div className="space-y-3 pt-2">
                <h4 className="text-sm font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Related Research Papers
                </h4>

                {relatedLoading ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[1, 2].map((idx) => (
                      <div key={idx} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-850 animate-pulse space-y-2">
                        <div className="h-4 bg-slate-800 rounded w-3/4"></div>
                        <div className="h-8 bg-slate-850 rounded"></div>
                      </div>
                    ))}
                  </div>
                ) : relatedError ? (
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-850 text-xs text-slate-400 italic">
                    {relatedError}
                  </div>
                ) : relatedPapers.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {relatedPapers.map((relItem) => (
                      <div
                        key={relItem.paper_id}
                        onClick={() => setCurrentPaperId(relItem.paper_id)}
                        className="p-4 rounded-2xl bg-slate-900/70 hover:bg-slate-850 border border-indigo-900/30 hover:border-indigo-500/50 cursor-pointer transition-all duration-300 space-y-2 group shadow-md"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h5 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 line-clamp-1 leading-snug">
                            {relItem.title}
                          </h5>
                          <span className="px-2 py-0.5 rounded-md bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-[10px] font-bold flex-shrink-0">
                            Semantic Similarity: {(relItem.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>

                        {relItem.abstract && (
                          <p className="text-[11px] text-slate-400 line-clamp-2 italic leading-tight">
                            "{relItem.abstract}"
                          </p>
                        )}

                        <div className="flex flex-wrap gap-1 pt-1">
                          {relItem.algorithms && relItem.algorithms.slice(0, 2).map((algo, i) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[9px]">
                              {algo}
                            </span>
                          ))}
                          {relItem.keywords && relItem.keywords.slice(0, 2).map((kw, i) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 text-[9px]">
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-850 text-xs text-slate-450 italic">
                    No related research papers found in vector index.
                  </div>
                )}
              </div>

              {/* Full Text Section */}
              <div className="space-y-3 flex flex-col h-full pt-2">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-850 pb-3">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    Extracted Text Content
                  </h4>

                  {/* Text search input inside Modal */}
                  <div className="relative flex items-center">
                    <input
                      type="text"
                      placeholder="Find in text..."
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      className="pl-8 pr-16 py-1.5 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500 w-full sm:w-56 transition-all"
                    />
                    <svg className="w-3.5 h-3.5 text-slate-500 absolute left-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    {searchText && (
                      <span className="absolute right-2 px-1.5 py-0.5 bg-slate-800 border border-slate-700 text-[10px] rounded text-slate-400 font-mono">
                        {matchCount} matches
                      </span>
                    )}
                  </div>
                </div>

                {/* Preformatted text display box */}
                <div 
                  className="p-5 rounded-2xl bg-slate-950/60 border border-slate-850/80 text-slate-300 text-sm font-sans leading-relaxed select-text overflow-y-auto h-[35vh] custom-scrollbar whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ 
                    __html: getHighlightedText(paper.full_text, searchText) 
                  }}
                ></div>
              </div>
            </>
          ) : null}
        </div>

        {/* 3. FIXED FOOTER (Stationary bottom) */}
        <footer className="shrink-0 px-6 py-4 bg-slate-900/60 border-t border-slate-800/80 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="btn-secondary py-1.5 text-xs px-5"
          >
            Close Viewer
          </button>
        </footer>

      </div>
    </div>
  </div>,
  document.body
);
}
