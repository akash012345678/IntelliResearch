import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import { apiService } from '../services/api';
import PaperViewModal from '../components/PaperViewModal';
import ProposalWorkspaceModal from '../components/ProposalWorkspaceModal';
import ResearchMap from '../components/ResearchMap';


const NODE_COLORS = {
  PAPER: '#6366f1',       // Indigo
  KEYWORD: '#38bdf8',     // Sky Blue
  ALGORITHM: '#10b981',   // Emerald Green
  DATASET: '#f59e0b',     // Amber
  METHODOLOGY: '#f43f5e', // Rose
  DOMAIN: '#14b8a6',      // Teal
  DEFAULT: '#94a3b8'
};

const NODE_TYPE_LABELS = {
  PAPER: 'Research Paper',
  KEYWORD: 'Keyword',
  ALGORITHM: 'Algorithm',
  DATASET: 'Dataset',
  METHODOLOGY: 'Methodology',
  DOMAIN: 'Application Domain'
};

export default function ResearchAnalysis() {
  const navigate = useNavigate();

  // State
  const [data, setData] = useState(null);
  const [directionsData, setDirectionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Search & Filter
  const [activeView, setActiveView] = useState('map'); // 'map' or 'advanced'
  const [paperQuery, setPaperQuery] = useState('');
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [expandedGapIdx, setExpandedGapIdx] = useState(null);
  const [expandedDirIdx, setExpandedDirIdx] = useState(null);
  const [inspectedNode, setInspectedNode] = useState(null);

  // Proposal Controls
  const [confidenceFilter, setConfidenceFilter] = useState('All');
  const [sortBy, setSortBy] = useState('direction_score');

  // Proposal Workspace State
  const [activeProposalDraft, setActiveProposalDraft] = useState(null);
  const [isProposalWorkspaceOpen, setIsProposalWorkspaceOpen] = useState(false);
  const [draftingDirId, setDraftingDirId] = useState(null);

  // Save Direction State
  const [isSaveDirModalOpen, setIsSaveDirModalOpen] = useState(false);
  const [dirToSave, setDirToSave] = useState(null);
  const [saveDirProjects, setSaveDirProjects] = useState([]);
  const [selectedDirProjectId, setSelectedDirProjectId] = useState('');
  const [newDirProjectName, setNewDirProjectName] = useState('');
  const [savingDir, setSavingDir] = useState(false);
  const [saveDirSuccess, setSaveDirSuccess] = useState(null);

  const handleOpenSaveDirModal = async (dir) => {
    setDirToSave(dir);
    setSaveDirSuccess(null);
    try {
      const res = await apiService.getProjects();
      setSaveDirProjects(res.data || []);
      if (res.data && res.data.length > 0) {
        setSelectedDirProjectId(res.data[0].id.toString());
      } else {
        setSelectedDirProjectId('NEW');
      }
      setIsSaveDirModalOpen(true);
    } catch (err) {
      console.error('Failed to fetch projects list:', err);
      alert('Could not fetch projects list.');
    }
  };

  const handleSaveDirectionSubmit = async (e) => {
    e.preventDefault();
    if (!dirToSave) return;
    setSavingDir(true);

    try {
      let targetProjectId = selectedDirProjectId;
      if (selectedDirProjectId === 'NEW') {
        if (!newDirProjectName.trim()) {
          alert('Please enter a new project name.');
          setSavingDir(false);
          return;
        }
        const newProjRes = await apiService.createProject({ name: newDirProjectName.trim() });
        targetProjectId = newProjRes.data.id;
      }

      await apiService.saveDirection(targetProjectId, {
        project_id: parseInt(targetProjectId, 10),
        source_direction_id: dirToSave.direction_id || 'dir_1',
        title: dirToSave.title,
        description: dirToSave.proposed_direction || dirToSave.gap_title,
        confidence: dirToSave.confidence_level || 'High',
        direction_data: dirToSave
      });

      setIsSaveDirModalOpen(false);
      setSaveDirSuccess(`Research direction saved successfully.`);
      setTimeout(() => setSaveDirSuccess(null), 5000);
    } catch (err) {
      console.error('Failed to save direction:', err);
      alert('Error saving direction: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingDir(false);
    }
  };


  // Handle Proposal Draft Generation
  const handleGenerateDraft = async (directionId) => {
    setDraftingDirId(directionId);
    try {
      const response = await apiService.generateProposalDraft(directionId);
      if (response && response.data && response.data.proposal) {
        setActiveProposalDraft(response.data.proposal);
        setIsProposalWorkspaceOpen(true);
      }
    } catch (err) {
      console.error('Failed to generate proposal draft:', err);
      setExportNotification({
        type: 'error',
        message: 'Unable to synthesize proposal draft. Please try again.'
      });
      setTimeout(() => setExportNotification(null), 4000);
    } finally {
      setDraftingDirId(null);
    }
  };

  // Export State
  const [isExportOpen, setIsExportOpen] = useState(false);

  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState(null);
  const [exportNotification, setExportNotification] = useState(null);

  // Handle Research Directions Export
  const handleExport = async (format) => {
    setIsExportOpen(false);
    setIsExporting(true);
    const formatName = format === 'md' ? 'Markdown' : format === 'json' ? 'JSON' : 'PDF';
    setExportStatus(`Generating ${formatName}...`);

    try {
      const response = await apiService.exportResearchDirections(format, 10);
      let filename = `intelliresearch_research_directions.${format === 'markdown' ? 'md' : format}`;
      const disposition = response.headers ? response.headers['content-disposition'] : null;
      if (disposition && disposition.includes('filename=')) {
        const matches = /filename="?([^";]+)"?/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      const blob = new Blob([response.data], {
        type: (response.headers && response.headers['content-type']) || 'application/octet-stream'
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setExportNotification({
        type: 'success',
        message: `Research directions exported successfully as ${filename}.`
      });
    } catch (err) {
      console.error('Export error:', err);
      setExportNotification({
        type: 'error',
        message: 'Unable to generate the export. Please try again.'
      });
    } finally {
      setIsExporting(false);
      setExportStatus(null);
      setTimeout(() => {
        setExportNotification(null);
      }, 4000);
    }
  };

  const paperGraphRef = useRef();

  const fullGraphRef = useRef();

  // Fetch Global Research Analysis & Actionable Research Directions backend data
  const fetchAnalysisData = async () => {
    setLoading(true);
    setError('');
    try {
      const [respAnalysis, respDirections] = await Promise.all([
        apiService.getResearchAnalysis(),
        apiService.getResearchDirections(10)
      ]);
      setData(respAnalysis.data);
      setDirectionsData(respDirections.data);
    } catch (err) {
      console.error('Failed to fetch research analysis:', err);
      setError('Unable to analyze the research collection. Verify backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysisData();
  }, []);

  // 1. Paper-to-Paper Connection Map Data
  const paperPairGraphData = useMemo(() => {
    if (!data || !data.paper_landscape) return { nodes: [], links: [] };

    const nodes = data.paper_landscape.map(p => ({
      id: `paper_${p.paper_id}`,
      label: p.title,
      type: 'PAPER',
      paper_id: p.paper_id
    }));

    const seenPairs = new Set();
    const links = [];
    (data.paper_relationships || []).forEach(r => {
      const src = r.source_paper_id;
      const tgt = r.target_paper_id;
      if (src === tgt || !src || !tgt) return;
      const lowId = src < tgt ? src : tgt;
      const highId = src < tgt ? tgt : src;
      const key = `${lowId}:${highId}`;
      if (seenPairs.has(key)) return;
      seenPairs.add(key);

      const sim = r.similarity_score > 1 ? r.similarity_score : r.similarity_score * 100;
      links.push({
        source: `paper_${src}`,
        target: `paper_${tgt}`,
        similarity: r.similarity_score,
        label: `${sim.toFixed(1)}%`
      });
    });

    return { nodes, links };
  }, [data]);

  // 2. Full Knowledge Graph Data
  const fullKnowledgeGraphData = useMemo(() => {
    if (!data || !data.paper_landscape) return { nodes: [], links: [] };

    const nodesMap = new Map();
    const links = [];

    data.paper_landscape.forEach(p => {
      const pNodeId = `paper_${p.paper_id}`;
      nodesMap.set(pNodeId, {
        id: pNodeId,
        label: p.title,
        type: 'PAPER',
        paper_id: p.paper_id
      });

      const addConcepts = (items, type) => {
        if (!items) return;
        items.forEach(c => {
          const cId = `${type.toLowerCase()}_${c.toLowerCase().replace(/\s+/g, '_')}`;
          if (!nodesMap.has(cId)) {
            nodesMap.set(cId, {
              id: cId,
              label: c,
              type: type
            });
          }
          links.push({
            source: pNodeId,
            target: cId,
            relation: `HAS_${type}`
          });
        });
      };

      addConcepts(p.algorithms, 'ALGORITHM');
      addConcepts(p.datasets, 'DATASET');
      addConcepts(p.methodologies, 'METHODOLOGY');
      addConcepts(p.application_domains, 'DOMAIN');
      addConcepts(p.keywords, 'KEYWORD');
    });

    return {
      nodes: Array.from(nodesMap.values()),
      links
    };
  }, [data]);

  // Client-side Filtered Papers
  const filteredPapers = useMemo(() => {
    if (!data || !data.paper_landscape) return [];
    if (!paperQuery.trim()) return data.paper_landscape;

    const q = paperQuery.toLowerCase();
    return data.paper_landscape.filter(p => (
      p.title.toLowerCase().includes(q) ||
      (p.abstract && p.abstract.toLowerCase().includes(q)) ||
      p.keywords.some(k => k.toLowerCase().includes(q)) ||
      p.algorithms.some(a => a.toLowerCase().includes(q)) ||
      p.datasets.some(d => d.toLowerCase().includes(q)) ||
      p.methodologies.some(m => m.toLowerCase().includes(q)) ||
      p.application_domains.some(dom => dom.toLowerCase().includes(q))
    ));
  }, [data, paperQuery]);

  // Client-side Filtered and Sorted Research Directions
  const filteredAndSortedDirections = useMemo(() => {
    if (!directionsData || !directionsData.directions) return [];
    let list = [...directionsData.directions];

    if (confidenceFilter !== 'All') {
      list = list.filter(d => d.confidence === confidenceFilter);
    }

    list.sort((a, b) => {
      if (sortBy === 'gap_score') {
        return b.evidence.gap_score - a.evidence.gap_score;
      }
      if (sortBy === 'semantic_evidence') {
        return b.evidence.semantic_evidence - a.evidence.semantic_evidence;
      }
      if (sortBy === 'collection_coverage') {
        return b.evidence.collection_coverage - a.evidence.collection_coverage;
      }
      return b.direction_score - a.direction_score;
    });

    return list;
  }, [directionsData, confidenceFilter, sortBy]);

  // Deterministic Insight Summary
  const deterministicInsight = useMemo(() => {
    if (!data || !data.collection_summary) return null;
    const s = data.collection_summary;
    const algos = data.shared_concepts?.algorithms || [];
    const topAlgoStr = algos.slice(0, 3).map(a => `${a.name} (${a.coverage_percentage}%)`).join(', ') || 'N/A';
    const topRel = data.paper_relationships?.[0];
    const topRelStr = topRel ? `Paper ${topRel.source_paper_id} <-> Paper ${topRel.target_paper_id} (${(topRel.similarity_score * 100).toFixed(1)}% similarity)` : 'None';
    const underrepCount = data.underrepresented_concepts?.length || 0;
    const gapCount = data.research_gap_summary?.total_gaps || 0;
    const directionCount = directionsData?.total_directions || 0;

    return {
      summaryText: `Collection comprises ${s.total_papers} indexed paper(s) spanning ${s.total_graph_nodes} concepts and ${s.total_graph_edges} relationships.`,
      topAlgorithms: topAlgoStr,
      strongestConnection: topRelStr,
      underrepresentedCount: underrepCount,
      gapCount: gapCount,
      directionCount: directionCount
    };
  }, [data, directionsData]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10 animate-fade-in">
      
      {/* 1. TOP SECTION: HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-indigo-400 mb-1">
            <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
            GLOBAL RESEARCH ANALYSIS
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            Analyze Your Research Collection
          </h2>
          <p className="text-sm text-slate-450 mt-1">
            Analyzing {data ? data.collection_summary.total_papers : 'N/A'} research paper(s) to identify relationships, shared concepts, potential gaps, and new research directions.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveView('map')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeView === 'map'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>🗺️</span> Research Map
            </button>
            <button
              onClick={() => setActiveView('advanced')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeView === 'advanced'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>📊</span> Technical Breakdown
            </button>
          </div>

          <button
            onClick={fetchAnalysisData}
            disabled={loading}
            className="btn-primary py-2.5 px-4 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20 whitespace-nowrap"
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {loading ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {/* STATES */}
      {loading ? (
        /* LOADING SKELETON */
        <div className="space-y-8 animate-pulse">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-slate-900/60 rounded-2xl border border-slate-850"></div>
            ))}
          </div>
          <div className="h-[400px] bg-slate-900/60 rounded-3xl border border-slate-850 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-sm font-semibold text-slate-300">Analyzing your research collection...</p>
            </div>
          </div>
        </div>
      ) : error ? (
        /* ERROR STATE */
        <div className="glass-card p-12 rounded-3xl border border-rose-500/30 text-center space-y-4 max-w-xl mx-auto my-12">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-100">Unable to analyze the research collection</h3>
          <p className="text-xs text-slate-400">{error}</p>
          <button onClick={fetchAnalysisData} className="btn-secondary py-2 px-6 text-xs mx-auto">Retry</button>
        </div>
      ) : data && data.collection_summary.total_papers === 0 ? (
        /* EMPTY STATE */
        <div className="glass-card p-12 rounded-3xl border border-slate-800 text-center space-y-4 max-w-xl mx-auto my-12">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-xl font-extrabold text-slate-100">No research papers are currently available</h3>
          <p className="text-xs text-slate-400">Upload research papers to build and analyze your research collection landscape.</p>
          <button
            onClick={() => navigate('/')}
            className="btn-primary py-2.5 px-6 text-xs font-bold inline-flex items-center gap-2 mx-auto"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload Research Papers
          </button>
        </div>
      ) : data ? (
        activeView === 'map' ? (
          <ResearchMap
            data={data}
            directionsData={directionsData}
            scope="global"
            onViewPaper={(paperId) => setSelectedPaperId(paperId)}
            onGenerateDraft={handleGenerateDraft}
            onSaveDirection={handleOpenSaveDirModal}
            draftingDirId={draftingDirId}
          />
        ) : (
          /* MAIN UNIFIED ANALYSIS WORKSPACE (ADVANCED VIEW) */
          <div className="space-y-10">
          
          {/* PART 3 — COLLECTION SUMMARY METRICS */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[
              { title: 'Papers Analyzed', value: data.collection_summary.total_papers, color: 'text-indigo-400', border: 'border-indigo-500/20' },
              { title: 'Concepts Identified', value: data.collection_summary.total_graph_nodes, color: 'text-sky-400', border: 'border-sky-500/20' },
              { title: 'Research Connections', value: data.collection_summary.total_graph_edges, color: 'text-purple-400', border: 'border-purple-500/20' },
              { title: 'Potential Gaps', value: data.collection_summary.total_potential_gaps, color: 'text-rose-400', border: 'border-rose-500/20' },
              { title: 'Algorithms', value: data.collection_summary.total_algorithms, color: 'text-emerald-400', border: 'border-emerald-500/20' },
              { title: 'Datasets', value: data.collection_summary.total_datasets, color: 'text-amber-400', border: 'border-amber-500/20' },
              { title: 'Methodologies', value: data.collection_summary.total_methodologies, color: 'text-rose-400', border: 'border-rose-500/20' },
              { title: 'Domains', value: data.collection_summary.total_domains, color: 'text-teal-400', border: 'border-teal-500/20' }
            ].map((item, idx) => (
              <div key={idx} className={`glass-card p-3.5 rounded-2xl border ${item.border} flex flex-col justify-between space-y-1`}>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{item.title}</span>
                <span className={`text-xl font-extrabold ${item.color}`}>{item.value}</span>
              </div>
            ))}
          </div>

          {/* PART 4 — RESEARCH PAPER LANDSCAPE */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Research Paper Landscape ({filteredPapers.length})
              </h3>

              {/* Filter / Search input */}
              <div className="relative w-full sm:w-72">
                <input
                  type="text"
                  placeholder="Search papers by title, algorithm, dataset..."
                  value={paperQuery}
                  onChange={(e) => setPaperQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500"
                />
                <svg className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPapers.map(paper => (
                <div
                  key={paper.paper_id}
                  onClick={() => setSelectedPaperId(paper.paper_id)}
                  className="glass-card p-5 rounded-3xl border border-slate-800 hover:border-indigo-500/50 cursor-pointer transition-all duration-300 space-y-3 flex flex-col justify-between group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-indigo-400 font-bold">Paper ID: {paper.paper_id}</span>
                    </div>
                    <h4 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 line-clamp-2 leading-snug">
                      {paper.title}
                    </h4>
                    {paper.abstract && (
                      <p className="text-xs text-slate-400 line-clamp-3 italic leading-relaxed">
                        "{paper.abstract}"
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-850">
                    {paper.algorithms.slice(0, 2).map((a, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[10px] font-medium border border-emerald-500/20">{a}</span>
                    ))}
                    {paper.datasets.slice(0, 1).map((d, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 text-[10px] font-medium border border-amber-500/20">{d}</span>
                    ))}
                    {paper.methodologies.slice(0, 1).map((m, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 text-[10px] font-medium border border-rose-500/20">{m}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* PART 5 — PAPER-TO-PAPER CONNECTION MAP */}
          <div className="glass-card rounded-3xl p-5 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  How Are These Papers Connected?
                </h3>
                <p className="text-xs text-slate-450">Visual relationship map highlighting semantic similarities between research papers (e.g. Paper 1 ── 82% ── Paper 2).</p>
              </div>

              <button
                onClick={() => paperGraphRef.current?.zoomToFit(400, 20)}
                className="btn-secondary py-1.5 text-xs px-3 font-semibold flex items-center gap-1 self-start sm:self-auto"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-2V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                Recenter Connection Map
              </button>
            </div>

            <div className="relative rounded-2xl overflow-hidden bg-slate-950/90 border border-slate-900 min-h-[380px] flex items-center justify-center">
              <ForceGraph2D
                ref={paperGraphRef}
                graphData={paperPairGraphData}
                nodeId="id"
                nodeLabel={node => node.label}
                nodeColor={() => NODE_COLORS.PAPER}
                nodeRelSize={7}
                linkColor={() => 'rgba(99, 102, 241, 0.6)'}
                linkWidth={2}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.006}
                onNodeClick={(node) => {
                  if (node.paper_id) setSelectedPaperId(node.paper_id);
                }}
                canvasObject={(node, ctx, globalScale) => {
                  const label = node.label;
                  const fontSize = Math.max(4, 12 / globalScale);
                  const radius = 8;

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                  ctx.fillStyle = NODE_COLORS.PAPER;
                  ctx.fill();
                  ctx.lineWidth = 1.5;
                  ctx.strokeStyle = '#ffffff';
                  ctx.stroke();

                  ctx.font = `bold ${fontSize}px sans-serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'top';
                  ctx.fillStyle = '#ffffff';
                  ctx.fillText(label.length > 25 ? label.slice(0, 22) + '...' : label, node.x, node.y + radius + 3);
                }}
              />
            </div>
          </div>

          {/* PART 6 — SHARED RESEARCH CONCEPTS */}
          <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              Shared Research Concepts
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { title: 'Algorithms', items: data.shared_concepts.algorithms, color: 'bg-emerald-500' },
                { title: 'Datasets', items: data.shared_concepts.datasets, color: 'bg-amber-500' },
                { title: 'Methodologies', items: data.shared_concepts.methodologies, color: 'bg-rose-500' },
                { title: 'Domains', items: data.shared_concepts.domains, color: 'bg-teal-500' },
                { title: 'Keywords', items: data.shared_concepts.keywords, color: 'bg-sky-500' }
              ].map((group, idx) => (
                <div key={idx} className="space-y-3 bg-slate-950/50 p-4 rounded-2xl border border-slate-850">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">{group.title}</h4>
                  <div className="space-y-2.5">
                    {group.items && group.items.length > 0 ? (
                      group.items.slice(0, 5).map((item, i) => {
                        const isCommon = item.coverage_percentage >= 50.0;
                        return (
                          <div key={i} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-200 font-medium truncate max-w-[170px]">{item.name}</span>
                              <div className="flex items-center gap-1.5">
                                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide ${
                                  isCommon ? 'bg-indigo-500/15 text-indigo-300' : 'bg-amber-500/15 text-amber-300'
                                }`}>
                                  {isCommon ? 'COMMON' : 'UNDERREPRESENTED'}
                                </span>
                                <span className="text-slate-400 text-[10px] font-mono">{item.paper_count} papers ({item.coverage_percentage}%)</span>
                              </div>
                            </div>
                            <div className="w-full h-1.5 bg-slate-850 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${group.color}`} style={{ width: `${Math.min(100, item.coverage_percentage)}%` }}></div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-slate-500 italic">None identified</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* PART 7 — UNIFIED KNOWLEDGE GRAPH SECTION */}
          <div className="glass-card rounded-3xl p-5 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Research Knowledge Graph
                </h3>
                <p className="text-xs text-slate-450">Collection-level graph connecting papers to shared algorithms, datasets, methodologies, domains, and keywords.</p>
              </div>

              {/* Node Legend */}
              <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-900/80 p-2 rounded-xl border border-slate-800">
                {Object.entries(NODE_COLORS).filter(([k]) => k !== 'DEFAULT').map(([type, color]) => (
                  <div key={type} className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }}></span>
                    <span className="text-slate-300 font-medium text-[10px]">{NODE_TYPE_LABELS[type] || type}</span>
                  </div>
                ))}
                <button
                  onClick={() => fullGraphRef.current?.zoomToFit(400, 20)}
                  className="btn-secondary py-1 text-[10px] px-2 font-semibold"
                >
                  Recenter
                </button>
              </div>
            </div>

            <div className="relative rounded-2xl overflow-hidden bg-slate-950/90 border border-slate-900 min-h-[420px] flex items-center justify-center">
              <ForceGraph2D
                ref={fullGraphRef}
                graphData={fullKnowledgeGraphData}
                nodeId="id"
                nodeLabel={node => `${NODE_TYPE_LABELS[node.type] || node.type}: ${node.label}`}
                nodeColor={node => NODE_COLORS[node.type] || NODE_COLORS.DEFAULT}
                nodeRelSize={6}
                linkColor={() => 'rgba(148, 163, 184, 0.2)'}
                linkWidth={1}
                linkDirectionalParticles={1}
                linkDirectionalParticleSpeed={0.004}
                onNodeClick={(node) => {
                  if (node.type === 'PAPER' && node.paper_id) {
                    setSelectedPaperId(node.paper_id);
                  } else {
                    setInspectedNode(node);
                  }
                }}
                canvasObject={(node, ctx, globalScale) => {
                  const label = node.label;
                  const fontSize = Math.max(3, 12 / globalScale);
                  const isPaper = node.type === 'PAPER';
                  const radius = isPaper ? 7 : 4;

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                  ctx.fillStyle = NODE_COLORS[node.type] || NODE_COLORS.DEFAULT;
                  ctx.fill();
                  ctx.lineWidth = inspectedNode?.id === node.id ? 2 : 0.8;
                  ctx.strokeStyle = inspectedNode?.id === node.id ? '#ffffff' : 'rgba(255, 255, 255, 0.3)';
                  ctx.stroke();

                  if (globalScale >= 1.2 || isPaper) {
                    ctx.font = `${isPaper ? 'bold' : 'normal'} ${fontSize}px sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    ctx.fillStyle = isPaper ? '#ffffff' : '#cbd5e1';
                    ctx.fillText(label.length > 25 ? label.slice(0, 22) + '...' : label, node.x, node.y + radius + 2);
                  }
                }}
              />
            </div>
          </div>

          {/* PART 8 — "WHAT IS MISSING?" - POTENTIAL RESEARCH GAPS */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Potential Research Gaps (Collection-Based Analysis)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.gaps && data.gaps.map((gap, idx) => (
                <div key={idx} className="glass-card p-5 rounded-3xl border border-slate-800 space-y-4">
                  <div className="flex items-start justify-between gap-3 border-b border-slate-850 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-slate-500">Source Paper ID {gap.source_paper_id}</span>
                      <h4 className="text-xs font-bold text-slate-100 line-clamp-2 mt-0.5">{gap.source_paper_title}</h4>
                    </div>
                    <span className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wide border flex-shrink-0 ${
                      gap.confidence === 'High' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                      gap.confidence === 'Moderate' ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30' :
                      'bg-slate-800 text-slate-300 border-slate-700'
                    }`}>
                      {gap.confidence} Conf.
                    </span>
                  </div>

                  <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-850 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">{gap.relationship_type}</span>
                      <span className="font-bold text-indigo-300">{gap.target_label} ({gap.target_type})</span>
                    </div>
                    <div className="text-right font-mono">
                      <span className="text-[10px] text-slate-500 block uppercase">Gap Score</span>
                      <span className="font-extrabold text-slate-100">{gap.gap_score}</span>
                    </div>
                  </div>

                  {/* Evidence breakdown */}
                  <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono bg-slate-950/40 p-2.5 rounded-xl border border-slate-850">
                    <div>
                      <span className="text-slate-500 block">Link Pred.</span>
                      <span className="text-slate-200 font-bold">{gap.evidence.link_prediction_score}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Cross-Paper</span>
                      <span className="text-slate-200 font-bold">{gap.evidence.cross_paper_support}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Semantic</span>
                      <span className="text-slate-200 font-bold">{gap.evidence.semantic_evidence}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Underrep.</span>
                      <span className="text-slate-200 font-bold">{gap.evidence.underrepresentation_score}</span>
                    </div>
                  </div>

                  {/* Expandable Explanation */}
                  <div className="pt-1">
                    <button
                      onClick={() => setExpandedGapIdx(expandedGapIdx === idx ? null : idx)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors"
                    >
                      <span>Why was this identified?</span>
                      <svg className={`w-3.5 h-3.5 transition-transform ${expandedGapIdx === idx ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {expandedGapIdx === idx && gap.explanation && (
                      <ul className="mt-2 space-y-1 p-3 rounded-xl bg-slate-950/70 border border-slate-850 text-xs text-slate-300 list-disc list-inside animate-fade-in">
                        {gap.explanation.map((exp, i) => (
                          <li key={i} className="leading-relaxed">{exp}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* PART 9 — UNDERREPRESENTED CONCEPTS */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Underrepresented Concepts (Within Current Collection)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.underrepresented_concepts && data.underrepresented_concepts.map((item, idx) => (
                <div key={idx} className="glass-card p-4.5 rounded-3xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 text-[10px] font-bold uppercase tracking-wide border border-amber-500/20">
                      {item.type}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">{item.paper_count} paper ({item.coverage_percentage}% coverage)</span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-100">{item.name}</h4>

                  <div className="w-full h-1.5 bg-slate-850 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-400 rounded-full" style={{ width: `${Math.min(100, item.coverage_percentage)}%` }}></div>
                  </div>

                  <p className="text-xs text-slate-400 italic leading-relaxed">{item.reason}</p>
                </div>
              ))}
            </div>
          </div>

          {/* PART 10 — ACTIONABLE RESEARCH DIRECTIONS & PROPOSAL ENGINE */}
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Actionable Research Directions & Proposals ({filteredAndSortedDirections.length})
                </h3>
                <p className="text-xs text-slate-450 mt-0.5">
                  These directions are derived from evidence across the currently indexed research collection.
                </p>
              </div>

              {/* Filter, Sort & Export Controls */}
              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={confidenceFilter}
                  onChange={(e) => setConfidenceFilter(e.target.value)}
                  className="bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-300 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="All">All Confidence Levels</option>
                  <option value="High">High Confidence</option>
                  <option value="Moderate">Moderate Confidence</option>
                  <option value="Low">Low Confidence</option>
                </select>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-300 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="direction_score">Sort by Direction Score</option>
                  <option value="gap_score">Sort by Gap Score</option>
                  <option value="semantic_evidence">Sort by Semantic Evidence</option>
                  <option value="collection_coverage">Sort by Coverage</option>
                </select>

                {/* Export Control Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setIsExportOpen(!isExportOpen)}
                    disabled={isExporting}
                    className="bg-indigo-600/90 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold px-3 py-1.5 flex items-center gap-1.5 transition-all shadow-sm disabled:opacity-50"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    {isExporting ? (exportStatus || 'Exporting...') : 'Export ▾'}
                  </button>

                  {isExportOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl z-30 p-2 space-y-1 backdrop-blur-md">
                      <div className="text-[10px] font-extrabold text-slate-400 uppercase px-2 py-1 tracking-wider">
                        Export Format
                      </div>
                      <button
                        onClick={() => handleExport('md')}
                        className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-200 hover:bg-indigo-600/20 hover:text-indigo-300 flex items-center gap-2 transition-all font-medium"
                      >
                        <span>📄</span> Markdown (.md)
                      </button>
                      <button
                        onClick={() => handleExport('json')}
                        className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-200 hover:bg-indigo-600/20 hover:text-indigo-300 flex items-center gap-2 transition-all font-medium"
                      >
                        <span>🔷</span> JSON (.json)
                      </button>
                      <button
                        onClick={() => handleExport('pdf')}
                        className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-200 hover:bg-indigo-600/20 hover:text-indigo-300 flex items-center gap-2 transition-all font-medium"
                      >
                        <span>📑</span> PDF (.pdf)
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Export Status Toast Notification */}
            {exportNotification && (
              <div className={`p-3 rounded-2xl border text-xs font-bold flex items-center justify-between transition-all ${
                exportNotification.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              }`}>
                <span>{exportNotification.message}</span>
                <button onClick={() => setExportNotification(null)} className="text-slate-400 hover:text-slate-200 font-bold ml-2">✕</button>
              </div>
            )}


            {filteredAndSortedDirections.length > 0 ? (
              <div className="space-y-6">
                {filteredAndSortedDirections.map((dir, idx) => (
                  <div key={dir.direction_id || idx} className="glass-card p-6 rounded-3xl border border-indigo-900/40 space-y-4">
                    {/* Proposal Header */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-850 pb-4">
                      <div className="space-y-1">
                        <span className="text-[10px] font-extrabold uppercase tracking-widest text-amber-400 flex items-center gap-1.5">
                          <span>💡</span> POTENTIAL RESEARCH DIRECTION
                        </span>
                        <h4 className="text-base font-extrabold text-slate-100">{dir.title}</h4>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase border ${
                          dir.confidence === 'High' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                          dir.confidence === 'Moderate' ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30' :
                          'bg-slate-800 text-slate-300 border-slate-700'
                        }`}>
                          {dir.confidence} Conf.
                        </span>
                        <span className="px-2.5 py-1 rounded-lg bg-slate-900 text-indigo-300 border border-slate-800 text-xs font-mono font-bold">
                          Score: {dir.direction_score}
                        </span>
                      </div>
                    </div>

                    {/* Structured Proposal Content */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1">
                        <span className="text-slate-400 font-bold uppercase text-[10px] block tracking-wider">RESEARCH PROBLEM</span>
                        <p className="text-slate-200 leading-relaxed">{dir.research_problem}</p>
                      </div>
                      <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1">
                        <span className="text-slate-400 font-bold uppercase text-[10px] block tracking-wider">WHY THIS MAY BE WORTH EXPLORING</span>
                        <p className="text-slate-200 leading-relaxed">{dir.motivation}</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1 text-xs">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block tracking-wider">MISSING / UNDERREPRESENTED ASPECT</span>
                      <p className="text-slate-200 leading-relaxed">{dir.missing_aspect}</p>
                    </div>

                    <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 space-y-1 text-xs">
                      <span className="text-indigo-400 font-bold uppercase text-[10px] block tracking-wider">PROPOSED DIRECTION</span>
                      <p className="text-slate-100 font-medium leading-relaxed">{dir.proposed_direction}</p>
                    </div>

                    {/* Supporting Entities Badges */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                      <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-850 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block">CANDIDATE ALGORITHMS</span>
                        <div className="flex flex-wrap gap-1">
                          {dir.candidate_algorithms && dir.candidate_algorithms.length > 0 ? (
                            dir.candidate_algorithms.map((a, i) => (
                              <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-medium" title={a.reason}>
                                {a.name}
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-slate-500 italic">None identified</span>
                          )}
                        </div>
                      </div>

                      <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-850 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">CANDIDATE DATASETS</span>
                        <div className="flex flex-wrap gap-1">
                          {dir.candidate_datasets && dir.candidate_datasets.length > 0 ? (
                            dir.candidate_datasets.map((d, i) => (
                              <span key={i} className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px] font-medium" title={d.reason}>
                                {d.name}
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-slate-500 italic">No dataset evidence available in current collection</span>
                          )}
                        </div>
                      </div>

                      <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-850 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 block">CANDIDATE METHODOLOGIES</span>
                        <div className="flex flex-wrap gap-1">
                          {dir.candidate_methodologies && dir.candidate_methodologies.length > 0 ? (
                            dir.candidate_methodologies.map((m, i) => (
                              <span key={i} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 text-[10px] font-medium">
                                {m.name} ({m.coverage_percentage}%)
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-slate-500 italic">None identified</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 4-Signal Evidence Metrics Bar */}
                    <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono bg-slate-950/70 p-3 rounded-2xl border border-slate-850">
                      <div>
                        <span className="text-slate-500 block uppercase">Gap Score</span>
                        <span className="text-indigo-300 font-bold text-xs">{dir.evidence.gap_score}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase">Semantic Ev.</span>
                        <span className="text-indigo-300 font-bold text-xs">{dir.evidence.semantic_evidence}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase">Link Prediction</span>
                        <span className="text-indigo-300 font-bold text-xs">{dir.evidence.link_prediction_score}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase">Underrep. Score</span>
                        <span className="text-indigo-300 font-bold text-xs">{dir.evidence.underrepresentation_score}</span>
                      </div>
                    </div>

                    {/* Action Bar: Supporting Papers Toggle & Draft Proposal Launcher */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-850">
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          onClick={() => setExpandedDirIdx(expandedDirIdx === idx ? null : idx)}
                          className="btn-secondary py-1.5 px-3 text-xs font-bold flex items-center gap-1.5"
                        >
                          <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                          View Supporting Papers ({dir.supporting_papers ? dir.supporting_papers.length : 0})
                        </button>

                        <button
                          onClick={() => handleGenerateDraft(dir.direction_id || `dir_${idx + 1}`)}
                          disabled={draftingDirId === (dir.direction_id || `dir_${idx + 1}`)}
                          className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-1.5 px-3 rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-md disabled:opacity-50"
                        >
                          <svg className="w-4 h-4 text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          {draftingDirId === (dir.direction_id || `dir_${idx + 1}`) ? 'Synthesizing Proposal...' : '✨ Draft Proposal'}
                        </button>

                        <button
                          onClick={() => handleOpenSaveDirModal(dir)}
                          className="bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-bold py-1.5 px-3 rounded-xl text-xs flex items-center gap-1.5 transition-all"
                        >
                          <span>📌 Save Direction</span>
                        </button>
                      </div>


                      <span className="text-[10px] text-slate-500 italic">{dir.disclaimer}</span>
                    </div>


                    {/* Expandable Supporting Papers Details */}
                    {expandedDirIdx === idx && dir.supporting_papers && dir.supporting_papers.length > 0 && (
                      <div className="space-y-2 p-4 rounded-2xl bg-slate-950/80 border border-slate-850 animate-fade-in">
                        <h5 className="text-xs font-bold uppercase tracking-wider text-slate-300">Supporting Research Papers</h5>
                        <div className="space-y-2">
                          {dir.supporting_papers.map((sp) => (
                            <div
                              key={sp.paper_id}
                              onClick={() => setSelectedPaperId(sp.paper_id)}
                              className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 cursor-pointer transition-all flex items-start justify-between gap-3 group"
                            >
                              <div>
                                <span className="text-[10px] font-mono text-indigo-400 font-bold">Paper ID {sp.paper_id}</span>
                                <h6 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 leading-snug">{sp.title}</h6>
                                <p className="text-[11px] text-slate-400 italic mt-0.5">{sp.role}</p>
                              </div>
                              <span className="text-indigo-400 text-xs font-bold group-hover:underline flex-shrink-0">View Paper →</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              /* Empty State */
              <div className="glass-card p-10 rounded-3xl border border-slate-800 text-center space-y-3 max-w-xl mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="text-base font-bold text-slate-100">No actionable research directions could be derived from the current collection</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Add more related research papers to strengthen cross-paper evidence and surface multi-signal research opportunities.
                </p>
              </div>
            )}
          </div>

          {/* PART 11 — FINAL COLLECTION-LEVEL RESEARCH INSIGHT SUMMARY */}
          {deterministicInsight && (
            <div className="glass-card p-6 rounded-3xl border border-indigo-500/30 space-y-4 bg-gradient-to-r from-slate-950 via-indigo-950/20 to-slate-950">
              <h3 className="text-base font-extrabold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Collection-Level Research Insight
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1">
                  <span className="text-slate-400 font-semibold block">Collection Scope</span>
                  <p className="text-slate-200 leading-relaxed">{deterministicInsight.summaryText}</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1">
                  <span className="text-emerald-400 font-semibold block">Dominant Algorithms</span>
                  <p className="text-slate-200 leading-relaxed">{deterministicInsight.topAlgorithms}</p>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1">
                  <span className="text-purple-400 font-semibold block">Strongest Connection</span>
                  <p className="text-slate-200 leading-relaxed">{deterministicInsight.strongestConnection}</p>
                </div>
              </div>
            </div>
          )}

          {/* FOOTER DISCLAIMER */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-center">
            <p className="text-xs text-slate-400 leading-relaxed">
              {data.collection_disclaimer}
            </p>
          </div>

        </div>
        )
      ) : null}

      {/* PAPER VIEW MODAL INTEGRATION */}
      {selectedPaperId && (
        <PaperViewModal
          paperId={selectedPaperId}
          onClose={() => setSelectedPaperId(null)}
        />
      )}

      {/* PROPOSAL WORKSPACE MODAL INTEGRATION */}
      {isProposalWorkspaceOpen && activeProposalDraft && (
        <ProposalWorkspaceModal
          proposal={activeProposalDraft}
          onClose={() => setIsProposalWorkspaceOpen(false)}
          onSelectPaperId={(paperId) => setSelectedPaperId(paperId)}
        />
      )}

      {/* SAVE DIRECTION DIALOG MODAL */}
      {isSaveDirModalOpen && dirToSave && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 rounded-3xl border border-purple-500/30 bg-slate-950 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>📌</span> Save Direction Snapshot
              </h3>
              <button onClick={() => setIsSaveDirModalOpen(false)} className="text-slate-400 hover:text-white text-sm">✕</button>
            </div>

            <form onSubmit={handleSaveDirectionSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Direction Title</label>
                <input
                  type="text"
                  disabled
                  value={dirToSave.title || ''}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900/60 border border-slate-850 text-xs text-slate-300"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Select Target Research Project</label>
                <select
                  value={selectedDirProjectId}
                  onChange={(e) => setSelectedDirProjectId(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  {saveDirProjects.map((p) => (
                    <option key={p.id} value={p.id.toString()}>
                      {p.name} ({p.status})
                    </option>
                  ))}
                  <option value="NEW">+ Create New Research Project</option>
                </select>
              </div>

              {selectedDirProjectId === 'NEW' && (
                <div className="space-y-1 animate-fade-in">
                  <label className="text-xs font-semibold text-slate-300 block">New Project Name *</label>
                  <input
                    type="text"
                    required
                    value={newDirProjectName}
                    onChange={(e) => setNewDirProjectName(e.target.value)}
                    placeholder="e.g. Autonomous Vision Systems"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-850">
                <button
                  type="button"
                  onClick={() => setIsSaveDirModalOpen(false)}
                  className="btn-secondary py-1.5 px-3 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingDir}
                  className="bg-purple-600 hover:bg-purple-500 text-white font-bold py-1.5 px-4 rounded-xl text-xs shadow-md transition-all disabled:opacity-50"
                >
                  {savingDir ? 'Saving...' : 'Save Direction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );


}
