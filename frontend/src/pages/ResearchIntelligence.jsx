import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import { apiService } from '../services/api';
import PaperViewModal from '../components/PaperViewModal';

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

export default function ResearchIntelligence() {
  const navigate = useNavigate();

  // State
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [gapConfidenceFilter, setGapConfidenceFilter] = useState('All');
  const [conceptTypeFilter, setConceptTypeFilter] = useState('All');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.2);

  // Interaction
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [expandedGapIdx, setExpandedGapIdx] = useState(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState(null);

  const fgRef = useRef();

  // Fetch Global Research Intelligence data
  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await apiService.getResearchIntelligence();
      setData(resp.data);
    } catch (err) {
      console.error('Failed to fetch research intelligence:', err);
      setError('Unable to analyze the research collection. Please verify the backend is active.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Build Graph Data from Landscape & Relationships
  const graphData = useMemo(() => {
    if (!data || !data.paper_landscape) return { nodes: [], links: [] };

    const nodesMap = new Map();
    const links = [];

    // Add Papers
    data.paper_landscape.forEach(p => {
      nodesMap.set(`paper_${p.paper_id}`, {
        id: `paper_${p.paper_id}`,
        label: p.title,
        type: 'PAPER',
        paper_id: p.paper_id
      });

      // Connect Paper -> Concepts
      const addConceptEdges = (items, type) => {
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
            source: `paper_${p.paper_id}`,
            target: cId,
            relation: `HAS_${type}`
          });
        });
      };

      addConceptEdges(p.keywords, 'KEYWORD');
      addConceptEdges(p.algorithms, 'ALGORITHM');
      addConceptEdges(p.datasets, 'DATASET');
      addConceptEdges(p.methodologies, 'METHODOLOGY');
      addConceptEdges(p.application_domains, 'DOMAIN');
    });

    // Add Paper-to-Paper Links meeting similarity threshold
    if (data.paper_relationships) {
      data.paper_relationships.forEach(rel => {
        if (rel.similarity_score >= similarityThreshold) {
          links.push({
            source: `paper_${rel.source_paper_id}`,
            target: `paper_${rel.target_paper_id}`,
            relation: `SIMILAR_TO (${(rel.similarity_score * 100).toFixed(1)}%)`,
            isPaperPair: true
          });
        }
      });
    }

    return {
      nodes: Array.from(nodesMap.values()),
      links
    };
  }, [data, similarityThreshold]);

  // Client-side Filtered Paper Landscape
  const filteredPapers = useMemo(() => {
    if (!data || !data.paper_landscape) return [];
    if (!searchQuery.trim()) return data.paper_landscape;

    const q = searchQuery.toLowerCase();
    return data.paper_landscape.filter(p => {
      return (
        p.title.toLowerCase().includes(q) ||
        (p.abstract && p.abstract.toLowerCase().includes(q)) ||
        p.keywords.some(k => k.toLowerCase().includes(q)) ||
        p.algorithms.some(a => a.toLowerCase().includes(q)) ||
        p.datasets.some(d => d.toLowerCase().includes(q)) ||
        p.methodologies.some(m => m.toLowerCase().includes(q)) ||
        p.application_domains.some(dom => dom.toLowerCase().includes(q))
      );
    });
  }, [data, searchQuery]);

  // Client-side Filtered Research Gaps
  const filteredGaps = useMemo(() => {
    if (!data || !data.gaps) return [];
    return data.gaps.filter(g => {
      const matchConf = gapConfidenceFilter === 'All' || g.confidence === gapConfidenceFilter;
      const matchQuery = !searchQuery.trim() || (
        g.source_paper_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        g.target_label.toLowerCase().includes(searchQuery.toLowerCase())
      );
      return matchConf && matchQuery;
    });
  }, [data, gapConfidenceFilter, searchQuery]);

  // Client-side Filtered Underrepresented Concepts
  const filteredUnderrepresented = useMemo(() => {
    if (!data || !data.underrepresented_concepts) return [];
    return data.underrepresented_concepts.filter(u => {
      const matchType = conceptTypeFilter === 'All' || u.type.toUpperCase() === conceptTypeFilter.toUpperCase();
      const matchQuery = !searchQuery.trim() || u.name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchType && matchQuery;
    });
  }, [data, conceptTypeFilter, searchQuery]);

  // Handle Graph Centering
  const handleResetZoom = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 20);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* 1. HEADER AREA */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight flex items-center gap-2.5">
            <div className="p-2 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            Research Intelligence Dashboard
          </h2>
          <p className="text-sm text-slate-450 mt-1">
            Global analysis of your indexed research collection — synthesizing shared concepts, paper relationships, potential gaps, and candidate research directions.
          </p>
        </div>

        {/* Action Controls */}
        <button
          onClick={fetchData}
          disabled={loading}
          className="btn-primary py-2.5 px-5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20"
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? 'Analyzing Collection...' : 'Analyze Collection / Refresh'}
        </button>
      </div>

      {/* LOADING STATE SKELETON */}
      {loading ? (
        <div className="space-y-8 animate-pulse">
          {/* Skeleton Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-slate-900/60 rounded-2xl border border-slate-850"></div>
            ))}
          </div>

          <div className="h-[450px] bg-slate-900/60 rounded-3xl border border-slate-850 flex items-center justify-center">
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
          <button onClick={fetchData} className="btn-secondary py-2 px-6 text-xs mx-auto">Retry</button>
        </div>
      ) : data && data.collection_summary.total_papers === 0 ? (
        /* EMPTY STATE */
        <div className="glass-card p-12 rounded-3xl border border-slate-800 text-center space-y-4 max-w-xl mx-auto my-12">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-extrabold text-slate-100">No research papers indexed yet</h3>
          <p className="text-xs text-slate-400">
            Upload PDF manuscripts to construct your research landscape and discover potential gaps.
          </p>
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
        /* 2. MAIN DASHBOARD CONTENT */
        <div className="space-y-8">
          
          {/* COLLECTION OVERVIEW METRICS */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[
              { title: 'Total Papers', value: data.collection_summary.total_papers, color: 'text-indigo-400', border: 'border-indigo-500/20' },
              { title: 'Concepts', value: data.collection_summary.total_graph_nodes, color: 'text-sky-400', border: 'border-sky-500/20' },
              { title: 'Connections', value: data.collection_summary.total_graph_edges, color: 'text-purple-400', border: 'border-purple-500/20' },
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

          {/* SEARCH & FILTER BAR */}
          <div className="glass-card p-4 rounded-3xl border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Search Box */}
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search research landscape (titles, concepts, algorithms, domains)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-2xl text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500 transition-all"
              />
              <svg className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Confidence filter */}
              <div className="flex items-center gap-1 p-1 bg-slate-950/60 rounded-xl border border-slate-850 text-xs">
                <span className="text-[10px] text-slate-400 px-2 font-semibold uppercase">Gap Conf:</span>
                {['All', 'High', 'Moderate', 'Low'].map(c => (
                  <button
                    key={c}
                    onClick={() => setGapConfidenceFilter(c)}
                    className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                      gapConfidenceFilter === c ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>

              {/* Concept Type filter */}
              <div className="flex items-center gap-1 p-1 bg-slate-950/60 rounded-xl border border-slate-850 text-xs">
                <span className="text-[10px] text-slate-400 px-2 font-semibold uppercase">Concept:</span>
                {['All', 'Algorithm', 'Dataset', 'Methodology', 'Domain'].map(t => (
                  <button
                    key={t}
                    onClick={() => setConceptTypeFilter(t)}
                    className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                      conceptTypeFilter === t ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 3. INTERACTIVE KNOWLEDGE GRAPH LANDSCAPE */}
          <div className="glass-card rounded-3xl p-5 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Global Research Landscape Visualization
                </h3>
                <p className="text-xs text-slate-450">Interactive graph mapping papers, shared entities, and semantic paper-to-paper connections.</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleResetZoom}
                  className="btn-secondary py-1.5 text-xs px-3 font-semibold flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-2V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                  Recenter Graph
                </button>
              </div>
            </div>

            {/* Canvas Container */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-950/90 border border-slate-900 min-h-[420px] flex items-center justify-center">
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeId="id"
                nodeLabel={node => `${NODE_TYPE_LABELS[node.type] || node.type}: ${node.label}`}
                nodeColor={node => NODE_COLORS[node.type] || NODE_COLORS.DEFAULT}
                nodeRelSize={6}
                linkColor={link => link.isPaperPair ? 'rgba(99, 102, 241, 0.5)' : 'rgba(148, 163, 184, 0.2)'}
                linkWidth={link => link.isPaperPair ? 2 : 1}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                onNodeClick={(node) => {
                  if (node.type === 'PAPER' && node.paper_id) {
                    setSelectedPaperId(node.paper_id);
                  } else {
                    setSelectedGraphNode(node);
                  }
                }}
                canvasObject={(node, ctx, globalScale) => {
                  const label = node.label;
                  const fontSize = Math.max(3, 12 / globalScale);
                  const isPaper = node.type === 'PAPER';
                  const radius = isPaper ? 7 : 4;
                  const color = NODE_COLORS[node.type] || NODE_COLORS.DEFAULT;

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                  ctx.fillStyle = color;
                  ctx.fill();

                  ctx.lineWidth = selectedGraphNode?.id === node.id ? 2 : 0.8;
                  ctx.strokeStyle = selectedGraphNode?.id === node.id ? '#ffffff' : 'rgba(255, 255, 255, 0.3)';
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

          {/* 4. PAPER COLLECTION LANDSCAPE */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Paper Collection ({filteredPapers.length})
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPapers.map(paper => (
                <div
                  key={paper.paper_id}
                  onClick={() => setSelectedPaperId(paper.paper_id)}
                  className="glass-card p-5 rounded-3xl border border-slate-800 hover:border-indigo-500/50 cursor-pointer transition-all duration-300 space-y-3 group flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <h4 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 line-clamp-2 leading-snug">
                      {paper.title}
                    </h4>
                    {paper.abstract && (
                      <p className="text-xs text-slate-400 line-clamp-3 italic leading-relaxed">
                        "{paper.abstract}"
                      </p>
                    )}
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-850/80">
                    {paper.algorithms.slice(0, 2).map((a, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 text-[10px] font-medium border border-emerald-500/20">
                        {a}
                      </span>
                    ))}
                    {paper.datasets.slice(0, 1).map((d, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 text-[10px] font-medium border border-amber-500/20">
                        {d}
                      </span>
                    ))}
                    {paper.methodologies.slice(0, 1).map((m, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-300 text-[10px] font-medium border border-rose-500/20">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 5. SHARED RESEARCH CONCEPTS */}
          <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              Shared Research Concepts
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { title: 'Top Algorithms', items: data.shared_concepts.algorithms, color: 'bg-emerald-500' },
                { title: 'Top Datasets', items: data.shared_concepts.datasets, color: 'bg-amber-500' },
                { title: 'Top Methodologies', items: data.shared_concepts.methodologies, color: 'bg-rose-500' },
                { title: 'Top Domains', items: data.shared_concepts.domains, color: 'bg-teal-500' },
                { title: 'Top Keywords', items: data.shared_concepts.keywords, color: 'bg-sky-500' }
              ].map((group, idx) => (
                <div key={idx} className="space-y-3 bg-slate-950/50 p-4 rounded-2xl border border-slate-850">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">{group.title}</h4>
                  <div className="space-y-2">
                    {group.items && group.items.length > 0 ? (
                      group.items.slice(0, 5).map((item, i) => (
                        <div key={i} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-200 font-medium truncate max-w-[170px]">{item.name}</span>
                            <span className="text-slate-400 text-[10px] font-mono">{item.paper_count} papers ({item.coverage_percentage}%)</span>
                          </div>
                          {/* Visual Bar */}
                          <div className="w-full h-1.5 bg-slate-850 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${group.color}`}
                              style={{ width: `${Math.min(100, item.coverage_percentage)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 italic">None identified</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 6. PAPER RELATIONSHIP CONNECTIONS */}
          {data.paper_relationships && data.paper_relationships.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                Research Paper Connections
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.paper_relationships.slice(0, 6).map((rel, idx) => (
                  <div key={idx} className="glass-card p-4 rounded-3xl border border-slate-800 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <div
                        onClick={() => setSelectedPaperId(rel.source_paper_id)}
                        className="flex-1 p-2.5 rounded-xl bg-slate-950/60 border border-slate-850 hover:border-indigo-500/40 cursor-pointer transition-all"
                      >
                        <span className="text-[10px] font-mono text-slate-500 block">Paper {rel.source_paper_id}</span>
                        <h5 className="text-xs font-bold text-slate-100 line-clamp-1">{rel.source_title}</h5>
                      </div>

                      <div className="flex flex-col items-center px-2">
                        <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                        <span className="text-[10px] font-bold text-indigo-300 font-mono mt-1">
                          {(rel.similarity_score * 100).toFixed(1)}%
                        </span>
                        <span className="text-[9px] uppercase tracking-wider text-slate-500">Semantic Similarity</span>
                      </div>

                      <div
                        onClick={() => setSelectedPaperId(rel.target_paper_id)}
                        className="flex-1 p-2.5 rounded-xl bg-slate-950/60 border border-slate-850 hover:border-indigo-500/40 cursor-pointer transition-all"
                      >
                        <span className="text-[10px] font-mono text-slate-500 block">Paper {rel.target_paper_id}</span>
                        <h5 className="text-xs font-bold text-slate-100 line-clamp-1">{rel.target_title}</h5>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7. POTENTIAL RESEARCH GAPS */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Potential Research Gaps ({filteredGaps.length})
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredGaps.map((gap, idx) => (
                <div key={idx} className="glass-card p-5 rounded-3xl border border-slate-800 space-y-4">
                  {/* Gap Header */}
                  <div className="flex items-start justify-between gap-3 border-b border-slate-850/80 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Source Paper ID {gap.source_paper_id}</span>
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

                  {/* Target Relationship */}
                  <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-850 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase tracking-wider">{gap.relationship_type}</span>
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
                      <span className="text-slate-500 block">Graph</span>
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

          {/* 8. UNDERREPRESENTED RESEARCH CONCEPTS */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Underrepresented Research Concepts ({filteredUnderrepresented.length})
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredUnderrepresented.map((item, idx) => (
                <div key={idx} className="glass-card p-4.5 rounded-3xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 text-[10px] font-bold uppercase tracking-wide border border-amber-500/20">
                      {item.type}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">{item.paper_count} paper ({item.coverage_percentage}% coverage)</span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-100">{item.name}</h4>

                  {/* Coverage Visual Bar */}
                  <div className="w-full h-1.5 bg-slate-850 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-400 rounded-full" style={{ width: `${Math.min(100, item.coverage_percentage)}%` }}></div>
                  </div>

                  <p className="text-xs text-slate-400 italic leading-relaxed">{item.reason}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 9. CANDIDATE RESEARCH DIRECTIONS */}
          {data.candidate_research_directions && data.candidate_research_directions.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Candidate Research Directions
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.candidate_research_directions.map((dir, idx) => (
                  <div key={idx} className="glass-card p-6 rounded-3xl border border-indigo-900/40 hover:border-indigo-500/50 transition-all duration-300 space-y-4 flex flex-col justify-between">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <h4 className="text-sm font-extrabold text-slate-100 flex items-start gap-2 leading-snug">
                          <span className="text-amber-400">💡</span>
                          {dir.title}
                        </h4>
                        <span className="px-2.5 py-0.5 rounded-md bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase tracking-wide flex-shrink-0">
                          {dir.confidence} Conf.
                        </span>
                      </div>

                      <p className="text-xs text-slate-350 leading-relaxed">{dir.description}</p>
                    </div>

                    {/* Metrics Footer */}
                    <div className="space-y-3 pt-3 border-t border-slate-850">
                      <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono bg-slate-950/60 p-2.5 rounded-2xl border border-slate-850">
                        <div>
                          <span className="text-slate-500 block">Gap Score</span>
                          <span className="text-slate-100 font-bold">{dir.evidence.gap_score}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Semantic Ev.</span>
                          <span className="text-slate-100 font-bold">{dir.evidence.semantic_evidence}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Coverage</span>
                          <span className="text-slate-100 font-bold">{dir.evidence.collection_coverage}%</span>
                        </div>
                      </div>

                      <p className="text-[10px] text-slate-500 italic text-center leading-tight">{dir.disclaimer}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 10. FOOTER COLLECTION DISCLAIMER */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-center">
            <p className="text-xs text-slate-400 leading-relaxed">
              {data.collection_disclaimer}
            </p>
          </div>

        </div>
      ) : null}

      {/* PAPER VIEW MODAL INTEGRATION */}
      {selectedPaperId && (
        <PaperViewModal
          paperId={selectedPaperId}
          onClose={() => setSelectedPaperId(null)}
        />
      )}

    </div>
  );
}
