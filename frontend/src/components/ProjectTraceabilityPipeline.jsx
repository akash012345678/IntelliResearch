import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';

export default function ProjectTraceabilityPipeline({
  projectId,
  selectedDirectionId: propDirectionId,
  onSelectDirection,
  onSelectTab,
  onOpenPaper,
  onOpenProposal,
  onOpenPlan,
  onOpenExperiments,
  onOpenResults
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [traceabilityData, setTraceabilityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL'); // ALL, OPPORTUNITIES, PROPOSALS, PLANS, EXPERIMENTS, RESULTS
  const [expandedChainId, setExpandedChainId] = useState(null);

  const activeDirId = propDirectionId || searchParams.get('dir_id');

  useEffect(() => {
    if (projectId) {
      fetchTraceability();
    }
  }, [projectId]);

  useEffect(() => {
    if (traceabilityData?.chains?.length > 0) {
      resolveExpandedChain(traceabilityData.chains, activeDirId);
    }
  }, [traceabilityData, activeDirId]);

  const resolveExpandedChain = (chains, targetDirId) => {
    if (!chains || chains.length === 0) return;
    if (targetDirId) {
      const match = chains.find(
        (c) =>
          c.opportunity?.direction_id === targetDirId ||
          c.chain_id === `chain_${targetDirId}` ||
          c.chain_id === targetDirId
      );
      if (match) {
        setExpandedChainId(match.chain_id);
        return;
      }
    }
    setExpandedChainId(chains[0].chain_id);
  };

  const fetchTraceability = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getProjectTraceability(projectId);
      setTraceabilityData(res.data);
      if (res.data?.chains?.length > 0) {
        resolveExpandedChain(res.data.chains, activeDirId);
      }
    } catch (err) {
      console.error('Failed to load project traceability:', err);
      setError('Unable to load dynamic evidence traceability data.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 rounded-3xl bg-slate-900/60 border border-slate-800 text-center space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-slate-800 text-indigo-400 flex items-center justify-center mx-auto text-lg">
          🔗
        </div>
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">
          Tracing End-to-End Evidence Lineage...
        </h4>
        <p className="text-[11px] text-slate-400">
          Synthesizing papers, gaps, opportunities, plans, experiments, results, and proposals.
        </p>
      </div>
    );
  }

  if (error || !traceabilityData) {
    return (
      <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto text-lg">
          ⚠️
        </div>
        <h4 className="text-xs font-bold text-slate-200 uppercase">{error || 'No Traceability Data Available'}</h4>
        <button
          onClick={fetchTraceability}
          className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition"
        >
          Retry Loading Traceability
        </button>
      </div>
    );
  }

  const { summary, chains } = traceabilityData;

  // Filter chains based on active filter
  const filteredChains = (chains || []).filter((chain) => {
    if (activeFilter === 'ALL') return true;
    if (activeFilter === 'PROPOSALS') return chain.proposal?.is_created;
    if (activeFilter === 'OPPORTUNITIES') return chain.opportunity?.direction_id;
    if (activeFilter === 'PLANS') return chain.plan?.status === 'SAVED';
    if (activeFilter === 'EXPERIMENTS') return chain.experiments?.length > 0;
    if (activeFilter === 'RESULTS') return chain.results?.results_recorded;
    return true;
  });

  const getStageBadgeClass = (statusStr) => {
    if (
      statusStr === 'AVAILABLE' ||
      statusStr === 'SAVED' ||
      statusStr === 'COMPLETED' ||
      statusStr === 'ALL_RESULTS_RECORDED' ||
      statusStr === 'READY_FOR_EXPORT'
    ) {
      return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    }
    if (statusStr === 'PARTIAL_RESULTS' || statusStr === 'COMPLETED_NO_RESULTS') {
      return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
    }
    if (statusStr === 'DRAFT' || statusStr === 'PLANNED' || statusStr === 'IDENTIFIED') {
      return 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30';
    }
    return 'bg-slate-800 text-slate-400 border-slate-700';
  };

  const getResultsBadgeLabel = (statusStr) => {
    if (statusStr === 'ALL_RESULTS_RECORDED') return '✓ All Recorded';
    if (statusStr === 'PARTIAL_RESULTS') return '⚠ Partial Results';
    if (statusStr === 'COMPLETED_NO_RESULTS') return '⚠ Completed (No Results)';
    return '⚠ Pending Results';
  };

  const handleChainHeaderClick = (chain) => {
    const chainDirId = chain.opportunity?.direction_id;
    const isCurrentlyExpanded = expandedChainId === chain.chain_id;

    if (isCurrentlyExpanded && activeDirId === chainDirId) {
      setExpandedChainId(null);
    } else {
      setExpandedChainId(chain.chain_id);
      if (chainDirId) {
        if (onSelectDirection) {
          onSelectDirection(chainDirId);
        } else {
          setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            next.set('dir_id', chainDirId);
            return next;
          });
        }
      }
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* HEADER & LIFECYCLE SUMMARY RIBBON */}
      <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
          <div className="space-y-1">
            <span className="text-[10px] font-extrabold text-indigo-400 uppercase tracking-widest flex items-center gap-1.5">
              <span>🔗</span> EVIDENCE PROVENANCE & LIFECYCLE TRACEABILITY
            </span>
            <h3 className="text-base font-bold text-white">
              End-to-End Research Lineage Matrix
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic mapping from literature evidence → gaps → opportunities → methodology plans → experiments → empirical results → proposal versions → thesis report.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={fetchTraceability}
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center gap-1.5"
            >
              <span>🔄</span> Refresh Lineage
            </button>
          </div>
        </div>

        {/* STAGE STATUS SUMMARY PIPELINE */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 pt-1 text-center text-xs">
          <div onClick={() => onSelectTab && onSelectTab('papers')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-indigo-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">1. Papers</span>
            <div className="font-extrabold text-white text-sm">{summary.total_papers}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.papers)}`}>
              {summary.stage_statuses.papers === 'AVAILABLE' ? '✓ Available' : '⚠ Missing'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('gaps')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-amber-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">2. Gaps</span>
            <div className="font-extrabold text-white text-sm">{summary.total_gaps}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.gaps)}`}>
              {summary.stage_statuses.gaps === 'AVAILABLE' ? '✓ Identified' : '⚠ None'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('directions')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-purple-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">3. Directions</span>
            <div className="font-extrabold text-white text-sm">{summary.total_opportunities}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.opportunities)}`}>
              {summary.stage_statuses.opportunities === 'AVAILABLE' ? '✓ Available' : '⚠ None'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('plan')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-indigo-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">4. Plans</span>
            <div className="font-extrabold text-white text-sm">{summary.saved_plans}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.plans)}`}>
              {summary.stage_statuses.plans === 'SAVED' ? '✓ Saved' : '⚠ Not Created'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('experiments')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-purple-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">5. Experiments</span>
            <div className="font-extrabold text-white text-sm">{summary.planned_experiments}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.experiments)}`}>
              {summary.completed_experiments > 0 ? `✓ ${summary.completed_experiments}/${summary.planned_experiments} Done` : '⚠ Planned'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('results-analysis')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-emerald-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">6. Results</span>
            <div className="font-extrabold text-white text-sm">{summary.recorded_result_runs} runs</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.results)}`}>
              {getResultsBadgeLabel(summary.stage_statuses.results)}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('proposals')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-amber-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">7. Proposals</span>
            <div className="font-extrabold text-white text-sm">{summary.created_proposals}</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.proposals)}`}>
              {summary.stage_statuses.proposals === 'DRAFT' || summary.stage_statuses.proposals === 'COMPLETED' ? '✓ Drafted' : '⚠ None'}
            </span>
          </div>

          <div onClick={() => onSelectTab && onSelectTab('report')} className="cursor-pointer p-2.5 rounded-2xl bg-slate-950/80 border border-slate-850 hover:border-rose-500/40 transition space-y-1">
            <span className="text-[9px] font-bold uppercase text-slate-400 block">8. Report</span>
            <div className="font-extrabold text-white text-sm">PDF</div>
            <span className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold border block truncate ${getStageBadgeClass(summary.stage_statuses.report)}`}>
              {summary.stage_statuses.report === 'READY_FOR_EXPORT' ? '✓ Ready' : '⚠ None'}
            </span>
          </div>
        </div>
      </div>

      {/* FILTER TABS & STAGE VIEWER */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {[
              { key: 'ALL', label: `ALL CHAINS (${chains.length})`, emoji: '🔮' },
              { key: 'PROPOSALS', label: `PROPOSALS (${summary.created_proposals})`, emoji: '📑' },
              { key: 'OPPORTUNITIES', label: `OPPORTUNITIES (${summary.total_opportunities})`, emoji: '🎯' },
              { key: 'PLANS', label: `PLANS (${summary.saved_plans})`, emoji: '🧪' },
              { key: 'EXPERIMENTS', label: `EXPERIMENTS (${summary.planned_experiments})`, emoji: '⚡' },
              { key: 'RESULTS', label: `RESULTS (${summary.recorded_result_runs})`, emoji: '📊' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveFilter(tab.key)}
                className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold transition flex items-center gap-1.5 whitespace-nowrap ${
                  activeFilter === tab.key
                    ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>{tab.emoji}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* CHAIN CARDS LIST */}
        {filteredChains.length === 0 ? (
          <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto text-xl">
              🔍
            </div>
            <h4 className="text-sm font-bold text-slate-200 uppercase">NO MATCHING TRACEABILITY CHAINS</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              No evidence traceability chains match the selected filter category ({activeFilter}).
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredChains.map((chain) => {
              const chainDirId = chain.opportunity?.direction_id;
              const isSelected = Boolean(activeDirId && (chainDirId === activeDirId || chain.chain_id === `chain_${activeDirId}`));
              const isExpanded = expandedChainId === chain.chain_id || isSelected;
              const hasProposal = chain.proposal?.is_created;
              const hasPlan = chain.plan?.status === 'SAVED';
              const hasResults = chain.results?.results_recorded;

              return (
                <div
                  key={chain.chain_id}
                  className={`rounded-3xl border transition-all duration-300 overflow-hidden ${
                    isSelected
                      ? 'bg-slate-900/95 border-indigo-500 shadow-2xl ring-2 ring-indigo-500/40'
                      : isExpanded
                      ? 'bg-slate-900/90 border-indigo-500/40 shadow-xl'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {/* CARD HEADER */}
                  <div
                    onClick={() => handleChainHeaderClick(chain)}
                    className="p-5 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/60 hover:bg-slate-850/40 transition"
                  >
                    <div className="space-y-1.5 max-w-2xl">
                      <div className="flex items-center gap-2 flex-wrap text-[10px]">
                        {isSelected && (
                          <span className="px-2.5 py-0.5 rounded-full bg-indigo-500 text-slate-950 font-black uppercase tracking-wider shadow-md">
                            ★ ACTIVE SELECTION
                          </span>
                        )}

                        <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30 font-mono font-bold">
                          {chainDirId || 'CHAIN'}
                        </span>

                        <span className={`px-2.5 py-0.5 rounded-full font-bold uppercase border ${
                          chain.opportunity?.confidence === 'High' || chain.opportunity?.confidence === 'HIGH'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        }`}>
                          Confidence: {chain.opportunity?.confidence || 'High'}
                        </span>

                        <span className={`px-2.5 py-0.5 rounded-full font-extrabold uppercase border ${
                          hasProposal
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {hasProposal ? `Proposal: ${chain.proposal.status}` : 'Proposal Not Created Yet'}
                        </span>

                        <span className={`px-2.5 py-0.5 rounded-full font-bold border ${getStageBadgeClass(chain.plan?.status)}`}>
                          Plan: {chain.plan?.status}
                        </span>
                      </div>

                      <h4 className="text-base font-bold text-white leading-snug">
                        {chain.opportunity?.title || chain.proposal?.title}
                      </h4>

                      <p className="text-xs text-slate-400 line-clamp-1">
                        {chain.gap?.title}: {chain.gap?.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className={`w-2 h-2 rounded-full ${hasResults ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
                        <span className="text-slate-300 font-semibold">{getResultsBadgeLabel(chain.results?.completion_status)}</span>
                      </div>

                      <span className="text-slate-400 text-sm font-bold">
                        {isExpanded ? '▲' : '▼'}
                      </span>
                    </div>
                  </div>

                  {/* EXPANDABLE LINEAGE BODY */}
                  {isExpanded && (
                    <div className="p-6 space-y-6 bg-slate-950/40 border-t border-slate-850 animate-fade-in text-xs">
                      
                      {/* PROVENANCE STEP 1: SUPPORTING PAPERS & CONCEPTS */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>📚</span> 1. Supporting Papers ({chain.papers.length})
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono font-bold">
                              [RECORDED_EVIDENCE]
                            </span>
                          </div>

                          <div className="space-y-2">
                            {chain.papers.map((paper) => (
                              <div
                                key={paper.paper_id}
                                onClick={() => onOpenPaper && onOpenPaper(paper.paper_id)}
                                className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-850 hover:border-indigo-500/40 hover:bg-slate-950 cursor-pointer transition space-y-1"
                              >
                                <div className="font-bold text-indigo-300 flex items-center justify-between">
                                  <span className="truncate max-w-[80%]">Paper #{paper.paper_id}: {paper.title}</span>
                                  <span className="text-[10px] text-slate-500">View →</span>
                                </div>
                                <div className="text-[10px] text-slate-400">
                                  {paper.authors ? `${paper.authors} (${paper.year || '2024'})` : 'Indexed Project Collection Evidence'}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>🧩</span> 2. Supporting Concepts ({chain.concepts.length})
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono font-bold">
                              [RECORDED_EVIDENCE]
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {chain.concepts.map((concept, cIdx) => (
                              <span
                                key={cIdx}
                                className="px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-850 text-indigo-300 font-medium text-[11px]"
                              >
                                {concept.name} <span className="text-[9px] text-slate-500">({concept.type})</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* PROVENANCE STEP 2: RESEARCH GAP & OPPORTUNITY */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>⚠️</span> 3. Parent Research Gap
                            </span>
                            <button
                              onClick={() => onSelectTab && onSelectTab('gaps')}
                              className="text-amber-400 hover:underline text-[10px] font-bold"
                            >
                              View Gaps →
                            </button>
                          </div>

                          <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-bold">
                                {chain.gap?.gap_id}
                              </span>
                              <span className="font-bold text-white text-xs">{chain.gap?.title}</span>
                            </div>
                            <p className="text-slate-300 text-[11px] leading-relaxed">
                              {chain.gap?.description}
                            </p>
                            <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-850">
                              Evidence Type: <span className="text-slate-200 font-semibold">{chain.gap?.relationship_evidence}</span> • Gap Score: <span className="text-amber-300 font-bold">{chain.gap?.gap_score}</span>
                            </div>
                          </div>
                        </div>

                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>🎯</span> 4. Research Opportunity
                            </span>
                            <button
                              onClick={() => onSelectTab && onSelectTab('directions', chain.opportunity?.direction_id)}
                              className="text-purple-400 hover:underline text-[10px] font-bold"
                            >
                              Select Opportunity →
                            </button>
                          </div>

                          <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[10px] font-mono font-bold">
                                {chain.opportunity?.direction_id}
                              </span>
                              <span className="font-bold text-white text-xs">{chain.opportunity?.title}</span>
                            </div>
                            <p className="text-slate-300 text-[11px] leading-relaxed">
                              {chain.opportunity?.description}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* PROVENANCE STEP 3: METHODOLOGY PLAN & EXPERIMENTS */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>🧪</span> 5. Methodology Plan
                            </span>
                            <button
                              onClick={() => onOpenPlan && onOpenPlan(chain.opportunity?.direction_id)}
                              className="px-2.5 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px]"
                            >
                              {hasPlan ? 'Open Saved Plan →' : 'Create Plan →'}
                            </button>
                          </div>

                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getStageBadgeClass(chain.plan?.status)}`}>
                                Status: {chain.plan?.status}
                              </span>
                              <span className="text-slate-400 text-[10px] font-mono font-bold">
                                Experiments Configured: {chain.plan?.experiment_count}
                              </span>
                            </div>

                            {hasPlan ? (
                              <div className="space-y-1.5 text-[11px] text-slate-300">
                                <div><b className="text-slate-400">Title:</b> {chain.plan?.methodology_title}</div>
                                <div><b className="text-slate-400">Baseline Methods:</b> {chain.plan?.baseline_methods?.join(', ') || 'Standard Baselines'}</div>
                                <div><b className="text-slate-400">Proposed Architecture:</b> <span className="text-indigo-300 font-bold">{chain.plan?.proposed_architecture}</span></div>
                              </div>
                            ) : (
                              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-850 text-slate-400 text-[11px] italic">
                                Methodology plan record is NOT_CREATED in persistent storage for this opportunity yet. [MISSING]
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>⚡</span> 6. Planned Experiments ({chain.experiments.length})
                            </span>
                            <button
                              onClick={() => onOpenExperiments && onOpenExperiments(chain.opportunity?.direction_id)}
                              className="text-purple-400 hover:underline text-[10px] font-bold"
                            >
                              Open Experiments →
                            </button>
                          </div>

                          {chain.experiments.length === 0 ? (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-850 text-slate-400 text-[11px] italic">
                              No experiments planned yet for this direction. Import methodology plan to create experiments.
                            </div>
                          ) : (
                            <div className="space-y-2">
                              {chain.experiments.map((exp) => (
                                <div key={exp.experiment_id} className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-850 space-y-1">
                                  <div className="font-bold text-white flex items-center justify-between">
                                    <span>#{exp.experiment_id}: {exp.title}</span>
                                    <span className={`px-2 py-0.2 rounded-full text-[9px] font-bold border ${getStageBadgeClass(exp.result_status)}`}>
                                      {exp.result_status}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-slate-400 flex items-center justify-between">
                                    <span>Status: <b className="text-slate-300">{exp.execution_status}</b></span>
                                    <span>Metrics: {exp.configured_metrics?.join(', ')}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* PROVENANCE STEP 4: EXPERIMENTAL RESULTS & PROPOSAL VERSIONS */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>📊</span> 7. Empirical Results State
                            </span>
                            <button
                              onClick={() => onOpenResults && onOpenResults(chain.opportunity?.direction_id)}
                              className="text-emerald-400 hover:underline text-[10px] font-bold"
                            >
                              Results Analysis →
                            </button>
                          </div>

                          <div className="space-y-2">
                            <div className="flex items-center gap-2 flex-wrap text-[10px]">
                              <span className={`px-2.5 py-0.5 rounded-full font-bold border ${getStageBadgeClass(chain.results?.completion_status)}`}>
                                Status: {getResultsBadgeLabel(chain.results?.completion_status)}
                              </span>
                              <span className="text-slate-400 font-mono font-bold">
                                Runs: {chain.results?.run_count} • Metric Rows: {chain.results?.result_row_count}
                              </span>
                            </div>

                            <p className="p-3 rounded-xl bg-slate-950/80 border border-slate-850 text-slate-300 text-[11px] leading-relaxed">
                              {chain.results?.notice}
                            </p>
                          </div>
                        </div>

                        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                              <span>📑</span> 8. Proposal & Historical Versions
                            </span>
                            {hasProposal && (
                              <button
                                onClick={() => onOpenProposal && onOpenProposal(chain.proposal?.proposal_id)}
                                className="px-3 py-1 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-[10px] shadow"
                              >
                                Open Proposal →
                              </button>
                            )}
                          </div>

                          <div className="space-y-2">
                            <div className="font-bold text-white text-xs">
                              {chain.proposal?.title}
                            </div>

                            {hasProposal && chain.versions?.length > 0 ? (
                              <div className="space-y-1.5">
                                <span className="text-[10px] text-slate-400 font-bold uppercase block">Version History ({chain.versions.length}):</span>
                                <div className="flex flex-wrap gap-1.5">
                                  {chain.versions.map((v) => (
                                    <button
                                      key={v.version_id}
                                      onClick={() => onOpenProposal && onOpenProposal(chain.proposal?.proposal_id, v.version_number)}
                                      className={`px-2.5 py-1 rounded-xl text-[10px] font-bold border transition ${
                                        v.is_current
                                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 ring-1 ring-amber-500/30'
                                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                                      }`}
                                    >
                                      v{v.version_number} ({v.source_type}) {v.is_current ? '• Current' : ''}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-850 text-slate-400 text-[11px] italic">
                                Proposal has not been drafted for this research direction yet. Draft a proposal from the Directions tab.
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* PROVENANCE STEP 5: FINAL REPORT STATUS */}
                      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="space-y-1">
                          <span className="font-extrabold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                            <span>📄</span> 9. Final Research Report Export
                          </span>
                          <p className="text-[11px] text-slate-400">
                            Academic thesis report PDF contains 8-chapter university structure, dotted-leader TOC, and verified evidence tags.
                          </p>
                        </div>

                        <button
                          onClick={() => onSelectTab && onSelectTab('report')}
                          className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow border border-rose-500/30 transition shrink-0"
                        >
                          Generate & Export PDF Report →
                        </button>
                      </div>

                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
