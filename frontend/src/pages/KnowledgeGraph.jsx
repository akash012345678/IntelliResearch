import React, { useState, useEffect, useRef, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { apiService } from '../services/api';

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

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [statistics, setStatistics] = useState(null);
  const [topEntities, setTopEntities] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterType, setFilterType] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);

  const fgRef = useRef();

  // Load graph data & top entities
  useEffect(() => {
    fetchKnowledgeGraphData(filterType);
  }, [filterType]);

  const fetchKnowledgeGraphData = async (typeFilter = '') => {
    setLoading(true);
    setError('');
    try {
      const [graphResp, topEntitiesResp] = await Promise.all([
        apiService.getKnowledgeGraph(typeFilter),
        apiService.getTopGraphEntities(5)
      ]);

      const gData = graphResp.data;
      setStatistics(gData.statistics || null);
      setGraphData({
        nodes: gData.nodes || [],
        links: (gData.edges || [])
          .filter(e => e.source && e.target && e.source !== e.target)
          .map(e => ({
            source: e.source,
            target: e.target,
            relation: e.relation
          }))
      });

      setTopEntities(topEntitiesResp.data || null);
    } catch (err) {
      console.error('Failed to load Knowledge Graph:', err);
      setError('Unable to load the research knowledge graph.');
    } finally {
      setLoading(false);
    }
  };

  // Node Inspector helper: find connected edges for selected node
  const selectedNodeConnections = useMemo(() => {
    if (!selectedNode || !graphData.links) return [];
    const nodeId = selectedNode.id;
    return graphData.links.filter(l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      return sourceId === nodeId || targetId === nodeId;
    });
  }, [selectedNode, graphData.links]);

  // Handle node selection
  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 500);
      fgRef.current.zoom(2.5, 500);
    }
  };

  const handleResetZoom = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 20);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight flex items-center gap-2">
            <svg className="w-7 h-7 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Research Knowledge Graph
          </h2>
          <p className="text-sm text-slate-450 mt-1">
            Explore relationships between research papers, algorithms, datasets, methodologies, keywords, and application domains.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl overflow-x-auto custom-scrollbar">
          {[
            { label: 'All', value: '' },
            { label: 'Papers', value: 'PAPER' },
            { label: 'Algorithms', value: 'ALGORITHM' },
            { label: 'Datasets', value: 'DATASET' },
            { label: 'Methodologies', value: 'METHODOLOGY' },
            { label: 'Keywords', value: 'KEYWORD' },
            { label: 'Domains', value: 'DOMAIN' }
          ].map(tab => (
            <button
              key={tab.value}
              onClick={() => setFilterType(tab.value)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-300 ${
                filterType === tab.value
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Glassmorphic Statistics Bar */}
      {statistics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { title: 'Papers', value: statistics.paper_nodes, color: 'text-indigo-400', border: 'border-indigo-500/20' },
            { title: 'Algorithms', value: statistics.algorithm_nodes, color: 'text-emerald-400', border: 'border-emerald-500/20' },
            { title: 'Datasets', value: statistics.dataset_nodes, color: 'text-amber-400', border: 'border-amber-500/20' },
            { title: 'Methodologies', value: statistics.methodology_nodes, color: 'text-rose-400', border: 'border-rose-500/20' },
            { title: 'Keywords', value: statistics.keyword_nodes, color: 'text-sky-400', border: 'border-sky-500/20' },
            { title: 'Domains', value: statistics.domain_nodes, color: 'text-teal-400', border: 'border-teal-500/20' },
            { title: 'Relationships', value: statistics.total_edges, color: 'text-slate-200', border: 'border-slate-700/50' }
          ].map((item, idx) => (
            <div key={idx} className={`glass-card p-3.5 rounded-2xl border ${item.border} flex flex-col justify-between space-y-1`}>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{item.title}</span>
              <span className={`text-xl font-extrabold ${item.color}`}>{item.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main Graph Visualization Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Force Directed Graph Canvas (3 Columns on Large Screens) */}
        <div className="lg:col-span-3 glass-card rounded-3xl p-4 border border-slate-800 shadow-2xl relative flex flex-col min-h-[550px]">
          
          {/* Legend & Controls Overlay */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-800/80 mb-3 z-10">
            {/* Color Legend */}
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {Object.entries(NODE_COLORS).filter(([k]) => k !== 'DEFAULT').map(([type, color]) => (
                <div key={type} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }}></span>
                  <span className="text-slate-300 font-medium text-[11px]">{NODE_TYPE_LABELS[type] || type}</span>
                </div>
              ))}
            </div>

            {/* Zoom Reset Button */}
            <button
              onClick={handleResetZoom}
              className="btn-secondary py-1 text-[11px] px-3 font-semibold flex items-center gap-1"
              title="Reset Zoom & Centering"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-2V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Recenter Graph
            </button>
          </div>

          {/* Graph Loading / Error / Canvas Container */}
          <div className="flex-1 relative rounded-2xl overflow-hidden bg-slate-950/90 border border-slate-900 min-h-[460px] flex items-center justify-center">
            {loading ? (
              <div className="py-20 text-center space-y-3">
                <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-sm font-semibold text-slate-300">Building research knowledge graph...</p>
              </div>
            ) : error ? (
              <div className="py-16 text-center space-y-3 px-4">
                <svg className="w-12 h-12 text-rose-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-sm font-bold text-slate-100">{error}</p>
                <p className="text-xs text-slate-450">Please ensure the backend server is running and research papers are uploaded.</p>
              </div>
            ) : graphData.nodes.length === 0 ? (
              <div className="py-16 text-center space-y-3 px-4">
                <svg className="w-12 h-12 text-slate-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <p className="text-sm font-bold text-slate-200">No research papers are currently available to build the graph.</p>
                <p className="text-xs text-slate-450">Upload PDF manuscripts on the main page to populate the Knowledge Graph.</p>
              </div>
            ) : (
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeId="id"
                nodeLabel={node => `${NODE_TYPE_LABELS[node.type] || node.type}: ${node.label}`}
                nodeColor={node => NODE_COLORS[node.type] || NODE_COLORS.DEFAULT}
                nodeRelSize={6}
                linkColor={() => 'rgba(148, 163, 184, 0.2)'}
                linkWidth={1.5}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleWidth={2}
                onNodeClick={handleNodeClick}
                canvasObject={(node, ctx, globalScale) => {
                  const label = node.label;
                  const fontSize = Math.max(3, 12 / globalScale);
                  const isPaper = node.type === 'PAPER';
                  const radius = isPaper ? 7 : 4;
                  const color = NODE_COLORS[node.type] || NODE_COLORS.DEFAULT;

                  // Node Circle
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                  ctx.fillStyle = color;
                  ctx.fill();

                  // Border stroke
                  ctx.lineWidth = selectedNode?.id === node.id ? 2 : 0.8;
                  ctx.strokeStyle = selectedNode?.id === node.id ? '#ffffff' : 'rgba(255, 255, 255, 0.3)';
                  ctx.stroke();

                  // Text Label (Always drawn when scale is legible or node selected)
                  if (globalScale >= 1.2 || selectedNode?.id === node.id || isPaper) {
                    ctx.font = `${isPaper ? 'bold' : 'normal'} ${fontSize}px sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    ctx.fillStyle = selectedNode?.id === node.id ? '#ffffff' : '#cbd5e1';
                    ctx.fillText(label.length > 25 ? label.slice(0, 22) + '...' : label, node.x, node.y + radius + 2);
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* Side Panel: Selected Node Inspector & Top Entities */}
        <div className="space-y-6">
          
          {/* Selected Node Details Inspector */}
          <div className="glass-card rounded-3xl p-5 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Node Inspector
            </h3>

            {selectedNode ? (
              <div className="space-y-3 bg-slate-950/60 p-4 rounded-2xl border border-slate-850 animate-fade-in">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className="px-2.5 py-0.5 rounded-lg text-[10px] font-extrabold uppercase tracking-wide text-white"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.type] || NODE_COLORS.DEFAULT }}
                  >
                    {NODE_TYPE_LABELS[selectedNode.type] || selectedNode.type}
                  </span>
                  {selectedNode.paper_id && (
                    <span className="text-[10px] font-mono text-slate-400">ID: {selectedNode.paper_id}</span>
                  )}
                </div>

                <h4 className="text-sm font-bold text-slate-100 leading-snug">
                  {selectedNode.label}
                </h4>

                {/* Connections summary */}
                <div className="space-y-2 pt-2 border-t border-slate-850">
                  <span className="text-[11px] font-semibold text-slate-400">
                    Connected Relationships ({selectedNodeConnections.length}):
                  </span>
                  <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-1.5 pr-1">
                    {selectedNodeConnections.map((conn, idx) => {
                      const otherId = (typeof conn.source === 'object' ? conn.source.id : conn.source) === selectedNode.id
                        ? (typeof conn.target === 'object' ? conn.target.label : conn.target)
                        : (typeof conn.source === 'object' ? conn.source.label : conn.source);

                      return (
                        <div key={idx} className="p-2 rounded-xl bg-slate-900/80 border border-slate-850 text-[11px] flex flex-col gap-0.5">
                          <span className="text-indigo-300 font-mono text-[9px] uppercase tracking-wide">{conn.relation}</span>
                          <span className="text-slate-200 font-medium truncate">{otherId}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-2xl bg-slate-950/40 border border-slate-850 text-center text-xs text-slate-450 space-y-1 italic">
                <p>Click any node on the graph canvas to inspect its details and relationships.</p>
              </div>
            )}
          </div>

          {/* Top Shared Entities Panel */}
          {topEntities && (
            <div className="glass-card rounded-3xl p-5 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Top Shared Entities
              </h3>

              {/* Algorithms */}
              {topEntities.algorithms && topEntities.algorithms.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wide">Top Algorithms</span>
                  <div className="space-y-1">
                    {topEntities.algorithms.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-xs bg-slate-950/50 px-3 py-1.5 rounded-xl border border-slate-850">
                        <span className="text-slate-200 font-medium truncate max-w-[170px]">{item.name}</span>
                        <span className="text-[10px] font-mono text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-md font-bold">{item.paper_count} papers</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Methodologies */}
              {topEntities.methodologies && topEntities.methodologies.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wide">Top Methodologies</span>
                  <div className="space-y-1">
                    {topEntities.methodologies.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-xs bg-slate-950/50 px-3 py-1.5 rounded-xl border border-slate-850">
                        <span className="text-slate-200 font-medium truncate max-w-[170px]">{item.name}</span>
                        <span className="text-[10px] font-mono text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded-md font-bold">{item.paper_count} papers</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
