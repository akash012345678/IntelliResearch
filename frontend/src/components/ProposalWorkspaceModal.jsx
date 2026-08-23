import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function ProposalWorkspaceModal({ proposal: initialProposal, proposalId: initialProposalId, onClose, onSelectPaperId }) {
  // Current active proposal content & version metadata
  const [activeProposal, setActiveProposal] = useState(initialProposal || null);
  const [dbProposalId, setDbProposalId] = useState(initialProposalId || null);
  const [activeVersionNumber, setActiveVersionNumber] = useState(1);
  const [versionHistory, setVersionHistory] = useState([]);

  // Copy & Export State
  const [copied, setCopied] = useState(false);
  const [exportingFormat, setExportingFormat] = useState(null);

  // Save to Project Modal State
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [projectsList, setProjectsList] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [savingProposal, setSavingProposal] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  // Edit Mode State
  const [isEditMode, setIsEditMode] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [isChangeSummaryOpen, setIsChangeSummaryOpen] = useState(false);
  const [changeSummaryInput, setChangeSummaryInput] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Version History Drawer & Compare Modal State
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [compareVerA, setCompareVerA] = useState(1);
  const [compareVerB, setCompareVerB] = useState(1);
  const [compareResult, setCompareResult] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [restoring, setRestoring] = useState(false);

  // Load persisted proposal data & version history if proposalId is provided
  useEffect(() => {
    if (initialProposalId) {
      loadPersistedProposal(initialProposalId);
    }
  }, [initialProposalId]);

  const loadPersistedProposal = async (pId) => {
    try {
      const res = await apiService.getProposal(pId);
      setDbProposalId(res.data.id);
      setActiveVersionNumber(res.data.current_version.version_number);
      setActiveProposal(res.data.current_version.proposal_data);
      fetchVersionHistory(res.data.id);
    } catch (err) {
      console.error('Failed to load saved proposal:', err);
    }
  };

  const fetchVersionHistory = async (pId) => {
    try {
      const res = await apiService.getProposalVersions(pId);
      setVersionHistory(res.data.versions || []);
      if (res.data.versions && res.data.versions.length >= 2) {
        setCompareVerA(res.data.versions[res.data.versions.length - 1].version_number);
        setCompareVerB(res.data.versions[0].version_number);
      }
    } catch (err) {
      console.error('Failed to load version history:', err);
    }
  };

  // Enable Edit Mode & Pre-fill Form
  const handleStartEdit = () => {
    if (!activeProposal) return;
    setEditFormData({
      title: activeProposal.title || '',
      abstract: activeProposal.abstract || '',
      problem_statement: activeProposal.problem_statement || '',
      research_motivation: activeProposal.research_motivation || '',
      related_work_synthesis: activeProposal.related_work_synthesis || '',
      research_gap: activeProposal.research_gap || '',
      proposed_methodology: activeProposal.proposed_methodology || '',
      candidate_algorithms: Array.isArray(activeProposal.candidate_algorithms) ? activeProposal.candidate_algorithms.join(', ') : (activeProposal.candidate_algorithms || ''),
      candidate_datasets: Array.isArray(activeProposal.candidate_datasets) ? activeProposal.candidate_datasets.join(', ') : (activeProposal.candidate_datasets || ''),
      dataset_evaluation_plan: activeProposal.dataset_evaluation_plan || '',
      experimental_plan: activeProposal.experimental_plan || '',
      evaluation_metrics: Array.isArray(activeProposal.evaluation_metrics) ? activeProposal.evaluation_metrics.join(', ') : (activeProposal.evaluation_metrics || ''),
      expected_contribution: activeProposal.expected_contribution || '',
      limitations: activeProposal.limitations || '',
    });
    setIsEditMode(true);
  };

  // Handle Save Edit Form Submit
  const handleOpenChangeSummaryModal = (e) => {
    e.preventDefault();
    if (!dbProposalId) {
      alert('Please save this proposal to a research project first before creating new versions.');
      return;
    }
    setChangeSummaryInput('');
    setIsChangeSummaryOpen(true);
  };

  const handleSaveEditSubmit = async (e) => {
    e.preventDefault();
    if (!changeSummaryInput.trim()) {
      alert('Please enter a change summary describing your edits.');
      return;
    }

    setSavingEdit(true);
    try {
      const payload = {
        change_summary: changeSummaryInput.trim(),
        title: editFormData.title.trim() || undefined,
        abstract: editFormData.abstract.trim() || undefined,
        problem_statement: editFormData.problem_statement.trim() || undefined,
        research_motivation: editFormData.research_motivation.trim() || undefined,
        related_work_synthesis: editFormData.related_work_synthesis.trim() || undefined,
        research_gap: editFormData.research_gap.trim() || undefined,
        proposed_methodology: editFormData.proposed_methodology.trim() || undefined,
        candidate_algorithms: editFormData.candidate_algorithms ? editFormData.candidate_algorithms.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
        candidate_datasets: editFormData.candidate_datasets ? editFormData.candidate_datasets.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
        dataset_evaluation_plan: editFormData.dataset_evaluation_plan.trim() || undefined,
        experimental_plan: editFormData.experimental_plan.trim() || undefined,
        evaluation_metrics: editFormData.evaluation_metrics ? editFormData.evaluation_metrics.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
        expected_contribution: editFormData.expected_contribution.trim() || undefined,
        limitations: editFormData.limitations.trim() || undefined,
      };

      const res = await apiService.updateProposal(dbProposalId, payload);
      setActiveVersionNumber(res.data.version_number);
      setActiveProposal(res.data.proposal_data);
      setIsEditMode(false);
      setIsChangeSummaryOpen(false);
      setSaveSuccessMsg(`Saved new Version ${res.data.version_number} successfully!`);
      fetchVersionHistory(dbProposalId);
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err) {
      console.error('Failed to save proposal edit:', err);
      alert('Error saving proposal version: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingEdit(false);
    }
  };

  // Handle Save to Project Modal
  const handleOpenSaveModal = async () => {
    setSaveSuccessMsg(null);
    try {
      const res = await apiService.getProjects();
      setProjectsList(res.data || []);
      if (res.data && res.data.length > 0) {
        setSelectedProjectId(res.data[0].id.toString());
      } else {
        setSelectedProjectId('NEW');
      }
      setIsSaveModalOpen(true);
    } catch (err) {
      console.error('Failed to load projects list:', err);
      alert('Could not fetch projects list.');
    }
  };

  const handleSaveProposalSubmit = async (e) => {
    e.preventDefault();
    setSavingProposal(true);
    try {
      let targetProjectId = selectedProjectId;
      if (selectedProjectId === 'NEW') {
        if (!newProjectTitle.trim()) {
          alert('Please enter a new project name.');
          setSavingProposal(false);
          return;
        }
        const newProjRes = await apiService.createProject({ name: newProjectTitle.trim() });
        targetProjectId = newProjRes.data.id;
      }

      const saveRes = await apiService.saveProposal({
        project_id: parseInt(targetProjectId, 10),
        source_direction_id: activeProposal.source_direction_id || 'dir_1',
        title: activeProposal.title,
        proposal_data: activeProposal,
        generation_mode: activeProposal.generation_mode || 'template',
        status: 'DRAFT'
      });

      setDbProposalId(saveRes.data.id);
      setActiveVersionNumber(1);
      setIsSaveModalOpen(false);
      setSaveSuccessMsg('Proposal saved successfully to project!');
      fetchVersionHistory(saveRes.data.id);
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err) {
      console.error('Failed to save proposal:', err);
      alert('Error saving proposal: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingProposal(false);
    }
  };

  // Handle Selecting a Historical Version
  const handleSelectVersion = async (verNum) => {
    if (!dbProposalId) return;
    try {
      const res = await apiService.getProposalVersion(dbProposalId, verNum);
      setActiveVersionNumber(res.data.version_number);
      setActiveProposal(res.data.proposal_data);
      setIsEditMode(false);
    } catch (err) {
      console.error('Failed to load version:', err);
      alert('Unable to load proposal version.');
    }
  };

  // Handle Restore Version
  const handleRestoreVersion = async (verNum) => {
    if (!dbProposalId) return;
    if (!window.confirm(`Restore Version ${verNum}? Restoring will create a new version entry. Existing versions will not be modified.`)) return;

    setRestoring(true);
    try {
      const res = await apiService.restoreProposalVersion(dbProposalId, verNum);
      setActiveVersionNumber(res.data.version_number);
      setActiveProposal(res.data.proposal_data);
      setIsEditMode(false);
      setSaveSuccessMsg(`Restored Version ${verNum} as new Version ${res.data.version_number}!`);
      fetchVersionHistory(dbProposalId);
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err) {
      console.error('Failed to restore version:', err);
      alert('Unable to restore this version: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRestoring(false);
    }
  };

  // Handle Run Version Comparison
  const handleRunComparison = async () => {
    if (!dbProposalId || compareVerA === compareVerB) return;
    setComparing(true);
    try {
      const res = await apiService.compareProposalVersions(dbProposalId, compareVerA, compareVerB);
      setCompareResult(res.data);
    } catch (err) {
      console.error('Failed to compare versions:', err);
      alert('Unable to compare proposal versions.');
    } finally {
      setComparing(false);
    }
  };

  // Copy & Export Handlers
  const handleCopyText = () => {
    if (!activeProposal) return;
    const fullText = `
TITLE: ${activeProposal.title}
ABSTRACT:
${activeProposal.abstract}

PROBLEM STATEMENT:
${activeProposal.problem_statement}

RESEARCH MOTIVATION:
${activeProposal.research_motivation}

RELATED WORK SYNTHESIS:
${activeProposal.related_work_synthesis}

IDENTIFIED RESEARCH GAP:
${activeProposal.research_gap}

PROPOSED METHODOLOGY:
${activeProposal.proposed_methodology}

CANDIDATE ALGORITHMS:
${Array.isArray(activeProposal.candidate_algorithms) ? activeProposal.candidate_algorithms.join(', ') : activeProposal.candidate_algorithms}

CANDIDATE DATASETS & EVALUATION PLAN:
${Array.isArray(activeProposal.candidate_datasets) ? activeProposal.candidate_datasets.join(', ') : activeProposal.candidate_datasets}
${activeProposal.dataset_evaluation_plan}

EXPERIMENTAL PLAN:
${activeProposal.experimental_plan}

EVALUATION METRICS:
${Array.isArray(activeProposal.evaluation_metrics) ? activeProposal.evaluation_metrics.join(', ') : activeProposal.evaluation_metrics}

EXPECTED CONTRIBUTION:
${activeProposal.expected_contribution}

LIMITATIONS:
${activeProposal.limitations}

DISCLAIMER:
${activeProposal.disclaimer}
    `.trim();

    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handleQuickExport = async (format) => {
    setExportingFormat(format);
    try {
      const response = await apiService.exportResearchDirections(format, 10);
      let filename = `intelliresearch_proposal_v${activeVersionNumber}.${format === 'markdown' ? 'md' : format}`;
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
    } catch (err) {
      console.error('Failed to export proposal:', err);
    } finally {
      setExportingFormat(null);
    }
  };

  if (!activeProposal) return null;
  const ev = activeProposal.evidence_summary || {};

  return (
    <>
      <div className="fixed inset-0 z-[100] overflow-y-auto bg-slate-950/85 backdrop-blur-md flex items-start justify-center pt-20 sm:pt-24 pb-6 px-4 sm:px-6 animate-fade-in">
        <div className="relative w-full max-w-5xl bg-slate-900 border border-indigo-900/40 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[calc(100vh-7rem)]">
          
          {/* WORKSPACE HEADER */}
          <div className="p-6 bg-slate-950/90 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-[10px] font-extrabold uppercase tracking-widest flex items-center gap-1">
                  <span>📑</span> PROPOSAL WORKSPACE
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-extrabold uppercase">
                  Version {activeVersionNumber}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
                  activeProposal.generation_mode === 'llm' ? 'bg-purple-500/10 text-purple-300 border-purple-500/30' :
                  activeProposal.generation_mode === 'manual' ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' :
                  activeProposal.generation_mode === 'restored' ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30' :
                  'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                }`}>
                  {activeProposal.generation_mode === 'llm' ? '🤖 LLM' :
                   activeProposal.generation_mode === 'manual' ? '✏️ Manual Edit' :
                   activeProposal.generation_mode === 'restored' ? '↺ Restored' : '⚡ Template'}
                </span>
              </div>
              <h2 className="text-xl font-extrabold text-slate-100 line-clamp-1">{activeProposal.title}</h2>
              <p className="text-xs text-slate-400">
                Source Direction ID: <span className="font-mono text-indigo-300 font-bold">{activeProposal.source_direction_id || 'dir_1'}</span>
              </p>
            </div>

            {/* ACTION BUTTONS */}
            <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
              {!dbProposalId ? (
                <button
                  onClick={handleOpenSaveModal}
                  className="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs transition-all shadow-md"
                >
                  💾 Save to Project
                </button>
              ) : (
                <>
                  {!isEditMode ? (
                    <button
                      onClick={handleStartEdit}
                      className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all shadow-md flex items-center gap-1"
                    >
                      ✏️ Edit Proposal
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditMode(false)}
                      className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-all"
                    >
                      Cancel Edit
                    </button>
                  )}

                  <button
                    onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs transition-all"
                  >
                    🕒 History ({versionHistory.length})
                  </button>

                  {versionHistory.length >= 2 && (
                    <button
                      onClick={() => {
                        setIsCompareOpen(true);
                        handleRunComparison();
                      }}
                      className="px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-bold text-xs transition-all"
                    >
                      ⚖️ Compare
                    </button>
                  )}
                </>
              )}

              <button onClick={handleCopyText} className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-all border border-slate-700">
                {copied ? '✓ Copied' : '📋 Copy'}
              </button>
              <button onClick={() => handleQuickExport('pdf')} disabled={!!exportingFormat} className="px-3 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-bold transition-all disabled:opacity-50">
                📑 PDF
              </button>
              <button onClick={() => handleQuickExport('md')} disabled={!!exportingFormat} className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-bold transition-all disabled:opacity-50">
                📄 MD
              </button>
              <button onClick={onClose} className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-all font-bold">
                ✕
              </button>
            </div>
          </div>

          {/* SUCCESS BANNER */}
          {saveSuccessMsg && (
            <div className="mx-6 mt-4 p-3 rounded-2xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-bold flex items-center justify-between animate-fade-in">
              <span className="flex items-center gap-2"><span>✓</span> {saveSuccessMsg}</span>
              <button onClick={() => setSaveSuccessMsg(null)} className="text-emerald-400">✕</button>
            </div>
          )}

          {/* HISTORY DRAWER BAR */}
          {isHistoryOpen && dbProposalId && (
            <div className="px-6 py-3 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between gap-4 overflow-x-auto animate-fade-in">
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs font-bold text-slate-300">Version History:</span>
              </div>
              <div className="flex items-center gap-2 overflow-x-auto">
                {versionHistory.map((v) => (
                  <div key={v.id} className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => handleSelectVersion(v.version_number)}
                      className={`px-3 py-1 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                        v.version_number === activeVersionNumber
                          ? 'bg-amber-500 text-slate-950 shadow-md'
                          : 'bg-slate-900 text-slate-300 border border-slate-800 hover:bg-slate-850'
                      }`}
                    >
                      <span>V{v.version_number}</span>
                      <span className="text-[9px] opacity-80 uppercase">({v.generation_mode})</span>
                    </button>
                    {v.version_number !== activeVersionNumber && (
                      <button
                        onClick={() => handleRestoreVersion(v.version_number)}
                        className="px-1.5 py-0.5 rounded-lg bg-slate-850 text-[10px] text-slate-400 hover:text-indigo-300 hover:bg-slate-800"
                        title={`Restore Version ${v.version_number}`}
                      >
                        ↺
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* WORKSPACE BODY */}
          <div className="p-6 overflow-y-auto space-y-6 text-slate-200 text-xs leading-relaxed flex-grow">
            
            {/* EDIT MODE FORM */}
            {isEditMode ? (
              <form onSubmit={handleOpenChangeSummaryModal} className="space-y-6 animate-fade-in">
                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between">
                  <span>✏️ <b>EDIT MODE ACTIVE:</b> Modify structured sections below. Protected empirical evidence fields remain read-only.</span>
                  <button type="submit" className="bg-amber-500 text-slate-950 font-extrabold px-3 py-1 rounded-xl text-xs shadow-md">
                    Save New Version →
                  </button>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 block">Proposal Title</label>
                  <input
                    type="text"
                    value={editFormData.title}
                    onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Executive Abstract</label>
                    <textarea
                      rows={4}
                      value={editFormData.abstract}
                      onChange={(e) => setEditFormData({ ...editFormData, abstract: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Problem Statement</label>
                    <textarea
                      rows={4}
                      value={editFormData.problem_statement}
                      onChange={(e) => setEditFormData({ ...editFormData, problem_statement: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Research Motivation</label>
                    <textarea
                      rows={4}
                      value={editFormData.research_motivation}
                      onChange={(e) => setEditFormData({ ...editFormData, research_motivation: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Related Work Synthesis</label>
                    <textarea
                      rows={4}
                      value={editFormData.related_work_synthesis}
                      onChange={(e) => setEditFormData({ ...editFormData, related_work_synthesis: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Identified Research Gap</label>
                    <textarea
                      rows={3}
                      value={editFormData.research_gap}
                      onChange={(e) => setEditFormData({ ...editFormData, research_gap: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Proposed Methodology</label>
                    <textarea
                      rows={3}
                      value={editFormData.proposed_methodology}
                      onChange={(e) => setEditFormData({ ...editFormData, proposed_methodology: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Candidate Algorithms (Comma separated)</label>
                    <input
                      type="text"
                      value={editFormData.candidate_algorithms}
                      onChange={(e) => setEditFormData({ ...editFormData, candidate_algorithms: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Candidate Datasets (Comma separated)</label>
                    <input
                      type="text"
                      value={editFormData.candidate_datasets}
                      onChange={(e) => setEditFormData({ ...editFormData, candidate_datasets: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Evaluation Metrics (Comma separated)</label>
                    <input
                      type="text"
                      value={editFormData.evaluation_metrics}
                      onChange={(e) => setEditFormData({ ...editFormData, evaluation_metrics: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Experimental Plan</label>
                    <textarea
                      rows={3}
                      value={editFormData.experimental_plan}
                      onChange={(e) => setEditFormData({ ...editFormData, experimental_plan: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-300 block">Expected Contribution</label>
                    <textarea
                      rows={3}
                      value={editFormData.expected_contribution}
                      onChange={(e) => setEditFormData({ ...editFormData, expected_contribution: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-y"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-850">
                  <button type="button" onClick={() => setIsEditMode(false)} className="btn-secondary py-2 px-4 text-xs font-bold">
                    Cancel
                  </button>
                  <button type="submit" className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold py-2 px-5 rounded-xl text-xs shadow-md transition-all">
                    Save New Version →
                  </button>
                </div>
              </form>
            ) : (
              /* READ-ONLY WORKSPACE VIEW */
              <div className="space-y-6 animate-fade-in">
                {/* Abstract & Problem Statement */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📌</span> Executive Abstract
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.abstract}</p>
                  </div>
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>🎯</span> Problem Statement
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.problem_statement}</p>
                  </div>
                </div>

                {/* Motivation & Related Work */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>💡</span> Research Motivation
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.research_motivation}</p>
                  </div>
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📚</span> Related Work Synthesis
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.related_work_synthesis}</p>
                  </div>
                </div>

                {/* Gap & Methodology */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>🔍</span> Identified Research Gap
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.research_gap}</p>
                  </div>
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>⚙️</span> Proposed Methodology
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.proposed_methodology}</p>
                  </div>
                </div>

                {/* Algorithms & Datasets */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-3">
                    <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>⚡</span> Candidate Algorithms
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {Array.isArray(activeProposal.candidate_algorithms) ? activeProposal.candidate_algorithms.map((alg, idx) => (
                        <span key={idx} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
                          {alg}
                        </span>
                      )) : <span className="text-slate-400">{activeProposal.candidate_algorithms}</span>}
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-3">
                    <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📊</span> Candidate Datasets & Plan
                    </h3>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {Array.isArray(activeProposal.candidate_datasets) ? activeProposal.candidate_datasets.map((ds, idx) => (
                        <span key={idx} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
                          {ds}
                        </span>
                      )) : <span className="text-slate-400">{activeProposal.candidate_datasets}</span>}
                    </div>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.dataset_evaluation_plan}</p>
                  </div>
                </div>

                {/* Experimental Plan & Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>🔬</span> Experimental Plan
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.experimental_plan}</p>
                  </div>

                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-3">
                    <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📈</span> Evaluation Metrics
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {Array.isArray(activeProposal.evaluation_metrics) ? activeProposal.evaluation_metrics.map((m, idx) => (
                        <span key={idx} className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-xs font-semibold">
                          {m}
                        </span>
                      )) : <span className="text-slate-400">{activeProposal.evaluation_metrics}</span>}
                    </div>
                  </div>
                </div>

                {/* Contribution & Limitations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>🏆</span> Expected Contribution
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.expected_contribution}</p>
                  </div>
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-2">
                    <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>⚠️</span> Collection Limitations
                    </h3>
                    <p className="text-slate-300 leading-relaxed">{activeProposal.limitations}</p>
                  </div>
                </div>

                {/* Evidence Metrics Summary */}
                <div className="p-5 rounded-2xl bg-slate-950/90 border border-indigo-500/20 space-y-3">
                  <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                    <span>📊</span> Evidence Summary (Protected Evidence Metrics)
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center">
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Gap Score</span>
                      <span className="text-sm font-black text-indigo-400">{ev.gap_score || '0.85'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Semantic Ev.</span>
                      <span className="text-sm font-black text-indigo-400">{ev.semantic_evidence_score || '0.80'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Link Predict.</span>
                      <span className="text-sm font-black text-indigo-400">{ev.link_prediction_score || '0.78'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Underrep.</span>
                      <span className="text-sm font-black text-indigo-400">{ev.underrepresentation_score || '0.92'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Coverage</span>
                      <span className="text-sm font-black text-indigo-400">{ev.collection_coverage || '75%'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">Dir. Score</span>
                      <span className="text-sm font-black text-purple-400">{ev.direction_score || '0.84'}</span>
                    </div>
                  </div>
                </div>

                {/* Supporting Papers */}
                {activeProposal.supporting_papers && activeProposal.supporting_papers.length > 0 && (
                  <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-850 space-y-3">
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📖</span> Supporting Collection Papers ({activeProposal.supporting_papers.length})
                    </h3>
                    <div className="space-y-2">
                      {activeProposal.supporting_papers.map((sp, idx) => (
                        <div
                          key={sp.paper_id || idx}
                          onClick={() => onSelectPaperId && onSelectPaperId(sp.paper_id)}
                          className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 cursor-pointer transition-all flex items-center justify-between gap-3 group"
                        >
                          <div>
                            <span className="text-[10px] font-mono text-indigo-400 font-bold">Paper ID {sp.paper_id}</span>
                            <h6 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300">{sp.title}</h6>
                            <p className="text-[11px] text-slate-400 italic mt-0.5">{sp.role}</p>
                          </div>
                          <span className="text-indigo-400 text-xs font-bold group-hover:underline shrink-0">View Details →</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-850 text-center">
                  <span className="text-[10px] text-slate-500 italic block">{activeProposal.disclaimer}</span>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* CHANGE SUMMARY MODAL */}
      {isChangeSummaryOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 rounded-3xl border border-amber-500/30 bg-slate-950 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>📝</span> Describe Proposal Changes
              </h3>
              <button onClick={() => setIsChangeSummaryOpen(false)} className="text-slate-400 hover:text-white text-sm">✕</button>
            </div>

            <form onSubmit={handleSaveEditSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Change Summary *</label>
                <textarea
                  rows={3}
                  required
                  value={changeSummaryInput}
                  onChange={(e) => setChangeSummaryInput(e.target.value)}
                  placeholder="e.g. Refined research methodology and added YOLOv8 to candidate algorithms."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-amber-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-850">
                <button type="button" onClick={() => setIsChangeSummaryOpen(false)} className="btn-secondary py-1.5 px-3 text-xs font-bold">
                  Cancel
                </button>
                <button type="submit" disabled={savingEdit || !changeSummaryInput.trim()} className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold py-1.5 px-4 rounded-xl text-xs shadow-md transition-all disabled:opacity-50">
                  {savingEdit ? 'Saving Version...' : 'Save New Version'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SAVE TO PROJECT MODAL */}
      {isSaveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 rounded-3xl border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>💾</span> Save Proposal to Project
              </h3>
              <button onClick={() => setIsSaveModalOpen(false)} className="text-slate-400 hover:text-white text-sm">✕</button>
            </div>

            <form onSubmit={handleSaveProposalSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300 block">Select Target Research Project</label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  {projectsList.map((p) => (
                    <option key={p.id} value={p.id.toString()}>
                      {p.name} ({p.status})
                    </option>
                  ))}
                  <option value="NEW">+ Create New Research Project</option>
                </select>
              </div>

              {selectedProjectId === 'NEW' && (
                <div className="space-y-1 animate-fade-in">
                  <label className="text-xs font-semibold text-slate-300 block">New Project Name *</label>
                  <input
                    type="text"
                    required
                    value={newProjectTitle}
                    onChange={(e) => setNewProjectTitle(e.target.value)}
                    placeholder="e.g. Autonomous Vision Systems"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-850">
                <button type="button" onClick={() => setIsSaveModalOpen(false)} className="btn-secondary py-1.5 px-3 text-xs font-bold">
                  Cancel
                </button>
                <button type="submit" disabled={savingProposal} className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold py-1.5 px-4 rounded-xl text-xs shadow-md transition-all disabled:opacity-50">
                  {savingProposal ? 'Saving Proposal...' : 'Save Proposal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* VERSION COMPARISON MODAL */}
      {isCompareOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-4xl p-6 rounded-3xl border border-purple-500/30 bg-slate-950 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>⚖️</span> Compare Proposal Versions
              </h3>
              <button onClick={() => setIsCompareOpen(false)} className="text-slate-400 hover:text-white text-sm">✕</button>
            </div>

            {/* VERSION SELECTORS */}
            <div className="flex items-center gap-4 p-3 rounded-2xl bg-slate-900 border border-slate-800 shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">Version A:</span>
                <select
                  value={compareVerA}
                  onChange={(e) => setCompareVerA(parseInt(e.target.value, 10))}
                  className="px-3 py-1 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100"
                >
                  {versionHistory.map((v) => (
                    <option key={v.id} value={v.version_number}>V{v.version_number} ({v.generation_mode})</option>
                  ))}
                </select>
              </div>

              <span className="text-slate-500 text-xs font-bold">vs</span>

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">Version B:</span>
                <select
                  value={compareVerB}
                  onChange={(e) => setCompareVerB(parseInt(e.target.value, 10))}
                  className="px-3 py-1 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100"
                >
                  {versionHistory.map((v) => (
                    <option key={v.id} value={v.version_number}>V{v.version_number} ({v.generation_mode})</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleRunComparison}
                disabled={comparing || compareVerA === compareVerB}
                className="bg-purple-600 hover:bg-purple-500 text-white font-bold py-1 px-3 rounded-xl text-xs ml-auto shadow-md disabled:opacity-50"
              >
                {comparing ? 'Comparing...' : 'Compare Versions'}
              </button>
            </div>

            {/* DIFF RESULTS */}
            <div className="overflow-y-auto space-y-4 flex-grow pr-1">
              {!compareResult ? (
                <div className="text-center py-8 text-xs text-slate-400">Select two different versions to compare section changes.</div>
              ) : compareResult.total_changes === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">No differences found between Version {compareVerA} and Version {compareVerB}.</div>
              ) : (
                <div className="space-y-4">
                  <div className="text-xs text-slate-400 font-semibold">
                    Found <span className="text-indigo-400 font-bold">{compareResult.total_changes}</span> changed section(s):
                  </div>

                  {compareResult.changes.map((c, idx) => (
                    <div key={idx} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <h4 className="text-xs font-bold text-purple-300 uppercase tracking-wider">{c.section.replace(/_/g, ' ')}</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/20 text-rose-200">
                          <span className="text-[10px] font-bold text-rose-400 block uppercase mb-1">Version {compareVerA} (Before)</span>
                          <p className="whitespace-pre-wrap">{typeof c.before === 'object' ? JSON.stringify(c.before, null, 2) : c.before || 'None'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-emerald-200">
                          <span className="text-[10px] font-bold text-emerald-400 block uppercase mb-1">Version {compareVerB} (After)</span>
                          <p className="whitespace-pre-wrap">{typeof c.after === 'object' ? JSON.stringify(c.after, null, 2) : c.after || 'None'}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
