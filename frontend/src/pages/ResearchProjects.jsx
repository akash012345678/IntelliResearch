import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

export default function ResearchProjects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getProjects();
      setProjects(res.data || []);
    } catch (err) {
      console.error('Failed to load research projects:', err);
      setError('Could not load research projects. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      const res = await apiService.createProject({
        name: name.trim(),
        description: description.trim() || undefined,
        status: 'ACTIVE'
      });
      setIsModalOpen(false);
      setName('');
      setDescription('');
      navigate(`/research-projects/${res.data.id}`);
    } catch (err) {
      console.error('Failed to create project:', err);
      alert('Error creating project: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (projectId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project? Assigned papers will remain in your paper library.')) {
      return;
    }

    try {
      await apiService.deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err) {
      console.error('Failed to delete project:', err);
      alert('Error deleting project: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggleStatus = async (project, e) => {
    e.stopPropagation();
    const newStatus = project.status === 'ACTIVE' ? 'ARCHIVED' : 'ACTIVE';
    try {
      const res = await apiService.updateProject(project.id, { status: newStatus });
      setProjects((prev) => prev.map((p) => (p.id === project.id ? res.data : p)));
    } catch (err) {
      console.error('Failed to update project status:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-slate-950 via-indigo-950/20 to-slate-950">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              PERSISTENCE & MANAGEMENT
            </span>
          </div>
          <h1 className="text-3xl font-black text-slate-100 mt-2 tracking-tight">
            Research Projects
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Organize research papers, preserve evidence-grounded research directions, and manage versioned research proposals under dedicated workspaces.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 px-5 rounded-2xl text-xs flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/20 self-start md:self-auto"
        >
          <svg className="w-4 h-4 text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          + New Research Project
        </button>
      </div>

      {/* ERROR DISPLAY */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchProjects} className="underline font-bold">Retry</button>
        </div>
      )}

      {/* LOADING STATE */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-400 font-medium">Loading research projects...</p>
        </div>
      ) : projects.length === 0 ? (
        /* EMPTY STATE */
        <div className="glass-card p-12 rounded-3xl text-center space-y-4 border border-slate-800">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-200">No Research Projects Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            Create your first research project to organize papers, save actionable research directions, and maintain proposal version history.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1.5 transition-all shadow-md"
          >
            + Create First Project
          </button>
        </div>
      ) : (
        /* PROJECTS GRID */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => navigate(`/research-projects/${project.id}`)}
              className="glass-card p-6 rounded-3xl border border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer flex flex-col justify-between group bg-slate-950/60 hover:bg-slate-950/90 shadow-lg"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-base font-extrabold text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
                    {project.name}
                  </h3>
                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider shrink-0 ${
                      project.status === 'ACTIVE'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {project.status}
                  </span>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 min-h-[2.5rem]">
                  {project.description || 'No description provided.'}
                </p>

                {/* BADGES METRICS */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-850/60 text-center">
                  <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold block">Papers</span>
                    <span className="text-sm font-black text-indigo-400">{project.paper_count}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold block">Directions</span>
                    <span className="text-sm font-black text-purple-400">{project.direction_count}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold block">Proposals</span>
                    <span className="text-sm font-black text-amber-400">{project.proposal_count}</span>
                  </div>
                </div>
              </div>

              {/* CARD FOOTER ACTIONS */}
              <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-850">
                <span className="text-[10px] text-slate-500">
                  Updated {new Date(project.updated_at).toLocaleDateString()}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleToggleStatus(project, e)}
                    className="px-2 py-1 rounded-lg text-[10px] font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                  >
                    {project.status === 'ACTIVE' ? 'Archive' : 'Activate'}
                  </button>
                  <button
                    onClick={(e) => handleDeleteProject(project.id, e)}
                    className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Delete Project"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE PROJECT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 rounded-3xl border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Create Research Project
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white text-lg">✕</button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Project Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Autonomous Vision Systems Research"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summary of research scope, baseline models, and candidate directions..."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-850">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn-secondary py-2 px-4 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !name.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 px-4 rounded-xl text-xs shadow-md transition-all disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
