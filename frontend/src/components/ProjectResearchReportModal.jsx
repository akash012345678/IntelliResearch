import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import api from '../services/api';
import PaperViewModal from './PaperViewModal';
import ProposalWorkspaceModal from './ProposalWorkspaceModal';

const ProjectResearchReportModal = ({ isOpen, onClose, projectId, projectName }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);

  // Traceability Navigation Modals
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [selectedProposalId, setSelectedProposalId] = useState(null);

  // Lock body scroll when report modal is open
  useEffect(() => {
    if (!isOpen) return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && projectId) {
      fetchReport();
    }
  }, [isOpen, projectId]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getProjectResearchReport(projectId);
      setReport(res.data);
    } catch (err) {
      console.error('Failed to load project research report:', err);
      setError('Failed to generate project research report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      setExporting(true);
      const response = await api.exportProjectResearchReport(projectId, format);

      if (format === 'json') {
        const jsonStr = JSON.stringify(response.data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        downloadFile(blob, `Project_${projectId}_Research_Report.json`);
      } else {
        const mimeType = format === 'pdf' ? 'application/pdf' : 'text/markdown';
        const extension = format === 'pdf' ? 'pdf' : 'md';
        const blob = new Blob([response.data], { type: mimeType });
        downloadFile(blob, `Project_${projectId}_Research_Report.${extension}`);
      }
    } catch (err) {
      console.error(`Failed to export report as ${format}:`, err);
      alert(`Export failed for format: ${format.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-4 bg-slate-950/85 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[calc(100vh-7rem)] flex flex-col shadow-2xl overflow-hidden text-slate-100">
        
        {/* Header */}
        <div className="px-6 py-5 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl border border-indigo-500/30">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Project Research Report: <span className="text-indigo-400">{projectName || `Project #${projectId}`}</span>
              </h2>
              <p className="text-xs text-slate-400">Consolidated Academic Research Intelligence & Evidence Traceability</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Export Buttons */}
            {report && (
              <div className="flex items-center space-x-2 mr-2">
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={exporting}
                  className="px-3 py-1.5 bg-red-600/80 hover:bg-red-500 text-white text-xs font-semibold rounded-lg shadow border border-red-500/30 transition flex items-center gap-1.5 disabled:opacity-50"
                  title="Export PDF Report"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export PDF
                </button>
                <button
                  onClick={() => handleExport('markdown')}
                  disabled={exporting}
                  className="px-3 py-1.5 bg-indigo-600/80 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow border border-indigo-500/30 transition flex items-center gap-1.5 disabled:opacity-50"
                  title="Export Markdown Report"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export Markdown
                </button>
                <button
                  onClick={() => handleExport('json')}
                  disabled={exporting}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg border border-slate-600 transition flex items-center gap-1.5 disabled:opacity-50"
                  title="Export JSON Data"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export JSON
                </button>
              </div>
            )}

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-slate-900/90 text-sm">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
              <p className="text-slate-400 text-sm animate-pulse">Generating project research report & evidence traceability...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-950/60 border border-red-800/80 rounded-xl text-red-300 flex items-center gap-3">
              <svg className="w-6 h-6 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          ) : report ? (
            <>
              {/* Section 1: Executive Collection Summary */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
                <h3 className="text-base font-semibold text-indigo-400 flex items-center gap-2">
                  <span>1. Executive Collection Summary</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-white">{report.collection_summary?.total_papers || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Assigned Papers</p>
                  </div>
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-emerald-400">{report.collection_summary?.total_algorithms || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Unique Algorithms</p>
                  </div>
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-cyan-400">{report.collection_summary?.total_datasets || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Unique Datasets</p>
                  </div>
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-amber-400">{report.collection_summary?.total_methodologies || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Methodologies</p>
                  </div>
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-purple-400">{report.collection_summary?.total_domains || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Application Domains</p>
                  </div>
                  <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 text-center">
                    <p className="text-2xl font-bold text-blue-400">{report.collection_summary?.total_keywords || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Keywords</p>
                  </div>
                </div>
              </section>

              {/* Section 2: Research Focus & Problem Summary */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <h3 className="text-base font-semibold text-indigo-400">2. Research Focus & Problem Summary</h3>
                <p className="text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                  {report.research_problem_summary?.summary_text || 'No dominant research problem established.'}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Dominant Domains</span>
                    <span className="text-slate-200">{report.research_problem_summary?.dominant_domains?.join(', ') || 'None'}</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Dominant Methodologies</span>
                    <span className="text-slate-200">{report.research_problem_summary?.dominant_methods?.join(', ') || 'None'}</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Dominant Algorithms</span>
                    <span className="text-slate-200">{report.research_problem_summary?.dominant_algorithms?.join(', ') || 'None'}</span>
                  </div>
                  <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Dominant Themes</span>
                    <span className="text-slate-200">{report.research_problem_summary?.dominant_research_themes?.join(', ') || 'None'}</span>
                  </div>
                </div>
              </section>

              {/* Section 3: Evidence Traceability Chain */}
              <section className="bg-slate-800/40 border border-indigo-500/30 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-indigo-400 flex items-center gap-2">
                    <span>3. Evidence Traceability Chains</span>
                    <span className="text-xs px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/30 font-normal">
                      Paper ➔ Concept ➔ Gap ➔ Direction ➔ Proposal ➔ Version
                    </span>
                  </h3>
                </div>

                <p className="text-xs text-slate-400">
                  Interactive end-to-end evidence derivation. Click on a paper node to view paper metadata or proposal node to open proposal workspace.
                </p>

                <div className="space-y-3">
                  {report.evidence_traceability?.map((chain, idx) => (
                    <div key={idx} className="bg-slate-900/80 p-4 rounded-xl border border-slate-700/80 space-y-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        
                        {/* Paper Node */}
                        <button
                          onClick={() => setSelectedPaperId(chain.paper_id)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-300 font-semibold rounded-lg border border-indigo-500/40 transition flex items-center gap-1.5 shadow"
                        >
                          <span>📄</span>
                          <span className="truncate max-w-[140px]">{chain.paper_title}</span>
                        </button>

                        <span className="text-slate-500 font-bold">➔</span>

                        {/* Concept Node */}
                        <div className="px-3 py-1.5 bg-emerald-950/60 text-emerald-300 rounded-lg border border-emerald-800/60 flex items-center gap-1.5">
                          <span className="text-[10px] uppercase font-bold text-emerald-400">{chain.concept?.type}:</span>
                          <span className="font-medium">{chain.concept?.name}</span>
                        </div>

                        <span className="text-slate-500 font-bold">➔</span>

                        {/* Gap Node */}
                        <div className="px-3 py-1.5 bg-amber-950/60 text-amber-300 rounded-lg border border-amber-800/60 flex items-center gap-1.5">
                          <span className="text-[10px] uppercase font-bold text-amber-400">GAP ({chain.gap?.confidence}):</span>
                          <span className="truncate max-w-[150px]">{chain.gap?.missing_concept}</span>
                        </div>

                        <span className="text-slate-500 font-bold">➔</span>

                        {/* Direction Node */}
                        <div className="px-3 py-1.5 bg-blue-950/60 text-blue-300 rounded-lg border border-blue-800/60 flex items-center gap-1.5">
                          <span className="text-[10px] uppercase font-bold text-blue-400">DIR:</span>
                          <span className="truncate max-w-[150px]">{chain.research_direction?.title}</span>
                        </div>

                        <span className="text-slate-500 font-bold">➔</span>

                        {/* Proposal Node */}
                        {chain.proposal ? (
                          <button
                            onClick={() => setSelectedProposalId(chain.proposal.db_id)}
                            className="px-3 py-1.5 bg-purple-900/60 hover:bg-purple-800/80 text-purple-200 font-semibold rounded-lg border border-purple-500/50 transition flex items-center gap-1.5 shadow"
                          >
                            <span>📝</span>
                            <span className="truncate max-w-[140px]">{chain.proposal.title}</span>
                            <span className="text-[10px] bg-purple-950 px-1.5 py-0.5 rounded text-purple-300">v{chain.proposal.latest_version}</span>
                          </button>
                        ) : (
                          <span className="px-3 py-1.5 bg-slate-800/60 text-slate-500 italic rounded border border-slate-700/40">
                            No Draft Proposal
                          </span>
                        )}

                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Section 4: Assigned Paper Landscape */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
                <h3 className="text-base font-semibold text-indigo-400">4. Assigned Paper Landscape ({report.paper_landscape?.length || 0})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {report.paper_landscape?.map((paper) => (
                    <div key={paper.id} className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/70 space-y-2">
                      <div className="flex items-start justify-between">
                        <h4 className="font-semibold text-white text-sm line-clamp-1">{paper.title}</h4>
                        <button
                          onClick={() => setSelectedPaperId(paper.id)}
                          className="text-xs text-indigo-400 hover:text-indigo-300 shrink-0 ml-2 font-medium"
                        >
                          View Paper ➔
                        </button>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{paper.abstract || 'No abstract available.'}</p>
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {paper.algorithms?.slice(0, 3).map((alg, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-emerald-950/80 text-emerald-300 rounded border border-emerald-800/50">{alg}</span>
                        ))}
                        {paper.datasets?.slice(0, 3).map((ds, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-cyan-950/80 text-cyan-300 rounded border border-cyan-800/50">{ds}</span>
                        ))}
                        {paper.methodologies?.slice(0, 3).map((m, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-950/80 text-amber-300 rounded border border-amber-800/50">{m}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Section 5: Shared Research Concepts */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <h3 className="text-base font-semibold text-indigo-400">5. Shared Research Concepts Across Collection</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  {['algorithms', 'datasets', 'methodologies', 'domains'].map((cat) => (
                    <div key={cat} className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60 space-y-2">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block capitalize">{cat}</span>
                      <div className="flex flex-wrap gap-1">
                        {(report.shared_concepts?.[cat] || []).length > 0 ? (
                          report.shared_concepts[cat].map((c, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 bg-slate-700 text-slate-200 rounded">
                              {typeof c === 'object' ? c.name : c}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-500 italic">None shared</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Section 6: Project Research Gaps & Opportunities */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <h3 className="text-base font-semibold text-indigo-400">6. Project-Scoped Research Gaps ({report.research_gaps?.length || 0})</h3>
                <div className="space-y-2.5">
                  {report.research_gaps?.map((gap, i) => (
                    <div key={i} className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700/80 flex items-start justify-between">
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-200 text-sm">{gap.missing_concept || gap.gap_title}</p>
                        <p className="text-xs text-slate-400">{gap.description || gap.reasoning}</p>
                      </div>
                      <div className="text-right shrink-0 ml-4">
                        <span className="text-xs font-bold text-amber-400 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800/60 block">
                          Score: {gap.gap_score || 0.8}
                        </span>
                        <span className="text-[10px] text-slate-400 mt-1 block">{gap.confidence} Confidence</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Section 7: Candidate Research Directions */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <h3 className="text-base font-semibold text-indigo-400">7. Candidate Research Directions ({report.candidate_research_directions?.length || 0})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {report.candidate_research_directions?.map((dir, i) => (
                    <div key={i} className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/70 space-y-2">
                      <h4 className="font-semibold text-indigo-300 text-sm">{dir.title}</h4>
                      <p className="text-xs text-slate-300 leading-relaxed">{dir.research_motivation || dir.summary}</p>
                      <div className="pt-1 text-[11px] text-slate-400 flex items-center justify-between">
                        <span>Candidate Algo: <strong className="text-slate-200">{dir.candidate_algorithms?.[0] || 'N/A'}</strong></span>
                        <span>Dataset: <strong className="text-slate-200">{dir.candidate_datasets?.[0] || 'N/A'}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Section 8: Saved Proposals & Version Summaries */}
              <section className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
                <h3 className="text-base font-semibold text-indigo-400">8. Saved Proposals & Version Traceability</h3>
                {report.proposal_summary?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-800 text-slate-400 uppercase text-[10px] border-b border-slate-700">
                        <tr>
                          <th className="py-2.5 px-3">Proposal Title</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Latest Version</th>
                          <th className="py-2.5 px-3">Generation Mode</th>
                          <th className="py-2.5 px-3 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {report.proposal_summary.map((prop, i) => (
                          <tr key={i} className="hover:bg-slate-800/50 transition">
                            <td className="py-2.5 px-3 font-medium text-white">{prop.title}</td>
                            <td className="py-2.5 px-3">
                              <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 rounded text-[10px] border border-indigo-800">
                                {prop.status}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-semibold text-purple-400">v{prop.latest_version}</td>
                            <td className="py-2.5 px-3 uppercase text-[10px] text-slate-400">{prop.generation_mode}</td>
                            <td className="py-2.5 px-3 text-right">
                              <button
                                onClick={() => setSelectedProposalId(prop.db_id)}
                                className="text-indigo-400 hover:text-indigo-300 font-semibold"
                              >
                                Open Workspace ➔
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No saved research proposals associated with this project yet.</p>
                )}
              </section>

              {/* Section 9: Collection Scope & Analytical Disclaimers */}
              <section className="bg-indigo-950/30 border border-indigo-800/40 rounded-xl p-4 text-xs text-indigo-200/90 leading-relaxed flex items-start gap-3">
                <svg className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="font-semibold text-indigo-300 mb-1">Scope & Academic Originality Notice</h4>
                  <p>{report.collection_disclaimer}</p>
                </div>
              </section>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-800/80 border-t border-slate-700/80 flex items-center justify-between shrink-0">
          <span className="text-xs text-slate-400">
            IntelliResearch Phase 6 Part 5 Project Research Report Engine
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-xl border border-slate-600 transition shadow"
          >
            Close Report
          </button>
        </div>

      </div>

      {/* Embedded Paper Metadata View Modal */}
      {selectedPaperId && (
        <PaperViewModal
          isOpen={!!selectedPaperId}
          onClose={() => setSelectedPaperId(null)}
          paperId={selectedPaperId}
        />
      )}

      {/* Embedded Proposal Workspace Modal */}
      {selectedProposalId && (
        <ProposalWorkspaceModal
          isOpen={!!selectedProposalId}
          onClose={() => setSelectedProposalId(null)}
          proposalId={selectedProposalId}
        />
      )}
    </div>,
    document.body
  );
};

export default ProjectResearchReportModal;
