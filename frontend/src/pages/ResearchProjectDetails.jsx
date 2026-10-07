import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';
import PaperViewModal from '../components/PaperViewModal';
import ProposalWorkspaceModal from '../components/ProposalWorkspaceModal';
import ProjectPaperSelector from '../components/ProjectPaperSelector';
import ProjectResearchReportModal from '../components/ProjectResearchReportModal';
import ResearchMap from '../components/ResearchMap';
import ResearchMethodologyPlannerModal from '../components/ResearchMethodologyPlannerModal';
import ResearchExperimentWorkspace from '../components/ResearchExperimentWorkspace';
import ResearchResultsAnalysis from '../components/ResearchResultsAnalysis';
import ResearchJourney from '../components/ResearchJourney';
import AcademicManuscriptWorkspace from '../components/AcademicManuscriptWorkspace';
import ProjectTraceabilityPipeline from '../components/ProjectTraceabilityPipeline';
import ErrorBoundary from '../components/ErrorBoundary';
import { filterQualifiedGaps } from '../utils/researchGapUtils';
import { normalizeProposal } from '../utils/proposalNormalizer';

export default function ResearchProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Active Workspace Tab: 'overview' | 'journey' | 'map' | 'papers' | 'connections' | 'concepts' | 'gaps' | 'directions' | 'plan' | 'experiments' | 'results-analysis' | 'proposals' | 'manuscript' | 'traceability' | 'report'
  const activeTab = searchParams.get('tab') || 'overview';

  // Basic Project Data & Loading State
  const [project, setProject] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [savedDirections, setSavedDirections] = useState([]);
  const [journeySummary, setJourneySummary] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [planningDirId, setPlanningDirId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [isIntelligenceLoading, setIsIntelligenceLoading] = useState(true);
  const [intelligenceError, setIntelligenceError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);

  // Add Paper Modal State
  const [isAddPaperOpen, setIsAddPaperOpen] = useState(false);

  // Viewing Paper / Proposal State
  const [viewingPaperId, setViewingPaperId] = useState(null);
  const [activeProposalData, setActiveProposalData] = useState(null);
  const [selectedProposalDbId, setSelectedProposalDbId] = useState(null);
  const [isProposalOpen, setIsProposalOpen] = useState(false);

  // Research Report Modal State
  const [isReportOpen, setIsReportOpen] = useState(false);

  // Manual Research Idea State
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [manualTitleInput, setManualTitleInput] = useState('');
  const [manualDescInput, setManualDescInput] = useState('');
  const [creatingManual, setCreatingManual] = useState(false);

  // Filter & Search states inside tabs
  const [paperSearchQuery, setPaperSearchQuery] = useState('');
  const [conceptCategoryTab, setConceptCategoryTab] = useState('algorithms');
  const [expandedGapId, setExpandedGapId] = useState(null);
  const [draftingDirectionId, setDraftingDirectionId] = useState(null);
  const [savingDirectionId, setSavingDirectionId] = useState(null);
  const [selectedOpportunityDirId, setSelectedOpportunityDirId] = useState(() => searchParams.get('dir_id') || null);

  useEffect(() => {
    try {
      const cached = sessionStorage.getItem(`intelliresearch_intel_${projectId}`);
      if (cached) {
        setIntelligence(JSON.parse(cached));
        setIsIntelligenceLoading(false);
      }
    } catch (e) {}
    fetchProjectData();
  }, [projectId]);

  useEffect(() => {
    if (activeTab === 'report' && !reportData && projectId) {
      fetchReportData();
    }
  }, [activeTab, projectId]);

  // Derived Intelligence Data
  const summary = intelligence?.collection_summary;
  const papers = intelligence?.paper_landscape || [];
  const sharedConcepts = intelligence?.shared_concepts || { algorithms: [], datasets: [], methodologies: [], domains: [], keywords: [] };
  const relationships = intelligence?.paper_relationships || [];
  const rawGaps = intelligence?.research_gaps || intelligence?.gaps || [];
  const gaps = useMemo(() => filterQualifiedGaps(rawGaps), [rawGaps]);
  const candidateDirections = intelligence?.candidate_research_directions || [];
  const traceability = intelligence?.proposal_traceability || [];
  const insightSummary = intelligence?.insight_summary || 'No project synthesis available.';

  // Eligible opportunities for methodology planning
  const eligibleOpportunities = useMemo(() => {
    if (!candidateDirections || !Array.isArray(candidateDirections)) return [];
    return candidateDirections.filter(opp => {
      const classification = opp.evidence?.evidence_classification || opp.evidence_classification || '';
      if (classification === 'UNDERREPRESENTATION_ONLY' || classification === 'INSUFFICIENT_EVIDENCE') {
        return false;
      }
      return true;
    });
  }, [candidateDirections]);

  useEffect(() => {
    const dirParam = searchParams.get('dir_id');
    if (dirParam && dirParam !== selectedOpportunityDirId) {
      setSelectedOpportunityDirId(dirParam);
    } else if (!dirParam && eligibleOpportunities.length === 1 && !selectedOpportunityDirId) {
      setSelectedOpportunityDirId(eligibleOpportunities[0].direction_id || eligibleOpportunities[0].id);
    }
  }, [searchParams, eligibleOpportunities]);

  const activePlanDirId = useMemo(() => {
    const dirParam = searchParams.get('dir_id');
    if (dirParam) return dirParam;
    if (selectedOpportunityDirId) return selectedOpportunityDirId;
    if (savedDirections && savedDirections.length > 0) {
      return savedDirections[0].source_direction_id || 'dir_1';
    }
    if (eligibleOpportunities.length > 0) return eligibleOpportunities[0].direction_id || eligibleOpportunities[0].id;
    return 'dir_1';
  }, [searchParams, selectedOpportunityDirId, savedDirections, eligibleOpportunities]);


  // Format metric display values: fallback to project metadata or '—' while loading
  const formatMetric = (val, fallback = null) => {
    if (val !== null && val !== undefined) return val;
    if (fallback !== null && fallback !== undefined) return fallback;
    if (isIntelligenceLoading || intelligenceError) return '—';
    return 0;
  };

  const uniquePaperRelationships = useMemo(() => {
    if (!relationships || !Array.isArray(relationships)) return [];
    const seen = new Set();
    const result = [];
    for (const r of relationships) {
      const srcId = r.source_paper_id || r.source_id;
      const tgtId = r.target_paper_id || r.target_id;
      if (!srcId || !tgtId || srcId === tgtId) continue;
      const lowId = Math.min(srcId, tgtId);
      const highId = Math.max(srcId, tgtId);
      const pairKey = `${lowId}-${highId}`;
      if (seen.has(pairKey)) continue;
      seen.add(pairKey);
      result.push(r);
    }
    return result;
  }, [relationships]);

  const fetchProjectData = async (opts = {}) => {
    const isRefresh = opts.refresh || false;
    if (isRefresh) {
      try {
        sessionStorage.removeItem(`intelliresearch_intel_${projectId}`);
      } catch (e) {}
      setAnalyzing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    setIntelligenceError(null);

    try {
      // Step 1: Fetch core project metadata immediately so page header & controls render instantly
      const projRes = await apiService.getProject(projectId);
      setProject(projRes.data);
      if (projRes.data?.proposals && Array.isArray(projRes.data.proposals)) {
        setProposals(projRes.data.proposals.map(normalizeProposal));
      }
      if (projRes.data?.saved_directions && Array.isArray(projRes.data.saved_directions)) {
        setSavedDirections(projRes.data.saved_directions);
      }
      setLoading(false);

      // Step 2: Fetch intelligence & workspace data non-blockingly using Promise.allSettled
      const intelPromise = isRefresh
        ? apiService.reindexProject(projectId)
        : apiService.getProjectResearchIntelligence(projectId);

      const [intelRes, propRes, dirRes, jnRes] = await Promise.allSettled([
        intelPromise,
        apiService.getProjectProposals(projectId),
        apiService.getProjectDirections(projectId),
        apiService.getProjectResearchJourney(projectId),
      ]);

      if (intelRes.status === 'fulfilled') {
        setIntelligence(intelRes.value.data);
        setIsIntelligenceLoading(false);
        try {
          sessionStorage.setItem(`intelliresearch_intel_${projectId}`, JSON.stringify(intelRes.value.data));
        } catch (e) {}
      } else {
        console.error('Failed to load project research intelligence:', intelRes.reason);
        setIntelligenceError('Unable to load project intelligence.');
        setIsIntelligenceLoading(false);
      }

      if (propRes.status === 'fulfilled') setProposals((propRes.value.data || []).map(normalizeProposal));
      if (dirRes.status === 'fulfilled') setSavedDirections(dirRes.value.data || []);
      if (jnRes.status === 'fulfilled') setJourneySummary(jnRes.value.data);
    } catch (err) {
      console.error('Failed to load project workspace data:', err);
      setError('Unable to analyze this research project collection.');
    } finally {
      setLoading(false);
      setIsIntelligenceLoading(false);
      setAnalyzing(false);
    }
  };

  const handleRefreshAnalysis = () => {
    fetchProjectData({ refresh: true });
  };

  const fetchReportData = async () => {
    setReportLoading(true);
    try {
      const res = await apiService.getProjectResearchReport(projectId);
      setReportData(res.data);
    } catch (err) {
      console.error('Failed to fetch research report:', err);
    } finally {
      setReportLoading(false);
    }
  };

  const handleTabChange = (tabKey, optionalDirId = null) => {
    const params = { tab: tabKey };
    const currentDir = optionalDirId || searchParams.get('dir_id') || selectedOpportunityDirId;
    if (currentDir) {
      params.dir_id = currentDir;
      setSelectedOpportunityDirId(currentDir);
    }
    setSearchParams(params);
  };


  const handleRemovePaper = async (paperId) => {
    if (!window.confirm('Remove this paper from the project? (The paper remains 100% intact in your global paper library)')) return;
    try {
      await apiService.removePaperFromProject(projectId, paperId);
      fetchProjectData();
    } catch (err) {
      console.error('Failed to remove paper:', err);
      alert('Failed to remove paper assignment.');
    }
  };

  const handleDeleteProject = async () => {
    if (!window.confirm(`Delete research project "${project.name}"? Project links, saved directions, and proposals will be removed. Your paper library remains 100% untouched.`)) return;
    try {
      await apiService.deleteProject(projectId);
      navigate('/research-projects');
    } catch (err) {
      console.error('Failed to delete project:', err);
      alert('Error deleting project.');
    }
  };

  const handleToggleArchiveStatus = async () => {
    const newStatus = project.status === 'ARCHIVED' ? 'ACTIVE' : 'ARCHIVED';
    try {
      await apiService.updateProject(projectId, { status: newStatus });
      fetchProjectData();
    } catch (err) {
      console.error('Failed to update project status:', err);
    }
  };

  const handleSaveDirection = async (direction) => {
    setSavingDirectionId(direction.direction_id);
    try {
      await apiService.saveDirection(projectId, {
        direction_id: direction.direction_id,
        title: direction.title,
        description: direction.description,
        confidence: direction.confidence || 'HIGH',
        supporting_papers: direction.supporting_papers || [],
        supporting_concepts: direction.supporting_concepts || [],
        evidence: direction.evidence || {},
        disclaimer: direction.disclaimer || '',
      });
      fetchProjectData();
      alert('Research Direction saved to project workspace!');
    } catch (err) {
      console.error('Failed to save research direction:', err);
      alert('Could not save research direction.');
    } finally {
      setSavingDirectionId(null);
    }
  };

  const handleDeleteSavedDirection = async (directionId) => {
    if (!window.confirm('Delete this saved research direction snapshot?')) return;
    try {
      await apiService.deleteDirection(projectId, directionId);
      fetchProjectData();
    } catch (err) {
      console.error('Failed to delete saved direction:', err);
    }
  };

  const handleOpenSavedProposal = async (proposalId) => {
    try {
      const res = await apiService.getProposal(proposalId);
      setSelectedProposalDbId(proposalId);
      setActiveProposalData(res.data.current_version.proposal_data);
      setIsProposalOpen(true);
    } catch (err) {
      console.error('Failed to load saved proposal:', err);
      alert('Error loading proposal content.');
    }
  };

  const handleDeleteProposal = async (proposalId) => {
    if (!window.confirm('Delete this research proposal and all its version entries?')) return;
    try {
      await apiService.deleteProposal(proposalId);
      fetchProjectData();
    } catch (err) {
      console.error('Failed to delete proposal:', err);
      alert('Could not delete research proposal.');
    }
  };

  const handleDraftProposalFromDirection = async (directionOrId) => {
    const dirId = typeof directionOrId === 'string' ? directionOrId : (directionOrId.direction_id || directionOrId.id);
    setDraftingDirectionId(dirId);
    try {
      const pIdInt = parseInt(projectId, 10);
      const payload = typeof directionOrId === 'object'
        ? {
            direction_id: directionOrId.direction_id || directionOrId.id,
            project_id: pIdInt,
            opportunity_family_id: directionOrId.opportunity_family_id || directionOrId.gap_relationship_key,
            title: directionOrId.title,
            research_question: directionOrId.research_question,
            supporting_papers: directionOrId.supporting_papers
          }
        : {
            direction_id: dirId,
            project_id: pIdInt
          };
      const draftRes = await apiService.generateProposalDraft(payload);
      const proposalObj = draftRes.data.proposal || draftRes.data;
      const dbId = draftRes.data.id || draftRes.data.proposal_db_id || null;
      setActiveProposalData(proposalObj);
      setSelectedProposalDbId(dbId);
      setIsProposalOpen(true);
    } catch (err) {
      console.error('Failed to synthesize proposal draft:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to synthesize proposal draft. Please try again.';
      alert(`Proposal Synthesis Error: ${msg}`);
    } finally {
      setDraftingDirectionId(null);
    }
  };

  const handleCreateManualProposal = async (e) => {
    e.preventDefault();
    if (!manualTitleInput.trim()) {
      alert('Please enter a title for your manual research idea.');
      return;
    }
    setCreatingManual(true);
    try {
      const draftRes = await apiService.generateProposalDraft({
        is_manual_idea: true,
        manual_title: manualTitleInput.trim(),
        manual_description: manualDescInput.trim(),
        project_id: parseInt(projectId, 10)
      });
      setActiveProposalData(draftRes.data.proposal || draftRes.data);
      setSelectedProposalDbId(null);
      setIsProposalOpen(true);
      setIsManualModalOpen(false);
      setManualTitleInput('');
      setManualDescInput('');
    } catch (err) {
      console.error('Failed to create manual proposal:', err);
      alert('Failed to create manual proposal.');
    } finally {
      setCreatingManual(false);
    }
  };

  const handleReportExport = async (format) => {
    try {
      setExporting(true);
      const response = await apiService.exportProjectResearchReport(projectId, format);
      if (format === 'json') {
        const jsonStr = JSON.stringify(response.data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        downloadBlob(blob, `Project_${projectId}_Research_Report.json`);
      } else {
        const mimeType = format === 'pdf' ? 'application/pdf' : 'text/markdown';
        const ext = format === 'pdf' ? 'pdf' : 'md';
        const blob = new Blob([response.data], { type: mimeType });
        downloadBlob(blob, `Project_${projectId}_Research_Report.${ext}`);
      }
    } catch (err) {
      console.error(`Export failed for format ${format}:`, err);
      alert(`Export failed for ${format.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-bold text-slate-300 animate-pulse">Loading project research workspace...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="p-8 rounded-3xl bg-slate-900 border border-rose-500/30 text-rose-300 space-y-3">
          <h3 className="text-lg font-bold">Unable to Load Research Project</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">{error || 'Project not found.'}</p>
          <button onClick={fetchProjectData} className="btn-primary text-xs py-2 px-5 font-bold">
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  const filteredPapers = papers.filter((p) => {
    if (!paperSearchQuery.trim()) return true;
    const q = paperSearchQuery.toLowerCase();
    return (
      (p.title && p.title.toLowerCase().includes(q)) ||
      (p.abstract && p.abstract.toLowerCase().includes(q)) ||
      (p.keywords && p.keywords.some((k) => k.toLowerCase().includes(q))) ||
      (p.algorithms && p.algorithms.some((a) => a.toLowerCase().includes(q))) ||
      (p.datasets && p.datasets.some((d) => d.toLowerCase().includes(q)))
    );
  });

  // Calculate current research stage (1 to 4)
  const currentStageNumber = 
    ['proposals', 'report', 'traceability', 'manuscript', 'academic-paper'].includes(activeTab) ? 4 :
    ['plan', 'experiments', 'results-analysis'].includes(activeTab) ? 3 :
    ['gaps', 'directions', 'opportunities'].includes(activeTab) ? 2 :
    ['papers', 'concepts', 'map', 'journey', 'connections'].includes(activeTab) ? 1 : 1;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16 animate-fade-in text-slate-200">
      
      {/* 1. BREADCRUMB */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-slate-400">
        <Link to="/research-projects" className="hover:text-indigo-400 font-medium transition-colors">
          Research Projects
        </Link>
        <span className="text-slate-600">/</span>
        <span className="text-slate-200 font-semibold truncate max-w-xs">{project.name}</span>
      </nav>

      {/* 2. PROJECT HEADER CARD */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-3 max-w-3xl">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{project.name}</h1>
            <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider border ${
              project.status === 'ARCHIVED' 
                ? 'bg-slate-800 text-slate-400 border-slate-700' 
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}>
              ● {project.status}
            </span>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed">
            {project.description || 'Academic research project scope and literature analysis workspace.'}
          </p>
        </div>

        {/* HEADER ACTIONS */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            onClick={() => setIsAddPaperOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5"
          >
            <span>+</span> Add Research Papers
          </button>
          
          <button
            onClick={() => setIsReportOpen(true)}
            className="px-4 py-2.5 rounded-xl border border-emerald-500/40 hover:bg-emerald-500/10 text-emerald-300 font-bold text-xs transition-all flex items-center gap-1.5"
          >
            <span>📊</span> Generate Research Report
          </button>

          <button
            onClick={handleRefreshAnalysis}
            disabled={analyzing}
            className="px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 font-medium text-xs transition-all disabled:opacity-50 flex items-center gap-1.5"
            title="Refresh Analysis"
          >
            <span className={analyzing ? 'animate-spin' : ''}>🔄</span>
            <span className="hidden sm:inline">{analyzing ? 'Analyzing...' : 'Refresh'}</span>
          </button>

          <button
            onClick={handleToggleArchiveStatus}
            className="px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 font-medium text-xs transition-all"
            title={project.status === 'ARCHIVED' ? 'Unarchive Project' : 'Archive Project'}
          >
            {project.status === 'ARCHIVED' ? 'Unarchive' : 'Archive'}
          </button>

          <button
            onClick={handleDeleteProject}
            className="px-3 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium text-xs transition-all"
            title="Delete Project"
          >
            Delete
          </button>
        </div>
      </div>

      {/* 3. PROJECT OVERVIEW STATISTICS */}
      <div className="space-y-4">
        {/* Primary Research-Level Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div 
            onClick={() => handleTabChange('papers')}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 cursor-pointer transition-all space-y-1"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
              <span>Papers</span>
              <span className="text-indigo-400 text-base">📄</span>
            </div>
            <div className="text-3xl font-extrabold text-white">{formatMetric(summary?.total_papers, project?.paper_count)}</div>
            <p className="text-[11px] text-slate-400">Indexed literature papers</p>
          </div>

          <div 
            onClick={() => handleTabChange('gaps')}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 cursor-pointer transition-all space-y-1"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
              <span>Potential Gaps</span>
              <span className="text-amber-400 text-base">❓</span>
            </div>
            <div className="text-3xl font-extrabold text-white">{formatMetric(gaps?.length)}</div>
            <p className="text-[11px] text-slate-400">Literature gaps detected</p>
          </div>

          <div 
            onClick={() => handleTabChange('opportunities')}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 cursor-pointer transition-all space-y-1"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
              <span>Research Opportunities</span>
              <span className="text-emerald-400 text-base">💡</span>
            </div>
            <div className="text-3xl font-extrabold text-white">{formatMetric(candidateDirections?.length, project?.direction_count)}</div>
            <p className="text-[11px] text-slate-400">Candidate directions</p>
          </div>

          <div 
            onClick={() => handleTabChange('proposals')}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/40 cursor-pointer transition-all space-y-1"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
              <span>Proposals</span>
              <span className="text-purple-400 text-base">📝</span>
            </div>
            <div className="text-3xl font-extrabold text-white">{formatMetric(proposals?.length, project?.proposal_count)}</div>
            <p className="text-[11px] text-slate-400">Draft proposals created</p>
          </div>
        </div>

        {/* Secondary Technical Metrics: Research Knowledge */}
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <span>🧠</span> Research Knowledge Metrics:
          </div>
          
          <div className="flex flex-wrap items-center gap-6 text-slate-300 font-medium">
            <div><strong className="text-indigo-300 font-bold">{formatMetric(summary?.total_nodes)}</strong> KG Nodes</div>
            <div className="text-slate-600">•</div>
            <div><strong className="text-indigo-300 font-bold">{formatMetric(summary?.total_edges)}</strong> KG Relationships</div>
            <div className="text-slate-600">•</div>
            <div><strong className="text-emerald-300 font-bold">{formatMetric(summary?.total_algorithms)}</strong> Algorithms</div>
            <div className="text-slate-600">•</div>
            <div><strong className="text-emerald-300 font-bold">{formatMetric(summary?.total_datasets)}</strong> Datasets</div>
            <div className="text-slate-600">•</div>
            <div><strong className="text-amber-300 font-bold">{formatMetric(summary?.total_methodologies)}</strong> Methodologies</div>
          </div>
        </div>
      </div>

      {/* 4. FOUR-STAGE RESEARCH JOURNEY STEPPER */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-extrabold text-white uppercase tracking-wider">Research Journey Lifecycle</h2>
            {activeTab !== 'overview' && (
              <button 
                onClick={() => handleTabChange('overview')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold underline"
              >
                ← Back to Overview
              </button>
            )}
          </div>
          <span className="text-xs text-slate-400 font-medium">Click any stage or sub-tab to navigate</span>
        </div>

        {/* Horizontal 4-Stage Stepper */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Stage 1: DISCOVER */}
          <div 
            onClick={() => handleTabChange('papers')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer ${
              currentStageNumber === 1 
                ? 'bg-slate-900 border-indigo-500/60 shadow-lg shadow-indigo-950/40 ring-1 ring-indigo-500/30' 
                : 'bg-slate-900/60 border-slate-800/90 opacity-85 hover:opacity-100 hover:border-indigo-500/50 hover:bg-slate-900/80'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                01 DISCOVER
              </span>
              <span className="text-xs">🔍</span>
            </div>
            <h3 className="text-sm font-bold text-white mb-2 hover:text-indigo-300 transition-colors">Literature Exploration</h3>
            
            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('papers'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'papers' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Papers ({formatMetric(papers?.length)})
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('concepts'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'concepts' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Concepts
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('map'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'map' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Map
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('connections'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'connections' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Connections
              </button>
            </div>
          </div>

          {/* Stage 2: UNDERSTAND */}
          <div 
            onClick={() => handleTabChange('gaps')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer ${
              currentStageNumber === 2 
                ? 'bg-slate-900 border-emerald-500/60 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/30' 
                : 'bg-slate-900/60 border-slate-800/90 opacity-85 hover:opacity-100 hover:border-emerald-500/50 hover:bg-slate-900/80'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                02 UNDERSTAND
              </span>
              <span className="text-xs">💡</span>
            </div>
            <h3 className="text-sm font-bold text-white mb-2 hover:text-emerald-300 transition-colors">Gaps & Opportunities</h3>
            
            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('gaps'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'gaps' ? 'bg-emerald-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Gaps ({formatMetric(gaps?.length)})
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('opportunities'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'opportunities' || activeTab === 'directions' ? 'bg-emerald-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Opportunities ({formatMetric(candidateDirections?.length)})
              </button>
            </div>
          </div>

          {/* Stage 3: BUILD */}
          <div 
            onClick={() => handleTabChange('plan')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer ${
              currentStageNumber === 3 
                ? 'bg-slate-900 border-amber-500/60 shadow-lg shadow-amber-950/40 ring-1 ring-amber-500/30' 
                : 'bg-slate-900/60 border-slate-800/90 opacity-85 hover:opacity-100 hover:border-amber-500/50 hover:bg-slate-900/80'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1">
                03 BUILD
              </span>
              <span className="text-xs">🧪</span>
            </div>
            <h3 className="text-sm font-bold text-white mb-2 hover:text-amber-300 transition-colors">Plan & Experiments</h3>
            
            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('plan'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'plan' ? 'bg-amber-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Research Plan
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('experiments'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'experiments' ? 'bg-amber-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Experiments
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('results-analysis'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'results-analysis' ? 'bg-amber-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Results
              </button>
            </div>
          </div>

          {/* Stage 4: FINALIZE */}
          <div 
            onClick={() => handleTabChange('proposals')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer ${
              currentStageNumber === 4 
                ? 'bg-slate-900 border-purple-500/60 shadow-lg shadow-purple-950/40 ring-1 ring-purple-500/30' 
                : 'bg-slate-900/60 border-slate-800/90 opacity-85 hover:opacity-100 hover:border-purple-500/50 hover:bg-slate-900/80'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1">
                04 FINALIZE
              </span>
              <span className="text-xs">📑</span>
            </div>
            <h3 className="text-sm font-bold text-white mb-2 hover:text-purple-300 transition-colors">Proposal & Report</h3>
            
            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('proposals'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'proposals' ? 'bg-purple-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Proposal
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('report'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'report' ? 'bg-purple-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Report
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('traceability'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'traceability' ? 'bg-purple-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Traceability
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); handleTabChange('manuscript'); }}
                className={`px-2.5 py-1 rounded-md transition-colors ${activeTab === 'manuscript' ? 'bg-purple-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
              >
                Paper
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* INTELLIGENCE LOADING STATE */}
      {isIntelligenceLoading && (
        <div className="p-10 rounded-2xl border border-slate-800 bg-slate-900/60 text-center space-y-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Analyzing research project...</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              Extracting entities, constructing knowledge graph, and analyzing literature gaps.
            </p>
          </div>
        </div>
      )}

      {/* INTELLIGENCE ERROR STATE */}
      {intelligenceError && !isIntelligenceLoading && (
        <div className="p-8 rounded-2xl border border-rose-500/30 bg-slate-900 text-center space-y-3">
          <h3 className="text-base font-bold text-rose-400">Unable to load project intelligence.</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            Failed to fetch or compute research analysis for this project.
          </p>
          <button
            onClick={handleRefreshAnalysis}
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md transition-all inline-flex items-center gap-1.5"
          >
            <span>🔄</span> Retry
          </button>
        </div>
      )}

      {/* EMPTY PROJECT WARNING */}
      {!isIntelligenceLoading && !intelligenceError && summary?.total_papers === 0 && (
        <div className="p-10 rounded-2xl border border-slate-800 bg-slate-900/60 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-2xl">
            📂
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">This research project has no papers assigned yet.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              Assign research papers from your library to compute project-scoped knowledge graphs, pairwise paper connections, shared concepts, research gaps, and proposals.
            </p>
          </div>
          <button
            onClick={() => setIsAddPaperOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all inline-flex items-center gap-2"
          >
            <span>+</span> Add Research Papers to Project
          </button>
        </div>
      )}

      {/* TAB CONTENT AREAS */}

      {/* OVERVIEW MAIN DASHBOARD VIEW */}
      {activeTab === 'overview' && !isIntelligenceLoading && !intelligenceError && summary?.total_papers > 0 && (
        <div className="space-y-8 animate-fade-in">
          
          {/* 5. PROJECT RESEARCH SYNTHESIS */}
          <div className="bg-slate-900/90 border border-indigo-500/20 rounded-2xl p-6 space-y-4">
            <h3 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
              <span>💡</span> PROJECT RESEARCH SYNTHESIS
            </h3>

            <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
              <p className="text-sm font-medium text-slate-200">
                <strong className="text-indigo-400 font-bold">{summary.total_papers}</strong> research papers have been analyzed within this project collection.
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 py-2">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-indigo-400 font-bold text-base block">{summary.total_nodes}</span>
                  <span className="text-[11px] text-slate-400">knowledge graph nodes</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-indigo-400 font-bold text-base block">{summary.total_edges}</span>
                  <span className="text-[11px] text-slate-400">relationships</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-emerald-400 font-bold text-base block">{summary.total_algorithms}</span>
                  <span className="text-[11px] text-slate-400">algorithms</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-emerald-400 font-bold text-base block">{summary.total_datasets}</span>
                  <span className="text-[11px] text-slate-400">datasets</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-amber-400 font-bold text-base block">{summary.total_methodologies}</span>
                  <span className="text-[11px] text-slate-400">methodologies</span>
                </div>
              </div>

              <p>
                <strong className="text-amber-300 font-bold">{gaps.length}</strong> potential research gaps were identified within the indexed project collection, supporting <strong className="text-emerald-300 font-bold">{candidateDirections.length}</strong> candidate research directions.
              </p>

              <div className="text-[11px] text-slate-400 bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 italic">
                Note: Findings are derived strictly from assigned project literature for academic analysis and exploratory direction formulation.
              </div>
            </div>
          </div>

          {/* 6. RESEARCH LANDSCAPE & PROGRESS (TWO-COLUMN LAYOUT) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* LEFT: Research Landscape / Knowledge Graph */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <span>🗺️</span> Research Landscape & Knowledge Graph
                  </h3>
                  <span className="text-[11px] text-indigo-400 font-medium">{summary.total_nodes} Nodes • {summary.total_edges} Edges</span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Interactive knowledge graph mapping relations across {summary.total_papers} assigned papers, {summary.total_algorithms} algorithms, and {summary.total_datasets} datasets.
                </p>

                {/* Graph Mini-Preview Box */}
                <div className="p-6 rounded-xl bg-slate-950/80 border border-slate-800/80 text-center space-y-3">
                  <div className="flex justify-center items-center gap-4 text-xs">
                    <span className="px-3 py-1 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-bold">
                      {summary.total_nodes} Concept Nodes
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="px-3 py-1 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20 font-bold">
                      {summary.total_edges} Links
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    View the full interactive 2D graph network with paper node filtering and directional linkages.
                  </p>
                </div>
              </div>

              <div>
                <button
                  onClick={() => handleTabChange('map')}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600/90 hover:bg-indigo-600 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2"
                >
                  <span>🗺️</span> View Interactive Research Map →
                </button>
              </div>
            </div>

            {/* RIGHT: Research Progress Bar Indicators */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <span>📊</span> Research Progress & Lifecycle
                  </h3>
                  <span className="text-[11px] text-emerald-400 font-bold">Stage {currentStageNumber} of 4</span>
                </div>

                <div className="space-y-3.5 text-xs">
                  {/* Papers Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-300">Papers Analyzed</span>
                      <span className="text-indigo-400 font-bold">{summary.total_papers}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.min(100, (summary.total_papers / 5) * 100)}%` }}></div>
                    </div>
                  </div>

                  {/* Research Gaps Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-300">Identified Research Gaps</span>
                      <span className="text-amber-400 font-bold">{gaps.length}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: `${Math.min(100, (gaps.length / 10) * 100)}%` }}></div>
                    </div>
                  </div>

                  {/* Opportunities Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-300">Candidate Opportunities</span>
                      <span className="text-emerald-400 font-bold">{candidateDirections.length}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(100, (candidateDirections.length / 5) * 100)}%` }}></div>
                    </div>
                  </div>

                  {/* Proposals Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-300">Proposals Created</span>
                      <span className="text-purple-400 font-bold">{proposals.length}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.min(100, (proposals.length / 2) * 100)}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  onClick={() => handleTabChange('journey')}
                  className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition-colors flex items-center justify-center gap-2 border border-slate-700"
                >
                  <span>🧭</span> View Full Guided Research Journey →
                </button>
              </div>
            </div>
          </div>

          {/* 7. RESEARCH GAPS PREVIEW */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                <span>❓</span> Identified Research Gaps ({gaps.length})
              </h3>
              <button 
                onClick={() => handleTabChange('gaps')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold underline"
              >
                View All Gaps →
              </button>
            </div>

            {gaps.length === 0 ? (
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-xs text-slate-400 italic">
                No research gaps detected within current project scope.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {gaps.slice(0, 4).map((g, idx) => {
                  const srcPapers = g.source_papers && g.source_papers.length > 0
                    ? g.source_papers
                    : [{ paper_id: g.source_paper_id, title: g.source_paper_title }];

                  return (
                    <div key={idx} className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 hover:border-slate-700 transition-all flex flex-col justify-between">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <h4 className="text-sm font-bold text-white">{g.title || g.missing_concept}</h4>
                          <span className="px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[11px] font-bold shrink-0">
                            Gap Score {typeof g.gap_score === 'number' ? (g.gap_score > 1 ? `${g.gap_score}%` : `${(g.gap_score * 100).toFixed(2)}%`) : g.gap_score}
                          </span>
                        </div>

                        <div className="text-[11px] text-slate-400">
                          Target Type: <span className="text-indigo-300 font-semibold">{g.concept_type || 'Entity'}</span>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">{g.explanation}</p>
                      </div>

                      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                        <span className="text-[11px] text-slate-400 truncate max-w-[200px]">
                          Supported by: {srcPapers[0]?.title || `Paper #${g.source_paper_id}`}
                        </span>
                        <button
                          onClick={() => handleTabChange('gaps')}
                          className="text-indigo-400 hover:text-indigo-300 font-semibold text-xs shrink-0"
                        >
                          Explore Gap →
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 8. RESEARCH OPPORTUNITIES PREVIEW */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                <span>💡</span> Candidate Research Opportunities ({candidateDirections.length})
              </h3>
              <button 
                onClick={() => handleTabChange('opportunities')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold underline"
              >
                View All Opportunities →
              </button>
            </div>

            {candidateDirections.length === 0 ? (
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-xs text-slate-400 italic">
                No candidate research directions generated. Assign additional papers to synthesize directions.
              </div>
            ) : (
              <div className="space-y-4">
                {candidateDirections.slice(0, 3).map((d, idx) => (
                  <div key={idx} className="p-5 sm:p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 hover:border-slate-700 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase">Direction #{d.direction_id}</span>
                        <h4 className="text-base font-bold text-white">{d.title}</h4>
                      </div>
                      <span className="px-3 py-1 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-xs font-bold self-start sm:self-auto">
                        {d.confidence || 'HIGH'} Confidence
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">{d.description}</p>

                    {/* Supporting Papers Evidence */}
                    <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5 text-xs">
                      <span className="text-[11px] font-bold text-slate-400 uppercase block">Supporting Paper Evidence:</span>
                      {d.supporting_papers && d.supporting_papers.length > 0 ? (
                        <div className="space-y-1">
                          {d.supporting_papers.map((sp, pIdx) => (
                            <div key={pIdx} className="text-slate-300 flex items-center gap-1.5 text-[11px]">
                              <span>📄</span>
                              <span className="font-medium truncate">{typeof sp === 'string' ? sp : sp.title || `Paper #${sp.id || sp.paper_id}`}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400 italic">No direct supporting paper found for this opportunity.</p>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center justify-end gap-3 pt-1">
                      <button
                        onClick={() => handleSaveDirection(d)}
                        disabled={savingDirectionId === d.direction_id}
                        className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all disabled:opacity-50"
                      >
                        {savingDirectionId === d.direction_id ? 'Saving...' : '💾 Save Direction'}
                      </button>
                      
                      <button
                        onClick={() => handleDraftProposalFromDirection(d)}
                        disabled={draftingDirectionId === d.direction_id}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all disabled:opacity-50"
                      >
                        {draftingDirectionId === d.direction_id ? 'Synthesizing...' : '🚀 Draft Proposal →'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 9. RESEARCH WORKFLOW LIFECYCLE FOOTER GRAPHIC */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">End-to-End Academic Research Lifecycle</h4>
            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-semibold text-slate-400">
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-indigo-300">Papers</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-indigo-300">Landscape</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-amber-300">Gaps</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-emerald-300">Opportunities</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-amber-300">Plan</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-amber-300">Experiments</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-amber-300">Results</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-purple-300">Proposal</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-purple-300">Report</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-purple-300">Traceability</span>
              <span>↓</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-purple-300">Submission</span>
            </div>
          </div>

        </div>
      )}

      {/* STAGE TAB CONTENT: JOURNEY */}
      {activeTab === 'journey' && (
        <ResearchJourney
          projectId={projectId}
          onSelectTab={(tabKey) => handleTabChange(tabKey)}
        />
      )}

      {/* STAGE TAB CONTENT: MAP */}
      {activeTab === 'map' && (
        <ErrorBoundary fallbackTitle="Unable to render Research Map view.">
          <ResearchMap
            data={intelligence}
            scope="project"
            projectName={project.name}
            onViewPaper={(id) => setViewingPaperId(id)}
            onGenerateDraft={handleDraftProposalFromDirection}
            draftingDirId={draftingDirectionId}
            mapOnly={true}
          />
        </ErrorBoundary>
      )}

      {/* STAGE TAB CONTENT: PAPERS */}
      {activeTab === 'papers' && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Assigned Project Papers ({filteredPapers.length} / {papers.length})
            </h3>

            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Search assigned papers..."
                value={paperSearchQuery}
                onChange={(e) => setPaperSearchQuery(e.target.value)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-full sm:w-56"
              />
              <button onClick={() => setIsAddPaperOpen(true)} className="btn-secondary py-1.5 px-3 text-xs font-bold shrink-0">
                + Add Papers
              </button>
            </div>
          </div>

          {filteredPapers.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400 italic">
              No assigned papers match search query "{paperSearchQuery}".
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredPapers.map((p) => (
                <div key={p.id} className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 hover:border-indigo-500/30 transition-all flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-indigo-400 font-bold block">Paper ID #{p.id}</span>
                        <h4 className="text-sm font-bold text-white hover:text-indigo-300 cursor-pointer" onClick={() => setViewingPaperId(p.id)}>
                          {p.title}
                        </h4>
                      </div>
                      <button
                        onClick={() => handleRemovePaper(p.id)}
                        className="text-slate-500 hover:text-rose-400 text-xs font-bold p-1 shrink-0"
                        title="Remove paper from project"
                      >
                        ✕
                      </button>
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{p.abstract}</p>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {p.algorithms && p.algorithms.map((alg, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-semibold">
                          {alg}
                        </span>
                      ))}
                      {p.datasets && p.datasets.map((ds, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[10px] font-semibold">
                          {ds}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-3 flex justify-end border-t border-slate-850">
                    <button onClick={() => setViewingPaperId(p.id)} className="text-indigo-400 text-xs font-semibold hover:underline">
                      View Paper Details →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STAGE TAB CONTENT: CONNECTIONS */}
      {activeTab === 'connections' && (
        <div className="space-y-5 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="space-y-0.5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span>🔗</span> Pairwise Paper Semantic Similarity
              </h3>
              <p className="text-xs text-slate-400">
                Comparisons across assigned project papers based on extracted concepts and vector embeddings.
              </p>
            </div>

            <span className="px-3.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-bold shrink-0">
              Showing {uniquePaperRelationships.length} unique connections
            </span>
          </div>

          {uniquePaperRelationships.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
              Insufficient paper count to compute pairwise paper similarity connections. Assign at least 2 papers.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {uniquePaperRelationships.map((r, idx) => {
                const srcId = r.source_paper_id || r.source_id;
                const tgtId = r.target_paper_id || r.target_id;
                const simVal = typeof r.similarity_score === 'number' ? r.similarity_score : parseFloat(r.similarity_score) || 0;
                const is100Pct = simVal >= 99.9;

                return (
                  <div key={idx} className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 flex flex-col justify-between hover:border-slate-700 transition-all">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <span className="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                          <span>🔗</span> Semantic Similarity Match
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${
                          is100Pct ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                        }`}>
                          {simVal.toFixed(1)}% Similar
                        </span>
                      </div>

                      {is100Pct && (
                        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300 space-y-1">
                          <span className="font-bold flex items-center gap-1">⚠️ 100% Similarity Warning</span>
                          <p className="text-amber-300/90 leading-relaxed">
                            These papers have extremely similar extracted concepts/content. Review both papers to determine whether they are duplicates.
                          </p>
                        </div>
                      )}

                      <div className="space-y-2 text-xs">
                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-slate-500 font-bold uppercase block">Paper A #{srcId}</span>
                            <span className="font-bold text-white truncate block">{r.source_paper_title}</span>
                          </div>
                          <button onClick={() => setViewingPaperId(srcId)} className="text-indigo-400 hover:underline text-[11px] font-semibold shrink-0">View</button>
                        </div>

                        <div className="text-center text-slate-500 font-bold text-sm">↕</div>

                        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-slate-500 font-bold uppercase block">Paper B #{tgtId}</span>
                            <span className="font-bold text-white truncate block">{r.target_paper_title}</span>
                          </div>
                          <button onClick={() => setViewingPaperId(tgtId)} className="text-indigo-400 hover:underline text-[11px] font-semibold shrink-0">View</button>
                        </div>
                      </div>

                      {r.shared_concepts && r.shared_concepts.length > 0 && (
                        <div className="pt-2 border-t border-slate-800 space-y-1.5">
                          <span className="text-[10px] text-slate-400 font-bold uppercase block">Shared concepts:</span>
                          <div className="flex flex-wrap gap-1">
                            {r.shared_concepts.map((sc, scIdx) => (
                              <span key={scIdx} className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 text-[10px] font-semibold border border-slate-700/60">
                                {sc}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* STAGE TAB CONTENT: CONCEPTS */}
      {activeTab === 'concepts' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex border-b border-slate-800 gap-2 text-xs font-bold overflow-x-auto scrollbar-none">
            {['algorithms', 'datasets', 'methodologies', 'domains', 'tasks', 'metrics', 'applications', 'keywords'].map((cat) => (
              <button
                key={cat}
                onClick={() => setConceptCategoryTab(cat)}
                className={`pb-2.5 px-3.5 transition-all border-b-2 uppercase tracking-wider whitespace-nowrap ${
                  conceptCategoryTab === cat ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                {cat} ({sharedConcepts[cat] ? sharedConcepts[cat].length : 0})
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {(sharedConcepts[conceptCategoryTab] || []).map((sc, idx) => {
              const rawRole = (sc.roles && sc.roles.length > 0) ? sc.roles[0] : '';
              const displayRole = rawRole
                ? rawRole.replace(/_/g, ' ')
                : (sc.type === 'dataset' ? 'EXPERIMENTAL DATASET' : (sc.type === 'domain' ? 'PRIMARY DOMAIN' : (sc.type === 'algorithm' ? 'USED MODEL' : (sc.type === 'methodology' ? 'PRIMARY METHODOLOGY' : 'RESEARCH CONCEPT'))));

              return (
                <div key={idx} className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2.5 flex flex-col justify-between hover:border-slate-700 transition-all">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-bold text-white truncate" title={sc.name}>{sc.name}</h4>
                      <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase shrink-0 ${
                        sc.classification === 'COMMON' ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      }`}>
                        {sc.classification === 'UNDERREPRESENTED' ? 'Underrepresented' : sc.classification}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-[9px] font-extrabold uppercase">
                        {displayRole}
                      </span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Coverage: <b className="text-slate-200">{sc.coverage_percentage}%</b></span>
                    <span>Appears in <b className="text-indigo-400">{sc.paper_count}</b> paper(s)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STAGE TAB CONTENT: GAPS */}
      {activeTab === 'gaps' && (
        <div className="space-y-4 animate-fade-in">
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            ⚠️ <strong>PROJECT-SCOPED ANALYSIS:</strong> Identified research gaps are derived strictly from research papers assigned to this project.
          </div>

          {gaps.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
              No research gaps detected within project scope.
            </div>
          ) : (
            <div className="space-y-4">
              {gaps.map((g, idx) => {
                const srcPapers = g.source_papers && g.source_papers.length > 0
                  ? g.source_papers
                  : [{ paper_id: g.source_paper_id, title: g.source_paper_title }];

                return (
                  <div key={idx} className="p-5 sm:p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                      <div>
                        <span className="text-[10px] font-mono text-amber-400 font-bold block">
                          {srcPapers.length > 1
                            ? `Supported across ${srcPapers.length} project papers`
                            : `Source Paper #${srcPapers[0].paper_id}`}
                        </span>
                        <h4 className="text-base font-bold text-white">
                          {g.title || g.missing_concept}
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-3 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-bold">
                          Gap Score {typeof g.gap_score === 'number' ? (g.gap_score > 1 ? `${g.gap_score}%` : `${(g.gap_score * 100).toFixed(2)}%`) : g.gap_score}
                        </span>
                        {g.evidence?.relationship_evidence_score !== undefined && (
                          <span className="px-3 py-1 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-bold">
                            Rel. Evidence {(g.evidence.relationship_evidence_score * 100).toFixed(2)}%
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400">Canonical Relationship Key:</span>
                      <span className="px-2.5 py-1 rounded-md bg-slate-800 text-indigo-300 font-mono text-[11px] font-bold border border-slate-700">
                        {g.evidence?.canonical_relationship_key || g.missing_concept}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">{g.explanation}</p>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                      <button
                        onClick={() => setExpandedGapId(expandedGapId === g.gap_id ? null : g.gap_id)}
                        className="text-xs text-indigo-400 font-semibold hover:underline flex items-center gap-1"
                      >
                        <span>{expandedGapId === g.gap_id ? '▼ Hide Evidence Details' : '▶ Explore Gap Evidence'}</span>
                      </button>
                    </div>

                    {expandedGapId === g.gap_id && (
                      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs text-slate-400 animate-fade-in">
                        <div className="font-bold text-slate-200 uppercase tracking-wider text-[10px]">Multi-Signal Evidence Breakdown:</div>
                        <ul className="list-disc list-inside space-y-1 text-[11px]">
                          <li>Confidence Rating: <b>{g.confidence || 'HIGH'}</b></li>
                          <li>Relationship Type: <b>{g.relationship_type || 'unassessed_canonical_relationship'}</b></li>
                          {g.evidence?.role_compatibility !== undefined && (
                            <li>Role Compatibility: <b>{(g.evidence.role_compatibility * 100).toFixed(1)}%</b></li>
                          )}
                          {g.evidence?.task_relevance !== undefined && (
                            <li>Task Relevance: <b>{(g.evidence.task_relevance * 100).toFixed(1)}%</b></li>
                          )}
                          {g.evidence?.cross_paper_support !== undefined && (
                            <li>Cross-Paper Support: <b>{(g.evidence.cross_paper_support * 100).toFixed(1)}%</b></li>
                          )}
                        </ul>

                        {g.gap_reasoning && Object.keys(g.gap_reasoning).length > 0 && (
                          <div className="pt-2 border-t border-slate-900 space-y-1.5">
                            <span className="font-bold text-indigo-400 block text-[10px] uppercase">Structured Gap Reasoning:</span>
                            <ul className="space-y-1 list-disc list-inside text-[11px] text-slate-300 leading-relaxed">
                              {g.gap_reasoning.component_a_evidence && (
                                <li><strong>Component A:</strong> {typeof g.gap_reasoning.component_a_evidence === 'object' ? g.gap_reasoning.component_a_evidence.description : g.gap_reasoning.component_a_evidence}</li>
                              )}
                              {g.gap_reasoning.component_b_evidence && (
                                <li><strong>Component B:</strong> {typeof g.gap_reasoning.component_b_evidence === 'object' ? g.gap_reasoning.component_b_evidence.description : g.gap_reasoning.component_b_evidence}</li>
                              )}
                              {g.gap_reasoning.missing_relationship && (
                                <li><strong>Missing Relationship:</strong> {typeof g.gap_reasoning.missing_relationship === 'object' ? g.gap_reasoning.missing_relationship.description : g.gap_reasoning.missing_relationship}</li>
                              )}
                              {g.gap_reasoning.evidence_limitation && (
                                <li className="text-amber-400/90 italic pt-0.5"><strong>Collection Limitation:</strong> {typeof g.gap_reasoning.evidence_limitation === 'object' ? g.gap_reasoning.evidence_limitation.statement : g.gap_reasoning.evidence_limitation}</li>
                              )}
                            </ul>
                          </div>
                        )}
                        {srcPapers.length > 0 && (
                          <div className="pt-2 border-t border-slate-900 space-y-1">
                            <span className="font-bold text-slate-300 block text-[10px] uppercase">Supporting Source Papers:</span>
                            <div className="space-y-1">
                              {srcPapers.map((sp, pIdx) => (
                                <div key={pIdx} className="text-[11px] text-slate-300 flex items-center gap-1.5">
                                  <span>📄</span>
                                  <span className="font-medium truncate">{sp.title}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* STAGE TAB CONTENT: DIRECTIONS / OPPORTUNITIES */}
      {(activeTab === 'opportunities' || activeTab === 'directions') && (
        <div className="space-y-6 animate-fade-in">
          {/* Saved Directions Section */}
          {savedDirections.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                Saved Research Directions ({savedDirections.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {savedDirections.map((sd) => (
                  <div key={sd.id} className="p-5 rounded-2xl bg-purple-950/20 border border-purple-800/40 space-y-3 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-bold text-white">{sd.title}</h4>
                        <button
                          onClick={() => handleDeleteSavedDirection(sd.id)}
                          className="text-slate-500 hover:text-rose-400 text-xs font-bold p-1 shrink-0"
                          title="Delete saved direction"
                        >
                          ✕
                        </button>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{sd.description}</p>
                    </div>
                    <div className="pt-2 border-t border-purple-900/30 flex items-center justify-between">
                      <span className="text-[10px] text-purple-300 font-bold">Saved Direction Snapshot</span>
                      <button
                        onClick={() => handleDraftProposalFromDirection(sd)}
                        disabled={draftingDirectionId === sd.direction_id}
                        className="btn-primary py-1 px-3 text-xs font-bold"
                      >
                        {draftingDirectionId === sd.direction_id ? 'Drafting...' : 'Draft Proposal →'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Candidate Directions Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Candidate Actionable Research Directions ({candidateDirections.length})
            </h3>
            {candidateDirections.length === 0 ? (
              <div className="p-8 rounded-2xl bg-slate-900/90 border border-amber-500/30 text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center justify-center mx-auto text-xl font-bold">
                  🛡️
                </div>
                <div className="space-y-2 max-w-lg mx-auto">
                  <h4 className="text-sm font-extrabold text-white">No evidence-qualified research opportunities were identified in the current indexed collection.</h4>
                  <p className="text-xs text-amber-300/90 leading-relaxed">
                    10 concepts are currently underrepresented, but underrepresentation alone is not treated as a research gap.
                  </p>
                  <p className="text-[11px] text-slate-400">
                    The evidence gate requires explicit text evidence or strong semantic alignment before proposing an automatic research opportunity.
                  </p>
                </div>
                <button
                  onClick={() => setIsManualModalOpen(true)}
                  className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs shadow-md transition-all inline-flex items-center gap-2"
                >
                  <span>✏️</span> Create Manual Research Direction
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {candidateDirections.map((d, idx) => (
                  <div key={idx} className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
                    <div className="flex items-start justify-between gap-4 border-b border-slate-800/80 pb-3">
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-purple-400 font-bold block">Direction #{d.direction_id}</span>
                        <h4 className="text-base font-bold text-white">{d.title}</h4>
                      </div>
                      <span className="px-3 py-1 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/30 text-xs font-bold shrink-0">
                        {d.confidence || 'HIGH'} Confidence
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">{d.description}</p>

                    {/* Supporting Papers Evidence */}
                    <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5 text-xs">
                      <span className="text-[11px] font-bold text-slate-400 uppercase block">Supporting Paper Evidence:</span>
                      {d.supporting_papers && d.supporting_papers.length > 0 ? (
                        <div className="space-y-1">
                          {d.supporting_papers.map((sp, pIdx) => (
                            <div key={pIdx} className="text-slate-300 flex items-center gap-1.5 text-[11px]">
                              <span>📄</span>
                              <span className="font-medium truncate">{typeof sp === 'string' ? sp : sp.title || `Paper #${sp.id || sp.paper_id}`}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400 italic">No direct supporting paper found for this opportunity.</p>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <button
                        onClick={() => handleSaveDirection(d)}
                        disabled={savingDirectionId === d.direction_id}
                        className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all disabled:opacity-50"
                      >
                        {savingDirectionId === d.direction_id ? 'Saving...' : '💾 Save Research Direction'}
                      </button>
                      
                      <button
                        onClick={() => handleDraftProposalFromDirection(d)}
                        disabled={draftingDirectionId === d.direction_id}
                        className="btn-primary py-2 px-4 text-xs font-bold"
                      >
                        {draftingDirectionId === d.direction_id ? 'Synthesizing...' : '🚀 Draft Proposal →'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* STAGE TAB CONTENT: PROPOSALS */}
      {activeTab === 'proposals' && (
        <div className="space-y-6 animate-fade-in">
          {/* Selected Opportunity Banner if user navigated with dir_id */}
          {(() => {
            const activeDirId = searchParams.get('dir_id') || selectedOpportunityDirId;
            const activeDir = candidateDirections.find(d => (d.direction_id || d.id) === activeDirId);
            if (!activeDir) return null;
            return (
              <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/40 shadow-lg space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-mono font-bold uppercase">
                        Selected Opportunity: #{activeDir.direction_id || activeDir.id}
                      </span>
                      <span className="text-xs text-slate-400">({activeDir.confidence || 'HIGH'} Confidence)</span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{activeDir.title}</h4>
                  </div>
                  <button
                    onClick={() => handleDraftProposalFromDirection(activeDir)}
                    disabled={draftingDirectionId === (activeDir.direction_id || activeDir.id)}
                    className="btn-primary py-2 px-4 text-xs font-bold shrink-0 flex items-center gap-2 shadow-lg shadow-purple-900/30"
                  >
                    <span>🚀</span>
                    {draftingDirectionId === (activeDir.direction_id || activeDir.id) ? 'Synthesizing Proposal...' : 'Synthesize & Draft Proposal →'}
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{activeDir.description}</p>
              </div>
            );
          })()}

          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Saved Research Proposals ({proposals.length})
            </h3>
          </div>

          {proposals.length === 0 ? (
            <div className="p-12 rounded-2xl border border-slate-800 bg-slate-900/50 text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-xl text-slate-400">
                📝
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-bold text-white">No research proposals have been created yet.</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Navigate to the Directions tab to synthesize a proposal draft from actionable research directions.
                </p>
              </div>
              <button onClick={() => handleTabChange('opportunities')} className="btn-secondary py-2 px-4 text-xs font-bold">
                Go to Research Directions →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {proposals.map((rawProp) => {
                const prop = normalizeProposal(rawProp);
                return (
                  <div key={prop.id || prop.proposal_id} className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <span className="text-[10px] font-mono text-amber-400 font-bold block">
                            Proposal UUID #{prop.proposal_id.slice(0, 8)}
                          </span>
                          <h4 className="text-base font-bold text-white">{prop.title}</h4>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-bold shrink-0">
                          v{prop.current_version_number}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pt-1">
                        <span>Status: <b className="text-emerald-400">{prop.status}</b></span>
                        <span>•</span>
                        <span>Mode: <b className="text-indigo-300">{prop.generation_mode}</b></span>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                      <button
                        onClick={() => handleDeleteProposal(prop.id)}
                        className="text-xs text-rose-400 hover:underline font-semibold"
                      >
                        Delete
                      </button>
                      <button
                        onClick={() => handleOpenSavedProposal(prop.id)}
                        className="btn-primary py-1.5 px-4 text-xs font-bold"
                      >
                        Open Proposal Workspace →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* STAGE TAB CONTENT: RESEARCH PLAN */}
      {activeTab === 'plan' && (
        <div className="space-y-8 animate-fade-in">
          {/* HEADER */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🧪</span> Project Research Methodology Plans
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Select an evidence-grounded research opportunity below to generate, view, or manage a structured implementation & experiment execution plan.
              </p>
            </div>

            {savedDirections.length > 0 && (
              <button
                onClick={() => {
                  const el = document.getElementById('available-opportunities-section');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
                className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20 self-start md:self-auto shrink-0"
              >
                <span>+</span> Create Plan for Another Opportunity
              </button>
            )}
          </div>

          {/* SECTION 1: SAVED RESEARCH METHODOLOGY PLANS */}
          {savedDirections.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                <span>✓</span> Saved Research Methodology Plans ({savedDirections.length})
              </h4>

              <div className="grid grid-cols-1 gap-4">
                {savedDirections.map((plan) => {
                  const dirId = plan.source_direction_id || 'dir_1';
                  const planData = plan.direction_data?.methodology_plan || {};
                  const problemText = planData.research_problem || plan.description || 'Structured research execution plan.';
                  const contribText = planData.expected_contribution || 'Controlled comparative benchmarking.';

                  return (
                    <div key={plan.id} className="rounded-2xl p-5 border border-emerald-500/30 bg-slate-900/90 shadow-xl space-y-4">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-mono font-bold text-[10px] uppercase">
                            SAVED RESEARCH PLAN
                          </span>
                          <span className="px-2.5 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[10px]">
                            Source Opportunity: {dirId}
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-400">
                          Saved: {new Date(plan.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <div>
                        <h4 className="text-base font-extrabold text-white">{plan.title}</h4>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                        <div className="space-y-1 p-3 rounded-xl bg-slate-950/60 border border-slate-850">
                          <span className="text-[10px] text-slate-400 uppercase font-bold block">Research Problem:</span>
                          <p className="text-slate-200 font-medium leading-relaxed">{problemText}</p>
                        </div>
                        <div className="space-y-1 p-3 rounded-xl bg-slate-950/60 border border-slate-850">
                          <span className="text-[10px] text-slate-400 uppercase font-bold block">Expected Contribution:</span>
                          <p className="text-indigo-300 font-medium leading-relaxed">{contribText}</p>
                        </div>
                      </div>

                      {/* ACTION BUTTONS */}
                      <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-850">
                        <button
                          onClick={() => setPlanningDirId(dirId)}
                          className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
                        >
                          <span>🧪</span> Open Full Methodology Planner →
                        </button>

                        <button
                          onClick={() => handleTabChange('experiments')}
                          className="px-3.5 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-bold text-xs transition-all flex items-center gap-1.5"
                        >
                          <span>⚡</span> Build Experiments →
                        </button>

                        <button
                          onClick={() => setDraftingDirectionId(dirId)}
                          className="px-3.5 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 font-bold text-xs transition-all flex items-center gap-1.5"
                        >
                          <span>📑</span> Draft Proposal →
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* SECTION 2: AVAILABLE RESEARCH OPPORTUNITIES CHOOSER */}
          <div id="available-opportunities-section" className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>🎯</span> AVAILABLE RESEARCH OPPORTUNITIES ({eligibleOpportunities.length})
                </h4>
                <p className="text-xs text-slate-400">
                  {eligibleOpportunities.length > 1
                    ? "Select one research opportunity below to generate its dedicated methodology plan:"
                    : "Evidence-grounded research opportunities eligible for methodology planning:"}
                </p>
              </div>

              {selectedOpportunityDirId && (
                <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 text-xs font-bold flex items-center gap-1.5 self-start sm:self-auto">
                  <span>✓</span> Opportunity Selected
                </span>
              )}
            </div>

            {eligibleOpportunities.length === 0 ? (
              <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto text-xl">
                  🚫
                </div>
                <h4 className="text-sm font-bold text-slate-200">NO ELIGIBLE RESEARCH OPPORTUNITIES</h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  No evidence-grounded research direction is currently available for methodology planning in this project. Please assign more research papers or reindex project intelligence.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  {eligibleOpportunities.map((opp, idx) => {
                    const dirId = opp.direction_id || opp.id || `dir_${idx + 1}`;
                    const isSelected = selectedOpportunityDirId === dirId;
                    const suppPapers = opp.supporting_papers || [];
                    const algos = opp.candidate_algorithms || [];
                    const datasets = opp.candidate_datasets || [];

                    return (
                      <div
                        key={dirId}
                        onClick={() => setSelectedOpportunityDirId(dirId)}
                        className={`cursor-pointer rounded-2xl p-5 transition-all duration-200 border relative ${
                          isSelected
                            ? 'bg-indigo-950/40 border-indigo-500 shadow-xl ring-2 ring-indigo-500/40'
                            : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4 mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all ${
                              isSelected ? 'border-indigo-400 bg-indigo-500 text-slate-950 font-bold text-xs' : 'border-slate-600 bg-slate-950'
                            }`}>
                              {isSelected ? '✓' : ''}
                            </div>

                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                              Opportunity {idx + 1}
                            </span>

                            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono font-bold">
                              {dirId}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
                              opp.confidence === 'High' || opp.confidence === 'HIGH'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                            }`}>
                              Confidence: {opp.confidence || 'High'}
                            </span>

                            {isSelected && (
                              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500 text-slate-950 font-extrabold text-[10px] uppercase shadow-md">
                                ✓ Selected
                              </span>
                            )}
                          </div>
                        </div>

                        {/* TITLE & PROBLEM */}
                        <div className="space-y-1 mb-4 pl-8">
                          <h4 className="text-base font-extrabold text-white">{opp.title}</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">{opp.research_problem}</p>
                        </div>

                        {/* METADATA ENTITIES */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pl-8 text-xs">
                          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-850 space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">Supporting Papers ({suppPapers.length}):</span>
                            <p className="text-slate-200 text-[11px] truncate">
                              {suppPapers.length > 0
                                ? suppPapers.map(sp => `Paper ${sp.paper_id || sp.id}`).join(', ')
                                : 'Indexed project collection'}
                            </p>
                          </div>

                          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-850 space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">Candidate Algorithms:</span>
                            <p className="text-indigo-300 text-[11px] truncate">
                              {algos.length > 0 ? algos.map(a => a.name || a).join(', ') : 'Standard baseline suite'}
                            </p>
                          </div>

                          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-850 space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">Candidate Datasets:</span>
                            <p className="text-emerald-300 text-[11px] truncate">
                              {datasets.length > 0 ? datasets.map(d => d.name || d).join(', ') : 'Benchmark evaluation split'}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* GENERATE PLAN BUTTON */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    onClick={() => {
                      if (!selectedOpportunityDirId) {
                        alert('Please select a research opportunity from the list first.');
                        return;
                      }
                      setPlanningDirId(selectedOpportunityDirId);
                    }}
                    disabled={!selectedOpportunityDirId}
                    className="btn-primary py-2.5 px-6 text-xs font-extrabold flex items-center gap-2 shadow-xl disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <span>🧪</span> Generate Plan for Selected Opportunity →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* STAGE TAB CONTENT: EXPERIMENTS */}
      {activeTab === 'experiments' && (
        <ResearchExperimentWorkspace
          projectId={projectId}
          directionId={activePlanDirId}
        />
      )}

      {/* STAGE TAB CONTENT: RESULTS */}
      {activeTab === 'results-analysis' && (
        <ResearchResultsAnalysis
          projectId={projectId}
          directionId={activePlanDirId || selectedOpportunityDirId}
          onOpenExperiments={(targetDirId) => handleTabChange('experiments', targetDirId || activePlanDirId || selectedOpportunityDirId)}
        />
      )}

      {/* STAGE TAB CONTENT: ACADEMIC MANUSCRIPT */}
      {(activeTab === 'manuscript' || activeTab === 'academic-paper') && (
        <AcademicManuscriptWorkspace
          projectId={projectId}
        />
      )}

      {/* STAGE TAB CONTENT: TRACEABILITY */}
      {activeTab === 'traceability' && (
        <ProjectTraceabilityPipeline
          projectId={projectId}
          selectedDirectionId={searchParams.get('dir_id') || selectedOpportunityDirId}
          onSelectDirection={(dirId) => handleTabChange('traceability', dirId)}
          onSelectTab={(tabKey, optionalDirId) => handleTabChange(tabKey, optionalDirId)}
          onOpenPaper={(paperId) => setViewingPaperId(paperId)}
          onOpenProposal={(propId, verNum) => {
            if (propId) {
              handleOpenSavedProposal(propId, verNum);
            } else {
              handleTabChange('directions');
            }
          }}
          onOpenPlan={(dirId) => {
            setPlanningDirId(dirId || activePlanDirId);
          }}
          onOpenExperiments={(dirId) => handleTabChange('experiments', dirId)}
          onOpenResults={(dirId) => handleTabChange('results-analysis', dirId)}
        />
      )}

      {/* STAGE TAB CONTENT: REPORT */}
      {activeTab === 'report' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white">Project Research Report Overview</h3>
              <p className="text-xs text-slate-400">Consolidated deterministic summary of research problem, paper landscape, concepts, gaps, and proposals.</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => handleReportExport('pdf')}
                disabled={exporting}
                className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow border border-rose-500/30 transition disabled:opacity-50"
              >
                PDF
              </button>
              <button
                onClick={() => handleReportExport('md')}
                disabled={exporting}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition disabled:opacity-50"
              >
                Markdown
              </button>
              <button
                onClick={() => handleReportExport('json')}
                disabled={exporting}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl shadow border border-indigo-500/30 transition disabled:opacity-50"
              >
                JSON
              </button>
            </div>
          </div>

          {reportLoading ? (
            <div className="p-12 text-center text-xs text-slate-400 animate-pulse">
              Generating project research report...
            </div>
          ) : reportData ? (
            <div className="p-8 rounded-2xl border border-slate-800 bg-slate-900/90 space-y-6 text-xs text-slate-300">
              <div className="border-b border-slate-800 pb-4 space-y-1">
                <h2 className="text-xl font-bold text-white">{reportData.title || project.name}</h2>
                <p className="text-xs text-slate-400">Project ID: #{project.id} • Generated Report</p>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-indigo-400 uppercase tracking-wider text-[11px]">Research Executive Summary</h4>
                <p className="leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">{reportData.executive_summary}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                  <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">Paper Landscape</h4>
                  <p>Total Papers: <b>{reportData.paper_landscape?.length || papers.length}</b></p>
                </div>
                <div className="space-y-2 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                  <h4 className="font-bold text-amber-400 uppercase tracking-wider text-[11px]">Identified Research Gaps</h4>
                  <p>Total Gaps: <b>{reportData.research_gaps?.length || gaps.length}</b></p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 italic">
              Could not load report preview. Use export buttons above to download the full report.
            </div>
          )}
        </div>
      )}

      {/* MODALS */}

      {/* PAPER COLLECTION BUILDER MODAL */}
      {isAddPaperOpen && (
        <ProjectPaperSelector
          projectId={projectId}
          onClose={() => setIsAddPaperOpen(false)}
          onPapersAdded={() => fetchProjectData()}
        />
      )}

      {/* PAPER VIEW MODAL */}
      {viewingPaperId && (
        <PaperViewModal paperId={viewingPaperId} onClose={() => setViewingPaperId(null)} />
      )}

      {/* PROPOSAL WORKSPACE MODAL */}
      {isProposalOpen && activeProposalData && (
        <ProposalWorkspaceModal
          proposal={activeProposalData}
          proposalId={selectedProposalDbId}
          onClose={() => {
            setIsProposalOpen(false);
            fetchProjectData();
          }}
          onSelectPaperId={(paperId) => setViewingPaperId(paperId)}
        />
      )}

      {/* PROJECT RESEARCH REPORT MODAL */}
      <ProjectResearchReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        projectId={projectId}
        projectName={project?.name}
      />

      {/* MANUAL RESEARCH DIRECTION MODAL */}
      {isManualModalOpen && (
        <div className="fixed inset-0 z-[110] overflow-y-auto bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
          <div className="relative w-full max-w-xl bg-slate-900 border border-amber-500/30 rounded-3xl shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-extrabold uppercase tracking-widest">
                  ✏️ USER-PROVIDED RESEARCH IDEA
                </span>
                <h3 className="text-lg font-bold text-white">Create Manual Research Direction</h3>
              </div>
              <button onClick={() => setIsManualModalOpen(false)} className="text-slate-400 hover:text-white font-bold p-1">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateManualProposal} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-300 block">Research Idea Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Evaluate Swin-Axial Transformer for Early Crop Disease Detection"
                  value={manualTitleInput}
                  onChange={(e) => setManualTitleInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-300 block">Research Concept & Hypothesis Description</label>
                <textarea
                  rows={4}
                  placeholder="Describe your research motivation, target concepts, and proposed hypothesis..."
                  value={manualDescInput}
                  onChange={(e) => setManualDescInput(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-amber-500 resize-y"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-850 text-[11px] text-slate-400 italic">
                Note: Manual ideas are explicitly tagged as <strong>USER-PROVIDED RESEARCH IDEA</strong> and kept separate from system-generated literature evidence opportunities.
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsManualModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingManual}
                  className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs shadow-md transition-all disabled:opacity-50"
                >
                  {creatingManual ? 'Creating Proposal...' : 'Create Manual Proposal →'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD RESEARCH PAPER SELECTOR MODAL */}
      {isAddPaperOpen && (
        <ProjectPaperSelector
          projectId={projectId}
          onClose={() => setIsAddPaperOpen(false)}
          onPapersAdded={() => {
            setIsAddPaperOpen(false);
            sessionStorage.removeItem(`intelliresearch_intel_${projectId}`);
            fetchProjectData({ refresh: true });
          }}
        />
      )}

      {/* RESEARCH METHODOLOGY PLANNER MODAL */}
      {planningDirId && (
        <ResearchMethodologyPlannerModal
          directionId={planningDirId}
          projectId={projectId}
          onClose={() => setPlanningDirId(null)}
          onGenerateDraft={(dirId) => {
            setPlanningDirId(null);
            handleDraftProposalFromDirection(dirId);
          }}
          onStartExperiments={(dirId) => {
            setPlanningDirId(null);
            handleTabChange('experiments', dirId);
          }}
        />
      )}
    </div>
  );
}
