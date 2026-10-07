import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import SearchBar from '../components/SearchBar';
import PaperCard from '../components/PaperCard';
import PaperViewModal from '../components/PaperViewModal';
import NextResearchStepCard from '../components/NextResearchStepCard';
import ResearchProjectHealth from '../components/ResearchProjectHealth';

export default function Dashboard() {
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [activeProjectAggregate, setActiveProjectAggregate] = useState(null);
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState('semantic');
  const [semanticResults, setSemanticResults] = useState([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticError, setSemanticError] = useState('');

  const [viewingPaperId, setViewingPaperId] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    const cleanQuery = searchQuery.trim();
    if (!cleanQuery) {
      setSemanticResults([]);
      setSemanticError('');
      fetchPapers('');
      return;
    }
    const handler = setTimeout(() => {
      if (searchMode === 'semantic') {
        executeSemanticSearch(cleanQuery);
      } else {
        fetchPapers(cleanQuery);
      }
    }, 300);
    return () => clearTimeout(handler);
  }, [searchQuery, searchMode]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [projRes, papRes] = await Promise.all([
        apiService.getProjects(),
        apiService.getPapers('')
      ]);
      setProjects(projRes.data || []);
      setPapers(papRes.data || []);

      if (projRes.data && projRes.data.length > 0) {
        const activeP = projRes.data[0];
        const aggRes = await apiService.getProjectDashboardAggregate(activeP.id);
        setActiveProjectAggregate(aggRes.data);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPapers = async (query = '') => {
    try {
      const response = await apiService.getPapers(query);
      setPapers(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  const executeSemanticSearch = async (query) => {
    setSemanticLoading(true);
    setSemanticError('');
    try {
      const response = await apiService.semanticSearch(query, 10);
      setSemanticResults(response.data);
    } catch (err) {
      console.error(err);
      setSemanticError('Semantic search failed.');
    } finally {
      setSemanticLoading(false);
    }
  };

  const handleTakeAction = (tab) => {
    if (activeProjectAggregate) {
      navigate(`/research-projects/${activeProjectAggregate.project_id}?tab=${tab}`);
    }
  };

  const handleDeletePaper = async (paperId) => {
    const targetPaper = papers.find((p) => p.id === paperId) || semanticResults.find((p) => (p.id || p.paper_id) === paperId);
    const paperTitle = targetPaper?.title || `Paper #${paperId}`;

    if (!window.confirm(`Are you sure you want to delete "${paperTitle}" from your research library?\n\nThis will remove the paper file, text extractions, and associated project links.`)) {
      return;
    }

    try {
      await apiService.deletePaper(paperId);
      await fetchDashboardData();
      if (searchQuery.trim() && searchMode === 'semantic') {
        executeSemanticSearch(searchQuery.trim());
      }
    } catch (err) {
      console.error('Failed to delete paper:', err);
      alert('Error deleting research paper.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in text-xs text-slate-300">

      {/* HERO BANNER */}
      <div className="glass-card rounded-3xl p-8 border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/60 flex flex-wrap items-center justify-between gap-6 shadow-2xl">
        <div className="space-y-2 max-w-2xl">
          <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px] uppercase tracking-wider">
            IntelliResearch Student Workspace
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
            From Research Papers to a Complete Research Project.
          </h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            IntelliResearch helps students discover research opportunities, validate ideas, plan experiments, analyze evidence, and prepare academic documents.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link to="/research-projects" className="btn-primary py-3 px-6 font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-500/20">
            <span>🗂</span> My Projects ({projects.length})
          </Link>
          <Link to="/papers" className="btn-secondary py-3 px-5 font-bold text-xs flex items-center gap-2">
            <span>📤</span> Upload Papers
          </Link>
        </div>
      </div>

      {/* ACTIVE PROJECT & SMART NEXT STEP */}
      {activeProjectAggregate && (
        <div className="space-y-6">
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-[10px]">
                    ● ACTIVE PROJECT
                  </span>
                  <span className="text-xs text-slate-400">STAGE: <strong>{activeProjectAggregate.current_stage_title}</strong></span>
                </div>
                <h2 className="text-xl font-black text-slate-100">{activeProjectAggregate.project_title}</h2>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Research Progress</span>
                  <span className="text-2xl font-black text-indigo-400">{activeProjectAggregate.progress_percentage}%</span>
                </div>
                <button
                  onClick={() => navigate(`/research-projects/${activeProjectAggregate.project_id}?tab=journey`)}
                  className="btn-primary py-2.5 px-5 font-bold text-xs shadow-md"
                >
                  Continue Research →
                </button>
              </div>
            </div>

            {/* HEALTH METERS */}
            <ResearchProjectHealth health={activeProjectAggregate.health} />
          </div>

          {/* NEXT STEP GUIDANCE CARD */}
          <NextResearchStepCard nextStep={activeProjectAggregate.next_step} onTakeAction={handleTakeAction} />
        </div>
      )}

      {/* RECENT PROJECTS SECTION */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <span>🗂</span> Recent Research Projects ({projects.length})
          </h3>
          <Link to="/research-projects" className="text-xs text-indigo-400 font-bold hover:underline">
            View All Projects →
          </Link>
        </div>

        {projects.length === 0 ? (
          <div className="glass-card rounded-3xl p-8 border border-slate-800 text-center space-y-3 bg-slate-900/40">
            <span className="text-3xl">📁</span>
            <h4 className="text-sm font-bold text-slate-200">No Research Projects Created Yet</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Create your first research project to organize papers, discover gaps, plan experiments, and write academic papers.
            </p>
            <Link to="/research-projects" className="btn-primary py-2.5 px-5 text-xs font-bold inline-block">
              + Create Research Project
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.slice(0, 3).map((proj) => (
              <div key={proj.id} className="glass-card rounded-3xl p-5 border border-slate-800 space-y-3 hover:border-indigo-500/40 transition-all bg-slate-900/60">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-slate-300 font-bold text-[10px]">
                    {proj.status}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">ID #{proj.id}</span>
                </div>

                <h4 className="text-sm font-bold text-slate-100 truncate">{proj.name}</h4>
                <p className="text-xs text-slate-400 line-clamp-2">{proj.description || 'No description provided.'}</p>

                <div className="flex items-center justify-between border-t border-slate-800/80 pt-3 text-[11px]">
                  <span className="text-slate-400 font-medium">📄 {proj.papers ? proj.papers.length : 0} Papers</span>
                  <button
                    onClick={() => navigate(`/research-projects/${proj.id}?tab=journey`)}
                    className="text-indigo-400 font-bold hover:underline"
                  >
                    Open Project →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* GLOBAL RESEARCH LIBRARY SECTION */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-0.5">
            <h3 className="text-sm font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <span>📚</span> Global Research Paper Collection ({papers.length})
            </h3>
            <p className="text-[11px] text-slate-400">Search and analyze indexed literature papers in your repository.</p>
          </div>

          <SearchBar
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            searchMode={searchMode}
            setSearchMode={setSearchMode}
          />
        </div>

        {/* PAPER CARDS GRID */}
        {searchMode === 'semantic' && searchQuery.trim() ? (
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-indigo-300">Semantic Relevance Search Results ({semanticResults.length})</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {semanticResults.map((item) => (
                <PaperCard
                  key={item.paper_id || item.id}
                  paper={item}
                  isSemantic={true}
                  onView={() => setViewingPaperId(item.paper_id || item.id)}
                  onDelete={handleDeletePaper}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {papers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                onView={() => setViewingPaperId(paper.id)}
                onDelete={handleDeletePaper}
              />
            ))}
          </div>
        )}
      </div>

      {/* PAPER VIEW MODAL */}
      {viewingPaperId && (
        <PaperViewModal
          paperId={viewingPaperId}
          onClose={() => setViewingPaperId(null)}
        />
      )}

    </div>
  );
}
