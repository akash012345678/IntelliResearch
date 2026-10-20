import React, { useState, useMemo, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import OpportunityExplorerModal from './OpportunityExplorerModal';
import OpportunityComparisonModal from './OpportunityComparisonModal';
import { filterQualifiedGaps } from '../utils/researchGapUtils';

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

export default function ResearchMap({
  data,
  directionsData = null,
  scope = 'global', // 'global' or 'project'
  projectName = '',
  onViewPaper,
  onGenerateDraft,
  onSaveDirection,
  draftingDirId = null,
  mapOnly = false
}) {
  // Help Panel State
  const [showHelpPanel, setShowHelpPanel] = useState(true);

  // Search & Filters
  const [confidenceFilter, setConfidenceFilter] = useState('All');
  const [sortBy, setSortBy] = useState('direction_score');
  const [paperQuery, setPaperQuery] = useState('');
  const [selectedNodeType, setSelectedNodeType] = useState('ALL');
  const [nodeSearchQuery, setNodeSearchQuery] = useState('');

  // Expandable States
  const [expandedGapIdx, setExpandedGapIdx] = useState(null);
  const [expandedDirIdx, setExpandedDirIdx] = useState(null);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [showAdvancedGraph, setShowAdvancedGraph] = useState(false);

  // Phase 7 Part 2 — Opportunity Explorer & Comparison States
  const [explorerDirId, setExplorerDirId] = useState(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  const toggleCompareSelection = (dirId) => {
    if (selectedCompareIds.includes(dirId)) {
      setSelectedCompareIds(selectedCompareIds.filter(id => id !== dirId));
    } else {
      if (selectedCompareIds.length >= 3) {
        alert('You can select up to 3 research opportunities to compare.');
        return;
      }
      setSelectedCompareIds([...selectedCompareIds, dirId]);
    }
  };

  const fullGraphRef = useRef();

  // Unified Extractors for Global vs Project Data Schemas
  const collectionSummary = useMemo(() => {
    if (!data) return { total_papers: 0 };
    return data.collection_summary || {};
  }, [data]);

  const papersList = useMemo(() => {
    if (!data) return [];
    return data.paper_landscape || [];
  }, [data]);

  const relationshipsList = useMemo(() => {
    if (!data || !data.paper_relationships) return [];
    const rels = data.paper_relationships;
    const seenPairs = new Set();
    const cleanList = [];

    rels.forEach(r => {
      const srcId = r.source_paper_id;
      const tgtId = r.target_paper_id;
      if (srcId === tgtId) return;
      if (r.source_title && r.target_title && r.source_title.trim().toLowerCase() === r.target_title.trim().toLowerCase()) return;

      const lowId = srcId < tgtId ? srcId : tgtId;
      const highId = srcId < tgtId ? tgtId : srcId;
      const pairKey = `${lowId}:${highId}`;
      if (seenPairs.has(pairKey)) return;
      seenPairs.add(pairKey);

      cleanList.push(r);
    });

    return cleanList;
  }, [data]);

  const gapsList = useMemo(() => {
    if (!data) return [];
    const raw = data.research_gaps || data.gaps || [];
    return filterQualifiedGaps(raw);
  }, [data]);

  const underrepresentedList = useMemo(() => {
    if (!data) return [];
    return data.underrepresented_concepts || [];
  }, [data]);

  // Unified Research Opportunities / Directions List with Defensive Deduplication
  const directionsList = useMemo(() => {
    let rawList = [];
    if (directionsData && directionsData.directions && directionsData.directions.length > 0) {
      rawList = directionsData.directions;
    } else if (data && data.candidate_research_directions && data.candidate_research_directions.length > 0) {
      rawList = data.candidate_research_directions;
    }

    const seenOppKeys = new Set();
    const uniqueList = [];
    rawList.forEach(dir => {
      const titleKey = (dir.title || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const probKey = (dir.research_problem || dir.description || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const oppKey = titleKey || probKey || dir.direction_id;
      if (!seenOppKeys.has(oppKey)) {
        seenOppKeys.add(oppKey);
        uniqueList.push(dir);
      }
    });

    return uniqueList;
  }, [data, directionsData]);

  // Filtered and Sorted Directions / Research Opportunities
  const filteredDirections = useMemo(() => {
    let list = [...directionsList];

    if (confidenceFilter !== 'All') {
      list = list.filter(d => {
        const conf = d.confidence || 'Moderate';
        return conf.toUpperCase() === confidenceFilter.toUpperCase();
      });
    }

    list.sort((a, b) => {
      const scoreA = a.direction_score || a.evidence?.gap_score || 0;
      const scoreB = b.direction_score || b.evidence?.gap_score || 0;
      if (sortBy === 'gap_score') {
        const gA = a.evidence?.gap_score || 0;
        const gB = b.evidence?.gap_score || 0;
        return gB - gA;
      }
      if (sortBy === 'semantic_evidence') {
        const sA = a.evidence?.semantic_evidence || 0;
        const sB = b.evidence?.semantic_evidence || 0;
        return sB - sA;
      }
      return scoreB - scoreA;
    });

    return list;
  }, [directionsList, confidenceFilter, sortBy]);

  // Client-side Filtered Papers
  const filteredPapers = useMemo(() => {
    if (!papersList) return [];
    if (!paperQuery.trim()) return papersList;

    const q = paperQuery.toLowerCase();
    return papersList.filter(p => (
      (p.title && p.title.toLowerCase().includes(q)) ||
      (p.abstract && p.abstract.toLowerCase().includes(q)) ||
      (p.keywords && p.keywords.some(k => k.toLowerCase().includes(q))) ||
      (p.algorithms && p.algorithms.some(a => a.toLowerCase().includes(q))) ||
      (p.datasets && p.datasets.some(d => d.toLowerCase().includes(q))) ||
      (p.methodologies && p.methodologies.some(m => m.toLowerCase().includes(q))) ||
      (p.application_domains && p.application_domains.some(dom => dom.toLowerCase().includes(q)))
    ));
  }, [papersList, paperQuery]);

  // Full Knowledge Graph Data for Advanced View & Isolated Map View
  const fullKnowledgeGraphData = useMemo(() => {
    if (!papersList || papersList.length === 0) return { nodes: [], links: [] };

    const nodesMap = new Map();
    const links = [];

    papersList.forEach(p => {
      const pId = p.paper_id || p.id;
      const pNodeId = `paper_${pId}`;
      nodesMap.set(pNodeId, {
        id: pNodeId,
        label: p.title,
        type: 'PAPER',
        paper_id: pId
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
      addConcepts(p.application_domains || p.domains, 'DOMAIN');
      addConcepts(p.keywords, 'KEYWORD');
    });

    (relationshipsList || []).forEach(r => {
      const srcId = r.source_paper_id || r.source_id;
      const tgtId = r.target_paper_id || r.target_id;
      if (!srcId || !tgtId || srcId === tgtId) return;
      const srcNodeId = `paper_${srcId}`;
      const tgtNodeId = `paper_${tgtId}`;
      if (nodesMap.has(srcNodeId) && nodesMap.has(tgtNodeId)) {
        const sim = typeof r.similarity_score === 'number'
          ? (r.similarity_score > 1 ? r.similarity_score : r.similarity_score * 100)
          : parseFloat(r.similarity_score) || 0;
        links.push({
          source: srcNodeId,
          target: tgtNodeId,
          relation: 'SIMILAR_TO',
          similarity: sim
        });
      }
    });

    return {
      nodes: Array.from(nodesMap.values()),
      links
    };
  }, [papersList, relationshipsList]);

  const filteredGraphData = useMemo(() => {
    let nodes = fullKnowledgeGraphData.nodes;

    if (selectedNodeType !== 'ALL') {
      nodes = nodes.filter(n => n.type === selectedNodeType || n.type === 'PAPER');
    }

    if (nodeSearchQuery.trim()) {
      const q = nodeSearchQuery.toLowerCase();
      nodes = nodes.filter(n => n.label.toLowerCase().includes(q));
    }

    const validNodeIds = new Set(nodes.map(n => n.id));
    const links = fullKnowledgeGraphData.links.filter(
      l => validNodeIds.has(typeof l.source === 'object' ? l.source.id : l.source) &&
           validNodeIds.has(typeof l.target === 'object' ? l.target.id : l.target)
    );

    return { nodes, links };
  }, [fullKnowledgeGraphData, selectedNodeType, nodeSearchQuery]);

  const isProjectScope = scope === 'project';
  const totalPapers = collectionSummary.total_papers || papersList.length || 0;

  if (mapOnly) {
    return (
      <div className="space-y-6 animate-fade-in">
        {/* --- HEADER BANNER & SCOPE IDENTIFIER --- */}
        <div className="glass-card p-6 rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/40 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-indigo-400 mb-1">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
                {isProjectScope ? `PROJECT RESEARCH MAP — ${projectName || 'PROJECT'}` : 'GLOBAL RESEARCH MAP'}
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
                Research Knowledge & Relationship Map
              </h2>
              <p className="text-xs sm:text-sm text-slate-350 mt-1 max-w-3xl leading-relaxed">
                Interactive node-edge graph visualization mapping relationships across assigned research papers, algorithms, datasets, methodologies, domains, and keywords.
              </p>
            </div>

            <button
              onClick={() => setShowHelpPanel(!showHelpPanel)}
              className="btn-secondary py-2 px-4 text-xs font-semibold flex items-center gap-2 self-start md:self-auto border-indigo-500/30 text-indigo-300 hover:bg-indigo-900/30 whitespace-nowrap shadow-sm"
            >
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {showHelpPanel ? 'Hide Map Legend' : 'How to Read This Map'}
            </button>
          </div>

          {showHelpPanel && (
            <div className="mt-5 pt-5 border-t border-indigo-900/40 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs animate-slide-up">
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Paper
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Research manuscript indexed in project collection.</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-emerald-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Algorithm
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Machine learning algorithm or model architecture.</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-amber-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Dataset
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Evaluation dataset or image corpus.</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-rose-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Methodology
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Experimental technique or methodology.</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-teal-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span> Domain
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Target application domain.</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
                <span className="font-bold text-sky-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span> Keyword
                </span>
                <p className="text-[11px] text-slate-400 leading-snug">Extracted keyword or concept descriptor.</p>
              </div>
            </div>
          )}
        </div>

        {/* GRAPH VISUALIZATION & CONTROLS CONTAINER */}
        <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-5 bg-slate-900/90 shadow-xl">
          {/* Controls: Node Type Filters & Node Search */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white flex items-center gap-2">
                <span>🗺️</span> Knowledge Graph Network ({collectionSummary.total_nodes || filteredGraphData.nodes.length} Nodes, {collectionSummary.total_edges || filteredGraphData.links.length} Edges)
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs">
              {/* Filter by Node Type */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 overflow-x-auto">
                {['ALL', 'PAPER', 'ALGORITHM', 'DATASET', 'METHODOLOGY', 'DOMAIN', 'KEYWORD'].map((typeKey) => (
                  <button
                    key={typeKey}
                    onClick={() => setSelectedNodeType(typeKey)}
                    className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all whitespace-nowrap ${
                      selectedNodeType === typeKey
                        ? 'bg-indigo-600 text-white shadow'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {typeKey}
                  </button>
                ))}
              </div>

              {/* Node Search Input */}
              <input
                type="text"
                placeholder="Filter graph nodes..."
                value={nodeSearchQuery}
                onChange={(e) => setNodeSearchQuery(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 w-40"
              />
            </div>
          </div>

          {/* Interactive ForceGraph2D Canvas */}
          <div className="relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 min-h-[520px] flex items-center justify-center">
            {filteredGraphData.nodes.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 italic">
                No graph nodes match the active filter criteria.
              </div>
            ) : (
              <ForceGraph2D
                ref={fullGraphRef}
                graphData={filteredGraphData}
                nodeId="id"
                nodeLabel={node => `${NODE_TYPE_LABELS[node.type] || node.type}: ${node.label}`}
                nodeColor={node => NODE_COLORS[node.type] || NODE_COLORS.DEFAULT}
                nodeRelSize={6}
                linkColor={link => link.relation === 'SIMILAR_TO' ? 'rgba(99, 102, 241, 0.7)' : 'rgba(148, 163, 184, 0.25)'}
                linkWidth={link => link.relation === 'SIMILAR_TO' ? 2.5 : 1}
                onNodeClick={(node) => {
                  if (node.type === 'PAPER' && node.paper_id && onViewPaper) {
                    onViewPaper(node.paper_id);
                  }
                }}
              />
            )}
          </div>

          {/* Node Legend Footer */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <div className="flex flex-wrap items-center gap-4 text-[11px] font-medium">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Paper</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Algorithm</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Dataset</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Methodology</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span> Domain</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span> Keyword</span>
            </div>

            <span className="text-[11px] text-slate-500 italic">Click any paper node to view full paper metadata</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">

      {/* --- HEADER BANNER & SCOPE IDENTIFIER --- */}
      <div className="glass-card p-6 rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/40 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-indigo-400 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
              {isProjectScope ? `PROJECT RESEARCH MAP — ${projectName || 'PROJECT'}` : 'GLOBAL RESEARCH MAP'}
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
              Research Opportunity & Discovery Map
            </h2>
            <p className="text-xs sm:text-sm text-slate-350 mt-1 max-w-3xl leading-relaxed">
              {isProjectScope
                ? `Analyzing ${totalPapers} research paper(s) assigned to this project to discover connections, missing concepts, and evidence-grounded research opportunities.`
                : `Analyzing ${totalPapers} indexed research publication(s) across your entire repository to map relationships, gaps, and new research directions.`
              }
            </p>
          </div>

          <button
            onClick={() => setShowHelpPanel(!showHelpPanel)}
            className="btn-secondary py-2 px-4 text-xs font-semibold flex items-center gap-2 self-start md:self-auto border-indigo-500/30 text-indigo-300 hover:bg-indigo-900/30 whitespace-nowrap shadow-sm"
          >
            <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {showHelpPanel ? 'Hide Map Legend' : 'How to Read This Map'}
          </button>
        </div>

        {/* --- COLLAPSIBLE HELP PANEL ("HOW TO READ THIS MAP") --- */}
        {showHelpPanel && (
          <div className="mt-5 pt-5 border-t border-indigo-900/40 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs animate-slide-up">
            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="font-bold text-slate-100 flex items-center gap-1.5">
                <span className="text-base">📄</span> Paper
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">A research manuscript indexed in your collection.</p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="font-bold text-slate-100 flex items-center gap-1.5">
                <span className="text-base">🔗</span> Connection
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">Two papers related by semantic similarity or shared concepts.</p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="font-bold text-emerald-300 flex items-center gap-1.5">
                <span className="text-base">🧠</span> Common Concept
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">Algorithm, dataset, or domain shared across multiple papers.</p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="font-bold text-amber-300 flex items-center gap-1.5">
                <span className="text-base">⚠</span> Underrepresented
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">A concept appearing in only 1 or very few papers in your collection.</p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-1">
              <span className="font-bold text-rose-300 flex items-center gap-1.5">
                <span className="text-base">🔎</span> Potential Gap
              </span>
              <p className="text-[11px] text-slate-400 leading-snug">A combination supported by signals but not currently present.</p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/70 border border-indigo-500/30 bg-indigo-950/20 space-y-1">
              <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                <span className="text-base">💡</span> Opportunity
              </span>
              <p className="text-[11px] text-slate-350 leading-snug">An evidence-grounded research direction you could investigate.</p>
            </div>
          </div>
        )}

        {/* --- VISUAL RESEARCH FLOW INDICATOR --- */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between overflow-x-auto text-[11px] font-bold text-slate-400 space-x-2 no-scrollbar">
          <div className="flex items-center gap-1.5 whitespace-nowrap text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-xl border border-indigo-500/20">
            <span>📄</span> {totalPapers} PAPERS
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20">
            <span>🧠</span> COMMON CONCEPTS
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded-xl border border-amber-500/20">
            <span>⚠</span> {underrepresentedList.length} UNDERREPRESENTED
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-rose-400 bg-rose-500/10 px-3 py-1.5 rounded-xl border border-rose-500/20">
            <span>🔎</span> {gapsList.length} POTENTIAL GAPS
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-sky-400 bg-sky-500/10 px-3 py-1.5 rounded-xl border border-sky-500/20 shadow-md shadow-sky-500/10">
            <span>💡</span> {filteredDirections.length} RESEARCH OPPORTUNITIES
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-purple-300 bg-purple-500/15 px-3 py-1.5 rounded-xl border border-purple-500/30">
            <span>📝</span> DRAFT PROPOSAL
          </div>
        </div>
      </div>


      {/* ========================================================================= */}
      {/* 1. PRIMARY SECTION: 💡 EVIDENCE-GROUNDED RESEARCH OPPORTUNITIES */}
      {/* ========================================================================= */}
      <div className="space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center text-lg">
                💡
              </span>
              Research Opportunities ({filteredDirections.length})
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Evidence-grounded new research directions derived directly from your indexed paper collection.
            </p>
          </div>

          {/* Controls: Filter & Sort */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase px-2 font-bold">Confidence:</span>
              {['All', 'High', 'Moderate'].map((conf) => (
                <button
                  key={conf}
                  onClick={() => setConfidenceFilter(conf)}
                  className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all ${
                    confidenceFilter === conf
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {conf}
                </button>
              ))}
            </div>

            {selectedCompareIds.length > 0 && (
              <button
                onClick={() => setShowComparisonModal(true)}
                className="py-1 px-3 rounded-xl font-bold text-xs bg-purple-600 hover:bg-purple-500 text-white shadow-md flex items-center gap-1.5 transition-all animate-pulse"
              >
                <span>⚖</span> Compare Selected ({selectedCompareIds.length})
              </button>
            )}

            <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase px-2 font-bold">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none pr-2 cursor-pointer"
              >
                <option value="direction_score" className="bg-slate-900">Highest Score</option>
                <option value="gap_score" className="bg-slate-900">Highest Gap Score</option>
                <option value="semantic_evidence" className="bg-slate-900">Highest Semantic Relevance</option>
              </select>
            </div>
          </div>
        </div>

        {/* Opportunities List */}
        {filteredDirections.length > 0 ? (
          <div className="space-y-6">
            {filteredDirections.map((dir, idx) => {
              const dirId = dir.direction_id || `dir_${idx + 1}`;
              const isDrafting = draftingDirId === dirId;
              const isExpanded = expandedDirIdx === idx;
              const conf = dir.confidence || 'Moderate';
              const evidence = dir.evidence || {};
              const gapScorePct = Math.round((evidence.gap_score || 0.7) * 100);
              const semanticPct = Math.round((evidence.semantic_evidence || 0.75) * 100);
              const coveragePct = evidence.collection_coverage || 25;

              return (
                <div
                  key={dirId}
                  className="glass-card rounded-3xl p-6 border border-slate-800 hover:border-indigo-500/40 transition-all duration-300 space-y-5 bg-gradient-to-b from-slate-900/90 to-slate-950/90 shadow-xl relative group"
                >
                  {/* Top Header: Opportunity Number & Badges */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono font-extrabold text-xs">
                        Opportunity #{idx + 1}
                      </span>
                      {(() => {
                        const evClass = (evidence.evidence_classification || 'CROSS_PAPER_SYNTHESIS').toUpperCase();
                        let badgeStyle = 'bg-purple-500/10 text-purple-300 border-purple-500/30';
                        let labelText = 'Cross-Paper Synthesis';
                        if (evClass === 'DIRECTLY_SUPPORTED') {
                          badgeStyle = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
                          labelText = 'Directly Supported';
                        } else if (evClass === 'STRONGLY_INFERRED') {
                          badgeStyle = 'bg-blue-500/10 text-blue-300 border-blue-500/30';
                          labelText = 'Strongly Inferred';
                        } else if (evClass === 'CROSS_PAPER_SYNTHESIS') {
                          badgeStyle = 'bg-purple-500/10 text-purple-300 border-purple-500/30';
                          labelText = 'Cross-Paper Synthesis';
                        } else if (evClass === 'EXPLORATORY') {
                          badgeStyle = 'bg-amber-500/10 text-amber-300 border-amber-500/30';
                          labelText = 'Exploratory Direction';
                        }
                        return (
                          <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide border ${badgeStyle}`}>
                            {labelText}
                          </span>
                        );
                      })()}
                      <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide border ${
                        conf.toUpperCase() === 'HIGH' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                        conf.toUpperCase() === 'MODERATE' ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30' :
                        'bg-amber-500/10 text-amber-300 border-amber-500/30'
                      }`}>
                        {conf} Confidence
                      </span>
                      <label className="flex items-center gap-1.5 cursor-pointer text-xs font-bold text-slate-300 hover:text-white bg-slate-950/60 px-2.5 py-1 rounded-xl border border-slate-800" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedCompareIds.includes(dirId)}
                          onChange={() => toggleCompareSelection(dirId)}
                          className="rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-800"
                        />
                        <span>Compare</span>
                      </label>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-mono">
                      {(() => {
                        const evClass = (evidence.evidence_classification || 'CROSS_PAPER_SYNTHESIS').toUpperCase();
                        const isCrossPaper = evClass === 'CROSS_PAPER_SYNTHESIS' || evClass === 'EXPLORATORY';
                        const scorePct = Math.round((evidence.opportunity_score || evidence.gap_score || 0.75) * 100);
                        return (
                          <span className="text-slate-400">
                            {isCrossPaper ? 'Opportunity Score:' : 'Gap Score:'} <strong className="text-slate-100">{scorePct}%</strong>
                          </span>
                        );
                      })()}
                      <span className="text-slate-400">Semantic Evidence: <strong className="text-indigo-300">{semanticPct}%</strong></span>
                      <span className="text-slate-400">Coverage: <strong className="text-amber-300">{coveragePct}%</strong></span>
                    </div>
                  </div>

                  {/* Title, Research Question & Core Problem */}
                  <div className="space-y-3">
                    <h4 className="text-lg font-bold text-slate-100 leading-snug group-hover:text-indigo-300 transition-colors">
                      {dir.title}
                    </h4>

                    {dir.research_question && (
                      <div className="p-3.5 rounded-2xl bg-purple-950/20 border border-purple-900/40 text-xs text-purple-200 flex items-start gap-2.5 shadow-inner">
                        <span className="text-purple-400 font-extrabold text-sm">❓</span>
                        <div>
                          <span className="text-[10px] font-extrabold text-purple-400 uppercase tracking-wider block mb-0.5">
                            Core Research Question
                          </span>
                          <p className="italic font-medium leading-relaxed text-purple-100">"{dir.research_question}"</p>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* What existing research does */}
                      <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-850 space-y-1.5">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                          Current Collection Context
                        </span>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {dir.research_problem || dir.description || 'Collection studies baseline methodologies in this domain.'}
                        </p>
                      </div>

                      {/* What is missing & Proposed contribution */}
                      <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 space-y-1.5">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">
                          Potential Contribution / Opportunity
                        </span>
                        <p className="text-xs text-indigo-200 leading-relaxed">
                          {dir.proposed_direction || dir.missing_aspect || 'Investigate combining baseline techniques with underrepresented concept.'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Supporting Papers & Candidate Tech Tags */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                    {/* Supporting Papers */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>📄</span> Supporting Collection Papers:
                      </span>
                      <div className="space-y-1.5">
                        {dir.supporting_papers && dir.supporting_papers.length > 0 ? (
                          dir.supporting_papers.map((sp, pIdx) => {
                            const pTitle = typeof sp === 'string' ? sp : (sp.title || `Paper ID ${sp.paper_id}`);
                            const pId = typeof sp === 'object' ? sp.paper_id : null;
                            const pRole = typeof sp === 'object' ? sp.role : null;

                            return (
                              <div
                                key={pIdx}
                                onClick={() => pId && onViewPaper && onViewPaper(pId)}
                                className={`p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs transition-colors ${pId ? 'hover:border-indigo-500/50 cursor-pointer' : ''}`}
                              >
                                <span className="text-slate-200 font-medium truncate max-w-[280px]" title={pTitle}>
                                  {pTitle}
                                </span>
                                {pRole && <span className="text-[10px] text-slate-500 italic ml-2 flex-shrink-0">{pRole}</span>}
                              </div>
                            );
                          })
                        ) : (
                          <p className="text-xs text-slate-500 italic">Collection baseline papers</p>
                        )}
                      </div>
                    </div>

                    {/* Candidate Algorithms & Datasets */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>⚙</span> Candidate Tech & Datasets:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {dir.candidate_algorithms && dir.candidate_algorithms.map((algo, aIdx) => (
                          <span key={aIdx} className="px-2.5 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold" title={algo.reason || ''}>
                            Algorithm: {typeof algo === 'string' ? algo : algo.name}
                          </span>
                        ))}
                        {dir.candidate_datasets && dir.candidate_datasets.map((ds, dIdx) => (
                          <span key={dIdx} className="px-2.5 py-1 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold" title={ds.reason || ''}>
                            Dataset: {typeof ds === 'string' ? ds : ds.name}
                          </span>
                        ))}
                        {dir.supporting_concepts && dir.supporting_concepts.map((sc, sIdx) => (
                          <span key={sIdx} className="px-2.5 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
                            Concept: {sc}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions & Evidence Toggle */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-800/80 pt-4 mt-2">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setExpandedDirIdx(isExpanded ? null : idx)}
                        className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                      >
                        <span>{isExpanded ? 'Hide Technical Evidence' : 'View Evidence & Signals'}</span>
                        <svg className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {onSaveDirection && (
                        <button
                          onClick={() => onSaveDirection(dir)}
                          className="text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          Save to Project
                        </button>
                      )}
                    </div>

                    {/* Primary CTAs: Explorer & Draft Research Proposal */}
                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <button
                        onClick={() => setExplorerDirId(dirId)}
                        className="btn-secondary py-2 px-4 text-xs font-bold flex items-center gap-1.5 border-indigo-500/30 text-indigo-300 hover:bg-indigo-900/30 transition-all shadow-sm"
                      >
                        <span>💡</span> View Opportunity
                      </button>

                      <button
                        onClick={() => onGenerateDraft && onGenerateDraft(dirId)}
                        disabled={isDrafting}
                        className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20"
                      >
                        {isDrafting ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            Synthesizing Proposal...
                          </>
                        ) : (
                          <>
                            <span>✨</span> Draft Research Proposal
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Technical Evidence Expansion */}
                  {isExpanded && (
                    <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-3 animate-fade-in text-xs">
                      <span className="font-bold text-slate-200 block uppercase tracking-wider text-[10px]">
                        Multi-Signal Evidence Breakdown:
                      </span>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                        <div className="p-2 rounded-xl bg-slate-900 border border-slate-850">
                          <span className="text-slate-500 block text-[10px]">Gap Score</span>
                          <span className="text-emerald-400 font-bold">{gapScorePct}%</span>
                        </div>
                        <div className="p-2 rounded-xl bg-slate-900 border border-slate-850">
                          <span className="text-slate-500 block text-[10px]">Semantic Similarity</span>
                          <span className="text-indigo-400 font-bold">{semanticPct}%</span>
                        </div>
                        <div className="p-2 rounded-xl bg-slate-900 border border-slate-850">
                          <span className="text-slate-500 block text-[10px]">Link Prediction</span>
                          <span className="text-amber-400 font-bold">{Math.round((evidence.link_prediction_score || 0.7) * 100)}%</span>
                        </div>
                        <div className="p-2 rounded-xl bg-slate-900 border border-slate-850">
                          <span className="text-slate-500 block text-[10px]">Underrepresentation</span>
                          <span className="text-rose-400 font-bold">{Math.round((evidence.underrepresentation_score || 0.3) * 100)}%</span>
                        </div>
                      </div>
                      {dir.disclaimer && (
                        <p className="text-[11px] text-slate-500 italic mt-2">
                          Disclaimer: {dir.disclaimer}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="glass-card rounded-3xl p-10 text-center space-y-3 border border-slate-800">
            <p className="text-sm font-bold text-slate-300">No research opportunities match filter criteria.</p>
            <button onClick={() => setConfidenceFilter('All')} className="btn-secondary py-1.5 text-xs px-4">Reset Filters</button>
          </div>
        )}
      </div>


      {/* ========================================================================= */}
      {/* 2. SECTION: 🔎 "WHAT IS MISSING?" (POTENTIAL RESEARCH GAPS) */}
      {/* ========================================================================= */}
      <div className="space-y-5 pt-4">
        <div>
          <h3 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center text-lg">
              🔎
            </span>
            What Is Missing? (Potential Research Gaps)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Potential research gaps identified from structural, semantic, and underrepresentation signals across your collection.
          </p>
        </div>

        {gapsList && gapsList.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gapsList.map((gap, idx) => {
              const gapId = gap.gap_id || `gap_${idx}`;
              const isExpanded = expandedGapIdx === idx;
              const gapTitle = gap.title || `Potential Gap #${idx + 1}: ${gap.missing_concept || 'Unassessed Relationship'}`;
              const gapType = gap.gap_type || gap.concept_type || 'CROSS_PAPER_COMPARISON';
              const description = gap.description || gap.explanation || 'Unassessed relationship across indexed collection.';
              const conf = gap.confidence || 'Moderate';
              const gapScorePct = typeof gap.gap_score === 'number' ? Math.round(gap.gap_score * 100) : gap.gap_score;
              const suppPapers = gap.source_papers && gap.source_papers.length > 0 ? gap.source_papers : (gap.source_paper_title ? [{ title: gap.source_paper_title, paper_id: gap.source_paper_id }] : []);

              return (
                <div key={gapId} className="glass-card p-5 rounded-3xl border border-slate-800 space-y-4 flex flex-col justify-between bg-slate-900/80 hover:border-rose-500/30 transition-all shadow-lg">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3 border-b border-slate-850 pb-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide bg-rose-500/10 text-rose-300 border border-rose-500/30">
                          {gapType.replace(/_/g, ' ')}
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide border ${
                          conf.toUpperCase() === 'HIGH' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                          conf.toUpperCase() === 'MODERATE' ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30' :
                          'bg-slate-800 text-slate-300 border-slate-700'
                        }`}>
                          {conf} Conf.
                        </span>
                        {gap.evidence?.eligibility_status && (
                          <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            {gap.evidence.eligibility_status.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                      <div className="text-right font-mono flex-shrink-0">
                        <div title="Gap Score represents the strength of the collection-level missing relationship based on multiple evidence signals. It does not represent probability of global research novelty.">
                          <span className="text-[10px] text-slate-500 block uppercase cursor-help">Gap Score ℹ️</span>
                          <span className="font-extrabold text-rose-300 text-base">{gapScorePct}%</span>
                        </div>
                        {gap.evidence?.relationship_evidence_score !== undefined && (
                          <div title="Measures how strongly the indexed papers support the scientific compatibility and evidence for this relationship." className="mt-1">
                            <span className="text-[9px] text-slate-500 block uppercase cursor-help">Rel. Evidence ℹ️</span>
                            <span className="font-bold text-indigo-300 text-xs">{Math.round(gap.evidence.relationship_evidence_score * 100)}%</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <h4 className="text-sm font-bold text-slate-100 leading-snug">
                        {gapTitle}
                      </h4>
                      <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-2xl border border-slate-850">
                        {description}
                      </p>
                    </div>

                    {/* Related Concepts & Supporting Papers */}
                    <div className="space-y-2 pt-1">
                      {gap.related_concepts && gap.related_concepts.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 items-center">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">Components:</span>
                          {gap.related_concepts.map((c, cIdx) => (
                            <span key={cIdx} className="px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-semibold">
                              {c}
                            </span>
                          ))}
                        </div>
                      )}

                      {suppPapers.length > 0 && (
                        <div className="text-[11px] text-slate-400 space-y-1">
                          <span className="text-[10px] font-bold text-slate-500 uppercase block">Supporting Papers in Collection:</span>
                          <ul className="space-y-1">
                            {suppPapers.map((sp, spIdx) => (
                              <li key={spIdx} className="text-slate-300 truncate flex items-center gap-1.5">
                                <span className="text-rose-400 text-xs">•</span>
                                <span className="truncate">{sp.title || `Paper ID ${sp.paper_id}`}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {gap.evidence?.evidence_aliases?.length > 0 && (
                        <div className="flex flex-wrap gap-1 items-center pt-1 border-t border-slate-850/50 mt-1">
                          <span className="text-[10px] font-bold text-slate-500 uppercase mr-1">Evidence Terms:</span>
                          {gap.evidence.evidence_aliases.map((alias, aIdx) => (
                            <span key={aIdx} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                              {alias}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step-by-Step Human Readable Explanation */}
                  <div className="pt-2 border-t border-slate-850 space-y-2">
                    <button
                      onClick={() => setExpandedGapIdx(isExpanded ? null : idx)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors"
                    >
                      <span>Why was this identified?</span>
                      <svg className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {isExpanded && (
                      <div className="p-3 rounded-2xl bg-slate-950/90 border border-slate-850 space-y-2 text-xs text-slate-300 animate-fade-in">
                        {gap.gap_reasoning && Object.keys(gap.gap_reasoning).length > 0 ? (
                          <ul className="space-y-1.5 list-disc list-inside leading-relaxed text-[11px]">
                            {gap.gap_reasoning.component_a_evidence && (
                              <li><strong className="text-slate-200">Component A Evidence:</strong> {typeof gap.gap_reasoning.component_a_evidence === 'object' ? gap.gap_reasoning.component_a_evidence.description : gap.gap_reasoning.component_a_evidence}</li>
                            )}
                            {gap.gap_reasoning.component_b_evidence && (
                              <li><strong className="text-slate-200">Component B Evidence:</strong> {typeof gap.gap_reasoning.component_b_evidence === 'object' ? gap.gap_reasoning.component_b_evidence.description : gap.gap_reasoning.component_b_evidence}</li>
                            )}
                            {gap.gap_reasoning.missing_relationship && (
                              <li><strong className="text-slate-200">Missing Relationship:</strong> {typeof gap.gap_reasoning.missing_relationship === 'object' ? gap.gap_reasoning.missing_relationship.description : gap.gap_reasoning.missing_relationship}</li>
                            )}
                            {gap.gap_reasoning.task_alignment && (
                              <li><strong className="text-slate-200">Task Alignment:</strong> {typeof gap.gap_reasoning.task_alignment === 'object' ? gap.gap_reasoning.task_alignment.description : gap.gap_reasoning.task_alignment}</li>
                            )}
                            {gap.gap_reasoning.scientific_compatibility && (
                              <li><strong className="text-slate-200">Scientific Compatibility:</strong> {typeof gap.gap_reasoning.scientific_compatibility === 'object' ? gap.gap_reasoning.scientific_compatibility.description : gap.gap_reasoning.scientific_compatibility}</li>
                            )}
                            {gap.gap_reasoning.evidence_limitation && (
                              <li className="text-amber-400/90 italic pt-1"><strong className="text-amber-300 font-semibold uppercase text-[10px]">Collection Limitation:</strong> {typeof gap.gap_reasoning.evidence_limitation === 'object' ? gap.gap_reasoning.evidence_limitation.statement : gap.gap_reasoning.evidence_limitation}</li>
                            )}
                          </ul>
                        ) : (
                          <ol className="space-y-1.5 list-decimal list-inside leading-relaxed text-[11px]">
                            <li>Components <strong>{gap.related_concepts ? gap.related_concepts.join(' and ') : gap.missing_concept}</strong> exist separately across indexed papers in your collection.</li>
                            <li>No single indexed paper directly evaluates or combines these components together.</li>
                            <li>Semantic similarity and task relevance indicate strong potential for integrated research.</li>
                            <li>Therefore, investigating their unassessed relationship is identified as a potential research gap.</li>
                          </ol>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="glass-card rounded-3xl p-8 text-center text-xs text-slate-400 border border-slate-800">
            No strong potential research gaps were identified in the current collection.
          </div>
        )}
      </div>


      {/* ========================================================================= */}
      {/* 3. SECTION: 📄 STRUCTURED PAPER LANDSCAPE & RELATIONSHIPS */}
      {/* ========================================================================= */}
      <div className="space-y-6 pt-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-lg">
                📄
              </span>
              Paper Landscape & Connections ({filteredPapers.length})
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Structured cards representing indexed manuscripts and pairwise relationship strength.
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <input
              type="text"
              placeholder="Search papers by title or algorithm..."
              value={paperQuery}
              onChange={(e) => setPaperQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500"
            />
            <svg className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Paper Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPapers.map(paper => {
            const pId = paper.paper_id || paper.id;
            return (
              <div
                key={pId}
                onClick={() => onViewPaper && onViewPaper(pId)}
                className="glass-card p-5 rounded-3xl border border-slate-800 hover:border-indigo-500/50 cursor-pointer transition-all duration-300 space-y-3 flex flex-col justify-between group bg-slate-900/60 hover:bg-slate-900/90"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-indigo-400 font-bold">Paper ID: {pId}</span>
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
                  {paper.algorithms && paper.algorithms.slice(0, 2).map((a, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[10px] font-medium border border-emerald-500/20">{a}</span>
                  ))}
                  {paper.datasets && paper.datasets.slice(0, 1).map((d, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 text-[10px] font-medium border border-amber-500/20">{d}</span>
                  ))}
                  {paper.methodologies && paper.methodologies.slice(0, 1).map((m, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 text-[10px] font-medium border border-rose-500/20">{m}</span>
                  ))}
                  {paper.application_domains && paper.application_domains.slice(0, 1).map((dom, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 text-[10px] font-medium border border-teal-500/20">{dom}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Pairwise Paper Connections Map */}
        {relationshipsList && relationshipsList.length > 0 && (
          <div className="glass-card p-5 rounded-3xl border border-slate-800 space-y-4">
            <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <span>🔗</span> How Are Papers Related in This Collection?
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {relationshipsList.slice(0, 6).map((rel, idx) => {
                const simVal = typeof rel.similarity_score === 'number'
                  ? (rel.similarity_score > 1 ? rel.similarity_score : rel.similarity_score * 100).toFixed(1)
                  : rel.similarity_score;

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedConnection(rel)}
                    className="p-4 rounded-2xl bg-slate-950/70 border border-slate-850 hover:border-indigo-500/40 cursor-pointer transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span className="text-slate-200 truncate max-w-[140px]" title={rel.source_title || rel.source_paper_title}>
                        {rel.source_title || rel.source_paper_title || `Paper ${rel.source_paper_id}`}
                      </span>

                      <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono whitespace-nowrap">
                        {simVal}% Similar
                      </span>

                      <span className="text-slate-200 truncate max-w-[140px]" title={rel.target_title || rel.target_paper_title}>
                        {rel.target_title || rel.target_paper_title || `Paper ${rel.target_paper_id}`}
                      </span>
                    </div>

                    {rel.shared_concepts && rel.shared_concepts.length > 0 && (
                      <div className="text-[11px] text-slate-400 flex items-center gap-1 truncate pt-1 border-t border-slate-900">
                        <span className="text-slate-500">Shared:</span>
                        <span className="text-indigo-300">{rel.shared_concepts.join(', ')}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>


      {/* ========================================================================= */}
      {/* 4. SECTION: 🧠 SHARED RESEARCH CONCEPTS (COMMON VS UNDERREPRESENTED) */}
      {/* ========================================================================= */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-5 pt-4">
        <div>
          <h3 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg">
              🧠
            </span>
            What Do These Papers Have In Common?
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Categorized research concepts identified across the collection.
          </p>
        </div>

        {/* Student Helper Text for Underrepresented Concepts */}
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 leading-relaxed flex items-start gap-3">
          <span className="text-lg flex-shrink-0">💡</span>
          <div>
            <strong className="font-bold text-amber-300 block mb-0.5">Understanding Underrepresented Concepts:</strong>
            "Underrepresented" means this concept appears in only a small number of papers in your current collection. It does <strong>NOT</strong> automatically mean the concept is globally unexplored.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { title: 'Algorithms', items: data?.shared_concepts?.algorithms, color: 'bg-emerald-500' },
            { title: 'Datasets', items: data?.shared_concepts?.datasets, color: 'bg-amber-500' },
            { title: 'Methodologies', items: data?.shared_concepts?.methodologies, color: 'bg-rose-500' },
            { title: 'Domains', items: data?.shared_concepts?.domains, color: 'bg-teal-500' },
            { title: 'Tasks', items: data?.shared_concepts?.tasks, color: 'bg-indigo-500' },
            { title: 'Metrics', items: data?.shared_concepts?.metrics, color: 'bg-cyan-500' },
            { title: 'Applications', items: data?.shared_concepts?.applications, color: 'bg-violet-500' },
            { title: 'Keywords', items: data?.shared_concepts?.keywords, color: 'bg-sky-500' }
          ].map((group, idx) => (
            <div key={idx} className="space-y-3 bg-slate-950/50 p-4 rounded-2xl border border-slate-850">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                {group.title} ({group.items?.length || 0})
              </h4>
              <div className="space-y-2.5">
                {group.items && group.items.length > 0 ? (
                  group.items.slice(0, 5).map((item, i) => {
                    const isCommon = item.coverage_percentage >= 50.0 || item.paper_count > 1;
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


      {/* ========================================================================= */}
      {/* 5. SECTION: ⚙ ADVANCED TECHNICAL KNOWLEDGE GRAPH (COLLAPSIBLE) */}
      {/* ========================================================================= */}
      <div className="glass-card p-5 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
              <span>⚙</span> Advanced 2D Knowledge Graph View
            </h3>
            <p className="text-xs text-slate-400">Technical force-directed graph view for developer and deep structural inspection.</p>
          </div>

          <button
            onClick={() => setShowAdvancedGraph(!showAdvancedGraph)}
            className="btn-secondary py-1.5 px-4 text-xs font-semibold"
          >
            {showAdvancedGraph ? 'Hide Graph' : 'Show Advanced Graph'}
          </button>
        </div>

        {showAdvancedGraph && (
          <div className="relative rounded-2xl overflow-hidden bg-slate-950/90 border border-slate-900 min-h-[420px] flex items-center justify-center animate-fade-in">
            <ForceGraph2D
              ref={fullGraphRef}
              graphData={fullKnowledgeGraphData}
              nodeId="id"
              nodeLabel={node => `${NODE_TYPE_LABELS[node.type] || node.type}: ${node.label}`}
              nodeColor={node => NODE_COLORS[node.type] || NODE_COLORS.DEFAULT}
              nodeRelSize={6}
              linkColor={() => 'rgba(148, 163, 184, 0.2)'}
              linkWidth={1}
              onNodeClick={(node) => {
                if (node.type === 'PAPER' && node.paper_id && onViewPaper) {
                  onViewPaper(node.paper_id);
                }
              }}
            />
          </div>
        )}
      </div>


      {/* --- CONNECTION MODAL OVERLAY --- */}
      {selectedConnection && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-4 bg-slate-950/85 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="w-full max-w-lg glass-card rounded-3xl p-6 border border-slate-800 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-850 pb-3">
              <h4 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🔗</span> Why Are These Papers Connected?
              </h4>
              <button
                onClick={() => setSelectedConnection(null)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3.5 rounded-2xl bg-indigo-950/30 border border-indigo-900/40 flex items-center justify-between">
                <span className="font-bold text-indigo-300">Semantic Similarity:</span>
                <span className="font-mono font-extrabold text-white text-base">
                  {typeof selectedConnection.similarity_score === 'number'
                    ? (selectedConnection.similarity_score > 1 ? selectedConnection.similarity_score : selectedConnection.similarity_score * 100).toFixed(1)
                    : selectedConnection.similarity_score}%
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Source Paper:</span>
                <p className="font-bold text-slate-100">{selectedConnection.source_title || selectedConnection.source_paper_title}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Target Paper:</span>
                <p className="font-bold text-slate-100">{selectedConnection.target_title || selectedConnection.target_paper_title}</p>
              </div>

              {selectedConnection.shared_concepts && selectedConnection.shared_concepts.length > 0 && (
                <div className="space-y-1 pt-2 border-t border-slate-850">
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Shared Concepts:</span>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {selectedConnection.shared_concepts.map((c, i) => (
                      <span key={i} className="px-2 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setSelectedConnection(null)} className="btn-secondary py-1.5 px-5 text-xs">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OPPORTUNITY EXPLORER MODAL */}
      {explorerDirId && (
        <OpportunityExplorerModal
          directionId={explorerDirId}
          projectId={isProjectScope ? (data?.project?.id || null) : null}
          fallbackDirection={directionsList.find(d => (d.direction_id || d.id) === explorerDirId)}
          onClose={() => setExplorerDirId(null)}
          onViewPaper={onViewPaper}
          onGenerateDraft={(dirId) => {
            setExplorerDirId(null);
            if (onGenerateDraft) onGenerateDraft(dirId);
          }}
          isDrafting={draftingDirId === explorerDirId}
        />
      )}

      {/* OPPORTUNITY COMPARISON MODAL */}
      {showComparisonModal && selectedCompareIds.length > 0 && (
        <OpportunityComparisonModal
          selectedDirections={directionsList.filter(d => selectedCompareIds.includes(d.direction_id || d.id))}
          onClose={() => setShowComparisonModal(false)}
          onSelectExplorer={(dirId) => {
            setShowComparisonModal(false);
            setExplorerDirId(dirId);
          }}
          onGenerateDraft={(dirId) => {
            setShowComparisonModal(false);
            if (onGenerateDraft) onGenerateDraft(dirId);
          }}
        />
      )}

    </div>
  );
}
