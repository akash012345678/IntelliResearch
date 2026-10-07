import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ExperimentDetailModal from './ExperimentDetailModal';

export default function ResearchExperimentWorkspace({ projectId, directionId }) {
  const [summary, setSummary] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [savedDirections, setSavedDirections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState(null);
  const [error, setError] = useState(null);
  const [activeDirId, setActiveDirId] = useState(directionId || 'dir_1');

  // Selected experiment for modal
  const [selectedExp, setSelectedExp] = useState(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Filter states
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Create Form State
  const [newName, setNewName] = useState('');
  const [newPurpose, setNewPurpose] = useState('');
  const [newType, setNewType] = useState('BASELINE_COMPARISON');
  const [newBaseline, setNewBaseline] = useState('');
  const [newProposed, setNewProposed] = useState('');

  useEffect(() => {
    if (directionId) {
      setActiveDirId(directionId);
    }
  }, [directionId]);

  useEffect(() => {
    fetchExperimentData();
    fetchProjectSavedDirections();
  }, [projectId]);

  const fetchProjectSavedDirections = async () => {
    try {
      const res = await apiService.getProjectDirections(projectId);
      setSavedDirections(res.data || []);
      if (!directionId && res.data && res.data.length > 0) {
        setActiveDirId(res.data[0].source_direction_id || 'dir_1');
      }
    } catch (err) {
      console.error('Failed to load project saved directions:', err);
    }
  };

  const fetchExperimentData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const [sumRes, expRes] = await Promise.all([
        apiService.getExperimentSummary(projectId),
        apiService.getProjectExperiments(projectId)
      ]);
      setSummary(sumRes.data);
      setExperiments(expRes.data || []);
    } catch (err) {
      console.error('Failed to load project experiments:', err);
      setError('Unable to load research experiment workspace.');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleExperimentUpdated = (updatedExp) => {
    if (updatedExp) {
      setExperiments(prev => prev.map(e => e.id === updatedExp.id ? updatedExp : e));
      if (updatedExp.status === 'COMPLETED') {
        setImportMessage({ type: 'success', text: `✓ Experiment "${updatedExp.name}" marked as COMPLETED.` });
      }
    }
    fetchExperimentData(false);
  };

  const handleImportPlan = async () => {
    const targetDirId = activeDirId || directionId || 'dir_1';
    setImporting(true);
    setImportMessage(null);
    try {
      const res = await apiService.importMethodologyExperiments(projectId, targetDirId);
      const data = res.data;
      if (data && data.message) {
        setImportMessage({ type: 'success', text: data.message });
      } else {
        setImportMessage({ type: 'success', text: 'Planned experiments imported successfully.' });
      }
      await fetchExperimentData();
    } catch (err) {
      console.error('Failed to import experiments from methodology plan:', err);
      const errDetail = err.response?.data?.detail || 'Failed to import methodology experiments.';
      setImportMessage({ type: 'error', text: errDetail });
    } finally {
      setImporting(false);
    }
  };

  const handleCreateExperiment = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await apiService.createProjectExperiment(projectId, {
        direction_id: activeDirId || directionId || 'dir_1',
        name: newName,
        purpose: newPurpose,
        experiment_type: newType,
        status: 'NOT_STARTED',
        baseline_config: { algorithm: newBaseline },
        proposed_config: { architecture: newProposed },
        execution_config: { origin: 'CUSTOM' }
      });
      setIsCreateOpen(false);
      setNewName('');
      setNewPurpose('');
      setNewBaseline('');
      setNewProposed('');
      fetchExperimentData();
    } catch (err) {
      console.error('Failed to create experiment:', err);
    }
  };

  const filteredExperiments = experiments.filter(e => {
    if (statusFilter !== 'ALL' && e.status !== statusFilter) return false;
    if (typeFilter !== 'ALL' && e.experiment_type !== typeFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return e.name.toLowerCase().includes(q) || (e.purpose && e.purpose.toLowerCase().includes(q));
    }
    return true;
  });

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 mx-auto flex items-center justify-center text-indigo-400 font-bold animate-spin">
          🧪
        </div>
        <p className="text-xs text-slate-400 font-bold">Loading Research Experiment Workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in text-xs text-slate-300">
      
      {/* WORKSPACE HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
              🧪 RESEARCH EXPERIMENT WORKSPACE
            </span>
            {savedDirections.length > 0 && (
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1 text-[11px]">
                <span className="text-slate-400 font-bold">Plan:</span>
                <select
                  value={activeDirId}
                  onChange={(e) => setActiveDirId(e.target.value)}
                  className="bg-transparent font-bold text-indigo-300 outline-none cursor-pointer"
                >
                  {savedDirections.map((sd) => (
                    <option key={sd.id} value={sd.source_direction_id} className="bg-slate-950 text-slate-200">
                      {sd.title} ({sd.source_direction_id})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <h2 className="text-xl font-black text-slate-100">Lab Notebook & Empirical Result Tracker</h2>
          <p className="text-xs text-slate-400">
            Run your experiments externally using Python, PyTorch, Colab, or MATLAB, then record real empirical results here.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleImportPlan}
            disabled={importing}
            className="px-4 py-2 rounded-2xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-bold text-xs transition-all flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>📥</span> {importing ? 'Importing...' : 'Import Planned Experiments'}
          </button>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="btn-primary py-2 px-4 text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-500/20"
          >
            <span>+</span> Create Custom Experiment
          </button>
        </div>
      </div>

      {/* IMPORT NOTIFICATION BANNER */}
      {importMessage && (
        <div className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between transition-all ${
          importMessage.type === 'success' 
            ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300' 
            : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            <span>{importMessage.type === 'success' ? '✓' : '⚠️'}</span>
            <span>{importMessage.text}</span>
          </div>
          <button onClick={() => setImportMessage(null)} className="text-slate-400 hover:text-slate-200 text-xs">✕</button>
        </div>
      )}

      {/* DASHBOARD METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Planned</span>
          <span className="text-xl font-black text-indigo-400">{summary?.total_planned || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Not Started</span>
          <span className="text-xl font-black text-slate-400">{summary?.not_started_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">In Progress</span>
          <span className="text-xl font-black text-amber-400">{summary?.in_progress_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Completed</span>
          <span className="text-xl font-black text-emerald-400">{summary?.completed_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Results Recorded</span>
          <span className="text-xl font-black text-purple-400">{summary?.results_recorded_count || 0}</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase block">Needs Attention</span>
          <span className="text-xl font-black text-rose-400">{summary?.needs_attention_count || 0}</span>
        </div>
      </div>

      {/* FILTER & SEARCH BAR */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search experiments..."
            className="px-3.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none w-48 sm:w-64"
          />

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-xs font-bold outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="NOT_STARTED">NOT_STARTED</option>
              <option value="PLANNED">PLANNED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="NEEDS_ATTENTION">NEEDS_ATTENTION</option>
            </select>
          </div>
        </div>

        <span className="text-[11px] text-slate-400 font-bold">
          Showing {filteredExperiments.length} of {experiments.length} Experiments
        </span>
      </div>

      {/* EXPERIMENTS GRID */}
      {filteredExperiments.length === 0 ? (
        <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto text-2xl">
            🧪
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-bold text-slate-100">No research experiments found.</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Click "Import Planned Experiments" to automatically load experiments from your research methodology plan or create custom experiments manually.
            </p>
          </div>
          <button
            onClick={handleImportPlan}
            disabled={importing}
            className="btn-primary py-2 px-5 text-xs font-bold disabled:opacity-50"
          >
            {importing ? 'Importing...' : 'Import Planned Experiments'}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredExperiments.map((exp, idx) => {
            const runCount = exp.runs?.length || 0;
            const hasResults = exp.runs?.some(r => r.results?.length > 0);
            const origin = exp.execution_config?.origin || (exp.direction_id ? 'PLANNED' : 'CUSTOM');
            const expNum = exp.execution_config?.experiment_number || (idx + 1);

            return (
              <div
                key={exp.id}
                className="glass-card rounded-3xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between space-y-4 bg-slate-900/60"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[10px]">
                        EXP #{expNum}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                        origin === 'PLANNED'
                          ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {origin}
                      </span>
                    </div>

                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                      exp.status === 'COMPLETED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                      exp.status === 'IN_PROGRESS' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                      exp.status === 'NEEDS_ATTENTION' ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' :
                      'bg-slate-800 border-slate-700 text-slate-300'
                    }`}>
                      {exp.status}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <h3 className="text-sm font-extrabold text-slate-100 line-clamp-2">{exp.name}</h3>
                    <p className="text-xs text-slate-400 line-clamp-2">{exp.purpose || 'No purpose description entered.'}</p>
                  </div>

                  {/* PROVENANCE / PLAN ORIGIN INFO */}
                  <div className="text-[10px] text-slate-400 bg-slate-950/40 p-2 rounded-xl border border-slate-850 space-y-1 font-mono">
                    {exp.execution_config?.source_plan_title && (
                      <div className="truncate"><strong className="text-slate-300">Plan:</strong> {exp.execution_config.source_plan_title}</div>
                    )}
                    {exp.direction_id && (
                      <div className="truncate"><strong className="text-slate-300">Opportunity ID:</strong> {exp.direction_id}</div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-950/60 p-2.5 rounded-2xl border border-slate-800">
                    <div>
                      <span className="text-[9px] text-slate-500 font-bold uppercase block">Baseline</span>
                      <span className="font-semibold text-slate-300 truncate block">{exp.baseline_config?.algorithm || 'Not set'}</span>
                    </div>
                    <div>
                      <span className="text-[9px] text-slate-500 font-bold uppercase block">Proposed</span>
                      <span className="font-semibold text-indigo-300 truncate block">{exp.proposed_config?.architecture || 'Not set'}</span>
                    </div>
                  </div>

                  {exp.execution_config?.metrics && exp.execution_config.metrics.length > 0 && (
                    <div className="text-[10px] text-amber-300/90 font-mono truncate">
                      <strong>Metrics:</strong> {Array.isArray(exp.execution_config.metrics) ? exp.execution_config.metrics.join(', ') : exp.execution_config.metrics}
                    </div>
                  )}
                </div>

                <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${hasResults ? 'bg-emerald-400' : 'bg-slate-600'}`}></span>
                    <span className="text-[11px] text-slate-400 font-bold">
                      {hasResults ? `${runCount} Run(s) Recorded` : 'Results not yet recorded'}
                    </span>
                  </div>

                  <button
                    onClick={() => setSelectedExp(exp)}
                    className="btn-secondary py-1.5 px-3.5 text-[11px] font-bold"
                  >
                    Open Experiment →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* CREATE EXPERIMENT MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg glass-card rounded-3xl p-6 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-4">
            <h3 className="text-base font-extrabold text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
              <span>+</span> Create Research Experiment
            </h3>

            <form onSubmit={handleCreateExperiment} className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Experiment Name *</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. EXP-001: Baseline Accuracy Comparison"
                  className="w-full mt-1 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Experiment Purpose</label>
                <textarea
                  value={newPurpose}
                  onChange={(e) => setNewPurpose(e.target.value)}
                  placeholder="Describe what this experiment aims to test or verify..."
                  className="w-full mt-1 p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none h-20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  >
                    <option value="BASELINE_COMPARISON">Baseline Comparison</option>
                    <option value="ABLATION">Ablation Study</option>
                    <option value="DATASET_COMPARISON">Dataset Comparison</option>
                    <option value="HYPERPARAMETER_STUDY">Hyperparameter Study</option>
                    <option value="EFFICIENCY">Efficiency & Latency</option>
                    <option value="CUSTOM">Custom Experiment</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Baseline Method</label>
                  <input
                    type="text"
                    value={newBaseline}
                    onChange={(e) => setNewBaseline(e.target.value)}
                    placeholder="Baseline Model"
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Proposed Architecture / Method</label>
                <input
                  type="text"
                  value={newProposed}
                  onChange={(e) => setNewProposed(e.target.value)}
                  placeholder="Proposed Spatial Transformer"
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 border-t border-slate-800 pt-3">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="btn-secondary py-2 px-4 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary py-2 px-5 text-xs font-bold"
                >
                  Create Experiment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EXPERIMENT DETAIL MODAL */}
      {selectedExp && (
        <ExperimentDetailModal
          experiment={selectedExp}
          projectId={projectId}
          onClose={() => setSelectedExp(null)}
          onRefresh={handleExperimentUpdated}
        />
      )}
    </div>
  );
}
