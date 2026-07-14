import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function PaperViewModal({ paperId, onClose }) {
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');
  const [matchCount, setMatchCount] = useState(0);

  // Fetch paper details on mount or ID change
  useEffect(() => {
    if (!paperId) return;
    
    const fetchPaperDetail = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await apiService.getPaper(paperId);
        setPaper(response.data);
      } catch (err) {
        console.error(err);
        setError('Failed to load paper details. The file or metadata may have been removed.');
      } finally {
        setLoading(false);
      }
    };

    fetchPaperDetail();
  }, [paperId]);

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-5xl h-[85vh] flex flex-col glass-card rounded-3xl overflow-hidden border border-slate-800 shadow-2xl">
        
        {/* Modal Header */}
        <div className="px-6 py-5 bg-slate-900/80 border-b border-slate-800 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {loading ? (
              <div className="h-6 w-48 bg-slate-800 rounded animate-pulse"></div>
            ) : paper ? (
              <>
                <h3 className="text-lg font-bold text-slate-100 leading-snug line-clamp-1 pr-6" title={paper.title}>
                  {paper.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1 truncate">
                  Filename: <span className="font-mono text-indigo-400">{paper.filename}</span>
                </p>
              </>
            ) : (
              <h3 className="text-lg font-bold text-slate-100">Error Loading Details</h3>
            )}
          </div>
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-450 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
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
                  <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 text-slate-300 text-sm leading-relaxed select-text italic">
                    {paper.abstract}
                  </div>
                </div>
              )}

              {/* Extracted Metadata Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900/40 p-5 rounded-3xl border border-slate-850/80">
                {/* Keywords */}
                <div className="space-y-2.5">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                    Keywords
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {paper.keywords && paper.keywords.length > 0 ? (
                      paper.keywords.map((kw, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold tracking-wide">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Algorithms */}
                <div className="space-y-2.5">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                    Algorithms
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {paper.algorithms && paper.algorithms.length > 0 ? (
                      paper.algorithms.map((algo, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold tracking-wide">
                          {algo}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Datasets */}
                <div className="space-y-2.5">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                    Datasets
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {paper.datasets && paper.datasets.length > 0 ? (
                      paper.datasets.map((ds, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold tracking-wide">
                          {ds}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Methodologies */}
                <div className="space-y-2.5">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
                    Methodologies
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {paper.methodologies && paper.methodologies.length > 0 ? (
                      paper.methodologies.map((method, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-semibold tracking-wide">
                          {method}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>

                {/* Application Domains */}
                <div className="space-y-2.5 md:col-span-2">
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-sky-400">
                    Application Domains
                  </h5>
                  <div className="flex flex-wrap gap-2">
                    {paper.application_domains && paper.application_domains.length > 0 ? (
                      paper.application_domains.map((domain, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs font-semibold tracking-wide">
                          {domain}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">None extracted</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Full Text Section */}
              <div className="space-y-3 flex flex-col h-full">
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
                  className="p-5 rounded-2xl bg-slate-950/60 border border-slate-850/80 text-slate-300 text-sm font-sans leading-relaxed select-text overflow-y-auto h-[40vh] custom-scrollbar whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ 
                    __html: getHighlightedText(paper.full_text, searchText) 
                  }}
                ></div>
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-900/50 border-t border-slate-800/80 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="btn-secondary py-2 text-sm px-6"
          >
            Close Viewer
          </button>
        </div>

      </div>
    </div>
  );
}
