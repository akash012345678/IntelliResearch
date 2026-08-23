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
import ErrorBoundary from '../components/ErrorBoundary';

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

  // Filter & Search states inside tabs
  const [paperSearchQuery, setPaperSearchQuery] = useState('');
  const [conceptCategoryTab, setConceptCategoryTab] = useState('algorithms');
  const [expandedGapId, setExpandedGapId] = useState(null);
  const [draftingDirectionId, setDraftingDirectionId] = useState(null);
  const [savingDirectionId, setSavingDirectionId] = useState(null);

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  useEffect(() => {
    if (activeTab === 'report' && !reportData && projectId) {
      fetchReportData();
    }
  }, [activeTab, projectId]);

  // Derived Intelligence Data & Unconditional React Hooks
  const summary = intelligence?.collection_summary || { total_papers: 0, total_nodes: 0, total_edges: 0, total_keywords: 0, total_algorithms: 0, total_datasets: 0, total_methodologies: 0, total_domains: 0 };
  const papers = intelligence?.paper_landscape || [];
  const sharedConcepts = intelligence?.shared_concepts || { algorithms: [], datasets: [], methodologies: [], domains: [], keywords: [] };
  const relationships = intelligence?.paper_relationships || [];
  const gaps = intelligence?.research_gaps || [];
  const candidateDirections = intelligence?.candidate_research_directions || [];
  const traceability = intelligence?.proposal_traceability || [];
  const insightSummary = intelligence?.insight_summary || 'No project synthesis available.';

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

  const fetchProjectData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch Project Details, Project Research Intelligence, Proposals, Directions, and Research Journey in parallel
      const [projRes, intelRes, propRes, dirRes, jnRes] = await Promise.all([
        apiService.getProject(projectId),
        apiService.getProjectResearchIntelligence(projectId),
        apiService.getProjectProposals(projectId),
        apiService.getProjectDirections(projectId),
        apiService.getProjectResearchJourney(projectId),
      ]);
      setProject(projRes.data);
      setIntelligence(intelRes.data);
      setProposals(propRes.data || []);
      setSavedDirections(dirRes.data || []);
      setJourneySummary(jnRes.data);
    } catch (err) {
      console.error('Failed to load project workspace data:', err);
      setError('Unable to analyze this research project collection.');
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
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

  const handleTabChange = (tabKey) => {
    setSearchParams({ tab: tabKey });
  };

  const handleRefreshAnalysis = () => {
    setAnalyzing(true);
    fetchProjectData();
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
    const dirId = typeof directionOrId === 'string' ? directionOrId : directionOrId.direction_id;
    setDraftingDirectionId(dirId);
    try {
      const draftRes = await apiService.generateProposalDraft(dirId);
      setActiveProposalData(draftRes.data);
      setSelectedProposalDbId(null);
      setIsProposalOpen(true);
    } catch (err) {
      console.error('Failed to synthesize proposal draft:', err);
      alert('Failed to synthesize proposal draft. Please try again.');
    } finally {
      setDraftingDirectionId(null);
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

  return (
    <div className="space-y-8 pb-16 animate-fade-in">
      
      {/* WORKSPACE BREADCRUMB & SCOPE BANNER */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <Link to="/research-projects" className="hover:text-indigo-400 font-semibold transition-all">Research Projects</Link>
          <span>/</span>
          <span className="text-slate-200 font-bold truncate max-w-xs">{project.name}</span>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
          <span>PROJECT SCOPE • <b>{summary.total_papers} Research Papers</b></span>
        </div>
      </div>

      {/* WORKSPACE HEADER BAR */}
      <div className="glass-card p-8 rounded-3xl border border-indigo-900/40 bg-slate-950/80 shadow-2xl relative overflow-hidden flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <span className="px-3 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-[10px] font-extrabold uppercase tracking-widest">
              🔬 RESEARCH PROJECT WORKSPACE
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
              project.status === 'ARCHIVED' ? 'bg-slate-800 text-slate-400 border-slate-700' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}>
              {project.status}
            </span>
          </div>

          <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">{project.name}</h1>
          {project.description && (
            <p className="text-xs text-slate-300 leading-relaxed">{project.description}</p>
          )}
        </div>

        {/* WORKSPACE ACTIONS */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            onClick={() => setIsReportOpen(true)}
            className="px-4 py-2 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-xs shadow-lg shadow-emerald-950/40 border border-emerald-400/30 transition-all flex items-center gap-1.5 transform hover:-translate-y-0.5"
          >
            <span>📊</span> Generate Research Report
          </button>
          <button
            onClick={() => setIsAddPaperOpen(true)}
            className="px-4 py-2 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center gap-1.5"
          >
            <span>+</span> Add Research Papers
          </button>
          <button
            onClick={handleRefreshAnalysis}
            disabled={analyzing}
            className="px-3.5 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            <span className={analyzing ? 'animate-spin' : ''}>🔄</span> {analyzing ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
          <button
            onClick={handleToggleArchiveStatus}
            className="px-3 py-2 rounded-2xl bg-slate-850 hover:bg-slate-800 text-slate-300 border border-slate-700 font-bold text-xs transition-all"
          >
            {project.status === 'ARCHIVED' ? 'Unarchive' : 'Archive'}
          </button>
          <button
            onClick={handleDeleteProject}
            className="px-3 py-2 rounded-2xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold text-xs transition-all"
          >
            Delete
          </button>
        </div>
      </div>

      {/* COLLECTION METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Papers</span>
          <span className="text-xl font-black text-indigo-400">{summary.total_papers}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Saved Directions</span>
          <span className="text-xl font-black text-purple-400">{savedDirections.length}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Proposals</span>
          <span className="text-xl font-black text-amber-400">{proposals.length}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">KG Nodes</span>
          <span className="text-xl font-black text-indigo-300">{summary.total_nodes}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">KG Links</span>
          <span className="text-xl font-black text-indigo-300">{summary.total_edges}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Algorithms</span>
          <span className="text-xl font-black text-emerald-400">{summary.total_algorithms}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Datasets</span>
          <span className="text-xl font-black text-emerald-400">{summary.total_datasets}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-semibold uppercase block">Methodologies</span>
          <span className="text-xl font-black text-amber-300">{summary.total_methodologies}</span>
        </div>
      </div>

      {/* EMPTY PROJECT STATE WARNING */}
      {summary.total_papers === 0 && (
        <div className="glass-card p-12 rounded-3xl border border-slate-800 bg-slate-900/50 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-2xl">
            📂
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-extrabold text-slate-100">This research project has no papers yet.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              Assign research papers from your paper library to compute project-scoped knowledge graphs, pairwise paper connections, shared concepts, research gaps, and proposals.
            </p>
          </div>
          <button
            onClick={() => setIsAddPaperOpen(true)}
            className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs shadow-md transition-all inline-flex items-center gap-2"
          >
            <span>+</span> Add Research Papers to Project
          </button>
        </div>
      )}

      {/* WORKSPACE NAVIGATION TABS */}
      {summary.total_papers > 0 && (
        <>
          <div className="flex border-b border-slate-800 overflow-x-auto gap-2 text-xs font-bold scrollbar-none pb-1">
            {/* GROUP 1 — DISCOVER */}
            <div className="flex items-center bg-slate-950/80 p-1 rounded-2xl border border-slate-800/80 shrink-0">
              <span className="text-[9px] text-indigo-400 font-extrabold uppercase px-2">DISCOVER</span>
              <button
                onClick={() => handleTabChange('journey')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'journey' ? 'bg-indigo-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>🧭</span> Journey
              </button>
              <button
                onClick={() => handleTabChange('map')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'map' ? 'bg-indigo-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>🗺️</span> Map
              </button>
              <button
                onClick={() => handleTabChange('papers')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'papers' ? 'bg-indigo-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>📄</span> Papers ({papers.length})
              </button>
              <button
                onClick={() => handleTabChange('concepts')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'concepts' ? 'bg-indigo-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>🧠</span> Concepts
              </button>
            </div>

            {/* GROUP 2 — UNDERSTAND */}
            <div className="flex items-center bg-slate-950/80 p-1 rounded-2xl border border-slate-800/80 shrink-0">
              <span className="text-[9px] text-emerald-400 font-extrabold uppercase px-2">UNDERSTAND</span>
              <button
                onClick={() => handleTabChange('gaps')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'gaps' ? 'bg-emerald-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>❓</span> Gaps ({gaps.length})
              </button>
              <button
                onClick={() => handleTabChange('directions')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'directions' ? 'bg-emerald-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>💡</span> Opportunities
              </button>
            </div>

            {/* GROUP 3 — BUILD */}
            <div className="flex items-center bg-slate-950/80 p-1 rounded-2xl border border-slate-800/80 shrink-0">
              <span className="text-[9px] text-amber-400 font-extrabold uppercase px-2">BUILD</span>
              <button
                onClick={() => handleTabChange('plan')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'plan' ? 'bg-amber-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>🧪</span> Research Plan
              </button>
              <button
                onClick={() => handleTabChange('experiments')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'experiments' ? 'bg-amber-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>⚙️</span> Experiments
              </button>
              <button
                onClick={() => handleTabChange('results-analysis')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'results-analysis' ? 'bg-amber-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>📊</span> Results
              </button>
            </div>

            {/* GROUP 5 — FINALIZE */}
            <div className="flex items-center bg-slate-950/80 p-1 rounded-2xl border border-slate-800/80 shrink-0">
              <span className="text-[9px] text-rose-400 font-extrabold uppercase px-2">FINALIZE</span>
              <button
                onClick={() => handleTabChange('report')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'report' ? 'bg-rose-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>📑</span> Report
              </button>
              <button
                onClick={() => handleTabChange('traceability')}
                className={`py-1.5 px-3 rounded-xl transition-all flex items-center gap-1.5 ${
                  activeTab === 'traceability' ? 'bg-rose-600 text-white font-extrabold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>📜</span> Traceability ({traceability.length})
              </button>
            </div>
          </div>

          {/* TAB: RESEARCH JOURNEY */}
          {activeTab === 'journey' && (
            <ResearchJourney
              projectId={projectId}
              onSelectTab={(tabKey) => handleTabChange(tabKey)}
            />
          )}

          {/* TAB: RESEARCH MAP */}
          {activeTab === 'map' && (
            <ErrorBoundary fallbackTitle="Unable to render Research Map view.">
              <ResearchMap
                data={intelligence}
                scope="project"
                projectName={project.name}
                onViewPaper={(id) => setViewingPaperId(id)}
                onGenerateDraft={handleDraftProposalFromDirection}
                draftingDirId={draftingDirectionId}
              />
            </ErrorBoundary>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6 animate-fade-in">
              {/* Insight Summary Box */}
              <div className="glass-card p-6 rounded-3xl border border-indigo-500/20 bg-slate-950/70 space-y-3">
                <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                  <span>💡</span> Project Research Synthesis
                </h3>
                <p className="text-xs text-slate-200 leading-relaxed">{insightSummary}</p>
              </div>

              {/* Pairwise Connections Preview & Top Gaps */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 rounded-3xl border border-slate-850 bg-slate-950/60 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                      <span>🔗</span> Strongest Paper Connections
                    </h3>
                    <button onClick={() => handleTabChange('connections')} className="text-xs text-indigo-400 font-bold hover:underline">
                      View All →
                    </button>
                  </div>
                  {relationships.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">Assign more papers to compute similarity connections.</p>
                  ) : (
                    <div className="space-y-3">
                      {relationships.slice(0, 3).map((r, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-extrabold text-slate-100 truncate">{r.source_paper_title}</span>
                            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-black text-[10px] shrink-0">
                              {r.similarity_score}% similarity
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-1">
                            <span>↔</span> <span className="font-semibold text-slate-300 truncate">{r.target_paper_title}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="glass-card p-6 rounded-3xl border border-slate-850 bg-slate-950/60 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                      <span>🔍</span> Identified Research Gaps
                    </h3>
                    <button onClick={() => handleTabChange('gaps')} className="text-xs text-indigo-400 font-bold hover:underline">
                      View All →
                    </button>
                  </div>
                  {gaps.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No research gaps detected within project scope.</p>
                  ) : (
                    <div className="space-y-3">
                      {gaps.slice(0, 3).map((g, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-extrabold text-amber-300">{g.missing_concept}</span>
                            <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold">
                              Gap Score {g.gap_score}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 line-clamp-2">{g.explanation}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Academic Paper Card */}
              <div className="glass-card p-6 rounded-3xl border border-indigo-500/30 bg-slate-950/70 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="space-y-1">
                  <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[10px]">
                    📄 ACADEMIC PAPER / THESIS GENERATOR
                  </span>
                  <h4 className="text-base font-black text-slate-100">Evidence-Grounded 29-Section Manuscript Draft</h4>
                  <p className="text-xs text-slate-400">
                    Transform your assigned papers, gaps, methodology plan, and empirical results into a structured academic manuscript with 4-level evidence classification badges.
                  </p>
                </div>
                <button
                  onClick={() => handleTabChange('manuscript')}
                  className="btn-primary py-2.5 px-6 text-xs font-extrabold whitespace-nowrap shrink-0"
                >
                  📄 Open Academic Paper →
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: PAPERS */}
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
                <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400 italic">
                  No assigned papers match search query "{paperSearchQuery}".
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredPapers.map((p) => (
                    <div key={p.id} className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3 hover:border-indigo-500/30 transition-all flex flex-col justify-between">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <span className="text-[10px] font-mono text-indigo-400 font-bold block">Paper ID #{p.id}</span>
                            <h4 className="text-sm font-extrabold text-slate-100 hover:text-indigo-300 cursor-pointer" onClick={() => setViewingPaperId(p.id)}>
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
                            <span key={idx} className="px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-semibold">
                              {alg}
                            </span>
                          ))}
                          {p.datasets && p.datasets.map((ds, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[10px] font-semibold">
                              {ds}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="pt-3 flex justify-end border-t border-slate-850">
                        <button onClick={() => setViewingPaperId(p.id)} className="text-indigo-400 text-xs font-bold hover:underline">
                          View Paper Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: CONNECTIONS */}
          {activeTab === 'connections' && (
            <div className="space-y-5 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div className="space-y-0.5">
                  <h3 className="text-sm font-black text-slate-100 uppercase tracking-wider flex items-center gap-2">
                    <span>🔗</span> How Are These Papers Related?
                  </h3>
                  <p className="text-xs text-slate-400">
                    Each card compares two different papers from your project. A paper is shown only once per pair.
                  </p>
                </div>

                <span className="px-3.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-black shrink-0">
                  Showing {uniquePaperRelationships.length} unique paper connections
                </span>
              </div>

              {uniquePaperRelationships.length === 0 ? (
                <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
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
                      <div key={idx} className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between hover:border-indigo-500/30 transition-all">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <span className="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                              <span>🔗</span> Semantic Similarity Match
                            </span>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-black border ${
                              is100Pct ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                            }`}>
                              {simVal.toFixed(1)}% Similar
                            </span>
                          </div>

                          {is100Pct && (
                            <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300 space-y-1">
                              <span className="font-bold flex items-center gap-1">⚠️ 100% Similarity Warning</span>
                              <p className="text-amber-300/90 leading-relaxed">
                                These papers have extremely similar extracted concepts/content. Review both papers to determine whether they are duplicates or closely related.
                              </p>
                            </div>
                          )}

                          <div className="space-y-2 text-xs">
                            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-850 flex items-center justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <span className="text-[10px] text-slate-500 font-bold uppercase block">Paper A #{srcId}</span>
                                <span className="font-extrabold text-slate-100 truncate block">{r.source_paper_title}</span>
                              </div>
                              <button onClick={() => setViewingPaperId(srcId)} className="text-indigo-400 hover:underline text-[11px] font-bold shrink-0">View</button>
                            </div>

                            <div className="text-center text-slate-500 font-bold text-sm">↕</div>

                            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-850 flex items-center justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <span className="text-[10px] text-slate-500 font-bold uppercase block">Paper B #{tgtId}</span>
                                <span className="font-extrabold text-slate-100 truncate block">{r.target_paper_title}</span>
                              </div>
                              <button onClick={() => setViewingPaperId(tgtId)} className="text-indigo-400 hover:underline text-[11px] font-bold shrink-0">View</button>
                            </div>
                          </div>

                          {r.shared_concepts && r.shared_concepts.length > 0 && (
                            <div className="pt-2 border-t border-slate-850 space-y-1.5">
                              <span className="text-[10px] text-slate-400 font-bold uppercase block">Shared concepts:</span>
                              <div className="flex flex-wrap gap-1">
                                {r.shared_concepts.map((sc, scIdx) => (
                                  <span key={scIdx} className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-200 text-[10px] font-bold border border-slate-700/60">
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

          {/* TAB 4: CONCEPTS */}
          {activeTab === 'concepts' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex border-b border-slate-800 gap-2 text-xs font-bold overflow-x-auto scrollbar-none">
                {['algorithms', 'datasets', 'methodologies', 'domains', 'keywords'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setConceptCategoryTab(cat)}
                    className={`pb-2.5 px-3.5 transition-all border-b-2 uppercase tracking-wider whitespace-nowrap ${
                      conceptCategoryTab === cat ? 'border-indigo-500 text-indigo-400 font-extrabold' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {cat} ({sharedConcepts[cat] ? sharedConcepts[cat].length : 0})
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {(sharedConcepts[conceptCategoryTab] || []).map((sc, idx) => (
                  <div key={idx} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-extrabold text-slate-100 truncate">{sc.name}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                        sc.classification === 'COMMON' ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      }`}>
                        {sc.classification === 'UNDERREPRESENTED' ? 'Underrepresented within project' : sc.classification}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Coverage: <b className="text-slate-200">{sc.coverage_percentage}%</b></span>
                      <span>Appears in <b className="text-indigo-400">{sc.paper_count}</b> paper(s)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: RESEARCH GAPS (WHAT IS MISSING?) */}
          {activeTab === 'gaps' && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                ⚠️ <b>PROJECT-SCOPED ANALYSIS:</b> Identified research gaps are derived strictly from research papers assigned to this project.
              </div>

              {gaps.length === 0 ? (
                <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
                  No research gaps detected within project scope.
                </div>
              ) : (
                <div className="space-y-4">
                  {gaps.map((g, idx) => (
                    <div key={idx} className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div>
                          <span className="text-[10px] font-mono text-amber-400 font-bold block">Source Paper #{g.source_paper_id}</span>
                          <h4 className="text-sm font-extrabold text-slate-100">{g.source_paper_title}</h4>
                        </div>
                        <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-black">
                          Gap Score {g.gap_score}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-slate-400">Target Concept:</span>
                        <span className="px-2.5 py-1 rounded-lg bg-slate-850 text-indigo-300 font-extrabold border border-slate-750">
                          {g.missing_concept} ({g.concept_type})
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">{g.explanation}</p>

                      <button
                        onClick={() => setExpandedGapId(expandedGapId === g.gap_id ? null : g.gap_id)}
                        className="text-xs text-indigo-400 font-bold hover:underline flex items-center gap-1"
                      >
                        <span>{expandedGapId === g.gap_id ? '▼ Hide Evidence' : '▶ Why was this identified?'}</span>
                      </button>

                      {expandedGapId === g.gap_id && (
                        <div className="p-4 rounded-2xl bg-slate-950 border border-slate-850 space-y-2 text-xs text-slate-400 animate-fade-in">
                          <div className="font-bold text-slate-200">Multi-Signal Evidence Metrics:</div>
                          <ul className="list-disc list-inside space-y-1 text-[11px]">
                            <li>Confidence Rating: <b>{g.confidence}</b></li>
                            <li>Relationship Type: <b>{g.relationship_type}</b></li>
                            <li>Cross-Paper Support: <b>{g.evidence?.cross_paper_support || 'Verified'}</b></li>
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 6: DIRECTIONS */}
          {activeTab === 'directions' && (
            <div className="space-y-6 animate-fade-in">
              {/* Saved Directions Section */}
              {savedDirections.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                    Saved Research Directions ({savedDirections.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {savedDirections.map((sd) => (
                      <div key={sd.id} className="p-5 rounded-3xl bg-purple-950/20 border border-purple-800/40 space-y-3 flex flex-col justify-between">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="text-sm font-extrabold text-slate-100">{sd.title}</h4>
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
                  <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
                    No research directions available. Add more papers to synthesize directions.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {candidateDirections.map((d, idx) => (
                      <div key={idx} className="p-6 rounded-3xl bg-slate-900/80 border border-indigo-900/40 space-y-4">
                        <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-3">
                          <div className="space-y-1">
                            <span className="text-[10px] font-mono text-purple-400 font-bold block">Direction #{d.direction_id}</span>
                            <h4 className="text-base font-extrabold text-slate-100">{d.title}</h4>
                          </div>
                          <span className="px-3 py-1 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30 text-xs font-black shrink-0">
                            {d.confidence} Confidence
                          </span>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed">{d.description}</p>

                        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                          <button
                            onClick={() => handleSaveDirection(d)}
                            disabled={savingDirectionId === d.direction_id}
                            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs transition-all disabled:opacity-50"
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

          {/* TAB 7: PROPOSALS */}
          {activeTab === 'proposals' && (
            <div className="space-y-4 animate-fade-in">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Saved Research Proposals ({proposals.length})
                </h3>
              </div>

              {proposals.length === 0 ? (
                <div className="glass-card p-12 rounded-3xl border border-slate-800 bg-slate-900/50 text-center space-y-4">
                  <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-xl text-slate-400">
                    📝
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-base font-extrabold text-slate-200">No research proposals have been created yet.</h4>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Navigate to the Directions tab to synthesize a proposal draft from actionable research directions.
                    </p>
                  </div>
                  <button onClick={() => handleTabChange('directions')} className="btn-secondary py-2 px-4 text-xs font-bold">
                    Go to Research Directions →
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {proposals.map((prop) => (
                    <div key={prop.id} className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <span className="text-[10px] font-mono text-amber-400 font-bold block">Proposal UUID #{prop.proposal_id.slice(0, 8)}</span>
                            <h4 className="text-base font-extrabold text-slate-100">{prop.title}</h4>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-black shrink-0">
                            v{prop.current_version_number}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pt-1">
                          <span>Status: <b className="text-emerald-400">{prop.status}</b></span>
                          <span>•</span>
                          <span>Mode: <b className="text-indigo-300">{prop.current_version?.generation_mode || 'SYNTHESIZED'}</b></span>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-850 flex flex-wrap items-center justify-between gap-2">
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
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB: RESEARCH PLAN */}
          {activeTab === 'plan' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
                    <span>🧪</span> Project Research Methodology Plan
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Convert candidate research directions into structured implementation, baseline, and experiment execution plans.
                  </p>
                </div>

                <button
                  onClick={() => setPlanningDirId(candidateDirections.length > 0 ? (candidateDirections[0].direction_id || candidateDirections[0].id) : 'dir_1')}
                  className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/20"
                >
                  <span>🧪</span> Build New Research Plan
                </button>
              </div>

              {project.metadata_json && project.metadata_json.saved_research_plan ? (
                <div className="glass-card rounded-3xl p-6 border border-emerald-500/30 bg-slate-900/80 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-bold text-xs">
                      SAVED RESEARCH PLAN
                    </span>
                    <span className="text-xs text-slate-400">
                      Target Direction: <strong className="text-slate-200">{project.metadata_json.saved_research_plan.title}</strong>
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase font-bold">Research Problem:</span>
                      <p className="text-slate-200 font-medium">{project.metadata_json.saved_research_plan.research_problem}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase font-bold">Potential Contribution:</span>
                      <p className="text-indigo-300 font-medium">{project.metadata_json.saved_research_plan.potential_contribution}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => setPlanningDirId(project.metadata_json.saved_research_plan.direction_id || 'dir_1')}
                      className="btn-secondary py-2 px-4 text-xs font-bold"
                    >
                      Open Full Methodology Planner →
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-4">
                  <div className="w-14 h-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto text-2xl">
                    🧪
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-base font-bold text-slate-100">No active research plan saved for this project.</h4>
                    <p className="text-xs text-slate-400 max-w-md mx-auto">
                      Select a candidate direction from your project research map or directions tab and click "Build Research Plan" to generate a complete execution guide.
                    </p>
                  </div>
                  <button
                    onClick={() => setPlanningDirId(candidateDirections.length > 0 ? (candidateDirections[0].direction_id || candidateDirections[0].id) : 'dir_1')}
                    className="btn-primary py-2 px-5 text-xs font-bold"
                  >
                    Generate Plan Now
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB: RESEARCH EXPERIMENT WORKSPACE */}
          {activeTab === 'experiments' && (
            <ResearchExperimentWorkspace
              projectId={projectId}
              directionId={candidateDirections.length > 0 ? (candidateDirections[0].direction_id || candidateDirections[0].id) : 'dir_1'}
            />
          )}

          {/* TAB: RESEARCH RESULTS ANALYSIS */}
          {activeTab === 'results-analysis' && (
            <ResearchResultsAnalysis
              projectId={projectId}
              onOpenExperiments={() => handleTabChange('experiments')}
            />
          )}

          {/* TAB: ACADEMIC MANUSCRIPT WORKSPACE */}
          {(activeTab === 'manuscript' || activeTab === 'academic-paper') && (
            <AcademicManuscriptWorkspace
              projectId={projectId}
            />
          )}

          {/* TAB 8: EVIDENCE TRACEABILITY */}
          {activeTab === 'traceability' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Evidence Traceability Pipeline ({traceability.length})
              </h3>

              {traceability.length === 0 ? (
                <div className="p-8 rounded-3xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
                  No proposal traceability chains available. Draft a proposal to view complete paper-to-version lineage.
                </div>
              ) : (
                <div className="space-y-4">
                  {traceability.map((tr) => (
                    <div key={tr.proposal_id} className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div className="space-y-1">
                          <span className="text-[10px] font-mono text-amber-400 font-bold block">Proposal UUID {tr.proposal_uuid}</span>
                          <h4 className="text-base font-extrabold text-slate-100">{tr.title}</h4>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-black">
                            Version {tr.current_version_number}
                          </span>
                          <button
                            onClick={() => handleOpenSavedProposal(tr.proposal_id)}
                            className="bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold py-1 px-3.5 rounded-xl text-xs shadow-md transition-all"
                          >
                            Open Workspace →
                          </button>
                        </div>
                      </div>

                      {/* TRACEABILITY FLOW */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                        <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-850 space-y-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase block">1. Supporting Papers</span>
                          <div className="space-y-1">
                            {tr.supporting_papers && tr.supporting_papers.map((sp, spIdx) => (
                              <div key={spIdx} className="font-semibold text-indigo-300 hover:underline cursor-pointer truncate" onClick={() => setViewingPaperId(sp.paper_id)}>
                                • {sp.title || `Paper #${sp.paper_id}`}
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-850 space-y-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase block">2. Supporting Concepts</span>
                          <div className="flex flex-wrap gap-1">
                            {tr.supporting_concepts && tr.supporting_concepts.map((sc, scIdx) => (
                              <span key={scIdx} className="px-2 py-0.5 rounded-md bg-slate-900 text-indigo-300 text-[10px] font-semibold">
                                {sc}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-850 space-y-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase block">3. Source Direction</span>
                          <div className="font-mono text-purple-300 font-bold">{tr.source_direction_id || 'dir_1'}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 9: RESEARCH REPORT */}
          {activeTab === 'report' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-slate-900 border border-slate-800">
                <div>
                  <h3 className="text-base font-extrabold text-slate-100">Project Research Report Overview</h3>
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
                <div className="glass-card p-8 rounded-3xl border border-slate-850 bg-slate-950/80 space-y-6 text-xs text-slate-300">
                  <div className="border-b border-slate-800 pb-4 space-y-1">
                    <h2 className="text-xl font-bold text-slate-100">{reportData.title || project.name}</h2>
                    <p className="text-xs text-slate-400">Project ID: #{project.id} • Generated Report</p>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-bold text-indigo-400 uppercase tracking-wider text-[11px]">Research Executive Summary</h4>
                    <p className="leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-850">{reportData.executive_summary}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2 bg-slate-900/60 p-4 rounded-2xl border border-slate-850">
                      <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">Paper Landscape</h4>
                      <p>Total Papers: <b>{reportData.paper_landscape?.length || papers.length}</b></p>
                    </div>
                    <div className="space-y-2 bg-slate-900/60 p-4 rounded-2xl border border-slate-850">
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
        </>
      )}

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
        />
      )}
    </div>
  );
}
