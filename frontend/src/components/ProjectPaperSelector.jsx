import React, { useState, useEffect, useMemo } from 'react';
import { apiService } from '../services/api';

export default function ProjectPaperSelector({ projectId, onClose, onPapersAdded }) {
  const [availablePapers, setAvailablePapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('');
  const [selectedDataset, setSelectedDataset] = useState('');
  const [selectedMethodology, setSelectedMethodology] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [selectedKeyword, setSelectedKeyword] = useState('');

  // Selected Paper IDs state
  const [selectedPaperIds, setSelectedPaperIds] = useState(new Set());

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch available papers whenever filters change
  useEffect(() => {
    fetchAvailablePapers();
  }, [projectId, debouncedSearch, selectedAlgorithm, selectedDataset, selectedMethodology, selectedDomain, selectedKeyword]);

  const fetchAvailablePapers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (debouncedSearch.trim()) params.search = debouncedSearch.trim();
      if (selectedAlgorithm) params.algorithm = selectedAlgorithm;
      if (selectedDataset) params.dataset = selectedDataset;
      if (selectedMethodology) params.methodology = selectedMethodology;
      if (selectedDomain) params.domain = selectedDomain;
      if (selectedKeyword) params.keyword = selectedKeyword;

      const res = await apiService.getAvailableProjectPapers(projectId, params);
      setAvailablePapers(res.data || []);
    } catch (err) {
      console.error('Failed to load available papers:', err);
      setError('Unable to load available research papers.');
    } finally {
      setLoading(false);
    }
  };

  // Derive filter option sets from available papers
  const filterOptions = useMemo(() => {
    const algs = new Set();
    const datasets = new Set();
    const meths = new Set();
    const doms = new Set();
    const kws = new Set();

    availablePapers.forEach((p) => {
      (p.algorithms || []).forEach((a) => a && algs.add(a));
      (p.datasets || []).forEach((d) => d && datasets.add(d));
      (p.methodologies || []).forEach((m) => m && meths.add(m));
      (p.application_domains || []).forEach((dom) => dom && doms.add(dom));
      (p.keywords || []).forEach((k) => k && kws.add(k));
    });

    return {
      algorithms: Array.from(algs).sort(),
      datasets: Array.from(datasets).sort(),
      methodologies: Array.from(meths).sort(),
      domains: Array.from(doms).sort(),
      keywords: Array.from(kws).sort(),
    };
  }, [availablePapers]);

  const handleTogglePaper = (paperId) => {
    setSelectedPaperIds((prev) => {
      const next = new Set(prev);
      if (next.has(paperId)) {
        next.delete(paperId);
      } else {
        next.add(paperId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedPaperIds.size === availablePapers.length) {
      setSelectedPaperIds(new Set());
    } else {
      setSelectedPaperIds(new Set(availablePapers.map((p) => p.id)));
    }
  };

  const handleAddSelectedPapers = async () => {
    if (selectedPaperIds.size === 0) return;
    setSubmitting(true);
    try {
      const paperIdsArray = Array.from(selectedPaperIds);
      const res = await apiService.bulkAddPapersToProject(projectId, paperIdsArray);
      if (onPapersAdded) {
        onPapersAdded(res.data);
      }
      onClose();
    } catch (err) {
      console.error('Failed to bulk add papers to project:', err);
      alert('Error adding papers to project: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setDebouncedSearch('');
    setSelectedAlgorithm('');
    setSelectedDataset('');
    setSelectedMethodology('');
    setSelectedDomain('');
    setSelectedKeyword('');
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-4 sm:px-6 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="glass-card w-full max-w-4xl max-h-[calc(100vh-7rem)] flex flex-col rounded-3xl border border-indigo-500/30 bg-slate-950 shadow-2xl overflow-hidden">
        
        {/* HEADER */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 shrink-0">
          <div className="space-y-1">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-[10px] font-extrabold uppercase tracking-widest">
              📂 PAPER COLLECTION BUILDER
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Add Research Papers to Project</h2>
            <p className="text-xs text-slate-400">
              Select papers from your research repository to build this project's evidence collection.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-base font-bold p-1 rounded-lg hover:bg-slate-900 transition-all"
            aria-label="Close Modal"
          >
            ✕
          </button>
        </div>

        {/* SEARCH & FILTERS BAR */}
        <div className="p-4 bg-slate-900/60 border-b border-slate-800 space-y-3 shrink-0">
          {/* SEARCH BAR */}
          <div className="relative">
            <span className="absolute left-3.5 top-2.5 text-slate-500 text-xs">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search available papers by title..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-2.5 text-xs text-slate-500 hover:text-slate-200"
              >
                ✕
              </button>
            )}
          </div>

          {/* FILTER CONTROLS */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
            <select
              value={selectedAlgorithm}
              onChange={(e) => setSelectedAlgorithm(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Algorithms</option>
              {filterOptions.algorithms.map((alg, idx) => (
                <option key={idx} value={alg}>{alg}</option>
              ))}
            </select>

            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Datasets</option>
              {filterOptions.datasets.map((ds, idx) => (
                <option key={idx} value={ds}>{ds}</option>
              ))}
            </select>

            <select
              value={selectedMethodology}
              onChange={(e) => setSelectedMethodology(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Methodologies</option>
              {filterOptions.methodologies.map((m, idx) => (
                <option key={idx} value={m}>{m}</option>
              ))}
            </select>

            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Domains</option>
              {filterOptions.domains.map((dom, idx) => (
                <option key={idx} value={dom}>{dom}</option>
              ))}
            </select>

            <select
              value={selectedKeyword}
              onChange={(e) => setSelectedKeyword(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Keywords</option>
              {filterOptions.keywords.map((kw, idx) => (
                <option key={idx} value={kw}>{kw}</option>
              ))}
            </select>
          </div>

          {/* ACTIVE FILTER BADGES */}
          {(debouncedSearch || selectedAlgorithm || selectedDataset || selectedMethodology || selectedDomain || selectedKeyword) && (
            <div className="flex items-center justify-between pt-1">
              <span className="text-[10px] text-slate-400 font-semibold">Active filters applied</span>
              <button
                onClick={clearFilters}
                className="text-[10px] text-indigo-400 font-bold hover:underline"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>

        {/* SELECTION BAR */}
        <div className="px-6 py-2.5 bg-slate-900/40 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              disabled={availablePapers.length === 0}
              className="text-indigo-400 font-bold hover:underline disabled:opacity-50"
            >
              {selectedPaperIds.size === availablePapers.length && availablePapers.length > 0 ? 'Deselect All' : 'Select All'}
            </button>
            <span className="text-slate-500">|</span>
            <span className="text-slate-300 font-semibold">
              <b className="text-indigo-400">{availablePapers.length}</b> papers available
            </span>
          </div>

          <span className="font-extrabold text-indigo-300 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
            {selectedPaperIds.size} paper{selectedPaperIds.size === 1 ? '' : 's'} selected
          </span>
        </div>

        {/* PAPERS SCROLLABLE LIST */}
        <div className="p-6 overflow-y-auto flex-1 space-y-3 scrollbar-thin">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs font-bold text-slate-400">Loading available research papers...</p>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-rose-400 text-xs font-bold space-y-2">
              <p>{error}</p>
              <button onClick={fetchAvailablePapers} className="btn-secondary text-[11px] py-1 px-3">
                Retry
              </button>
            </div>
          ) : availablePapers.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-xs space-y-2">
              <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-xl">
                📄
              </div>
              <p className="font-bold text-slate-300">No additional papers are available for this project.</p>
              <p className="text-[11px] text-slate-500">All research papers in your library are already assigned or do not match your filter parameters.</p>
            </div>
          ) : (
            availablePapers.map((paper) => {
              const isSelected = selectedPaperIds.has(paper.id);
              return (
                <div
                  key={paper.id}
                  onClick={() => handleTogglePaper(paper.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-2 ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-950/50'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}} // Handled by parent container click
                      className="mt-1 w-4 h-4 rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950 shrink-0"
                    />

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-mono text-indigo-400 font-bold">Paper ID #{paper.id}</span>
                        {paper.uploaded_at && (
                          <span className="text-[10px] text-slate-500">
                            Uploaded {new Date(paper.uploaded_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      <h4 className="text-xs font-extrabold text-slate-100 leading-snug">{paper.title}</h4>
                      {paper.abstract && (
                        <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{paper.abstract}</p>
                      )}

                      {/* TAGS */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {paper.algorithms && paper.algorithms.map((alg, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[9px] font-semibold">
                            {alg}
                          </span>
                        ))}
                        {paper.datasets && paper.datasets.map((ds, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[9px] font-semibold">
                            {ds}
                          </span>
                        ))}
                        {paper.application_domains && paper.application_domains.map((dom, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[9px] font-semibold">
                            {dom}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* FOOTER ACTIONS */}
        <div className="p-4 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="btn-secondary py-2 px-4 text-xs font-bold"
          >
            Cancel
          </button>

          <button
            onClick={handleAddSelectedPapers}
            disabled={selectedPaperIds.size === 0 || submitting}
            className="px-5 py-2 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs shadow-md transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {submitting ? 'Assigning Papers...' : `Add ${selectedPaperIds.size} Selected Paper${selectedPaperIds.size === 1 ? '' : 's'}`}
          </button>
        </div>

      </div>
    </div>
  );
}
