import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../services/api';

export default function PaperViewModal({ paperId, onClose }) {
  const [currentPaperId, setCurrentPaperId] = useState(paperId);
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');
  const [matchCount, setMatchCount] = useState(0);

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

              {/* Extracted Metadata Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/40 p-4 rounded-3xl border border-slate-850/80">
                {/* Keywords */}
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                    Keywords
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {paper.keywords && paper.keywords.length > 0 ? (
                      paper.keywords.map((kw, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Algorithms */}
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                    Algorithms
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {paper.algorithms && paper.algorithms.length > 0 ? (
                      paper.algorithms.map((algo, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium">
                          {algo}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Datasets */}
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                    Datasets
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {paper.datasets && paper.datasets.length > 0 ? (
                      paper.datasets.map((ds, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium">
                          {ds}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Methodologies */}
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
                    Methodologies
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {paper.methodologies && paper.methodologies.length > 0 ? (
                      paper.methodologies.map((method, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
                          {method}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>
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
