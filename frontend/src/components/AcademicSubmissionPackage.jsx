import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function AcademicSubmissionPackage({ projectId }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadZip = async () => {
    setDownloading(true);
    try {
      const response = await apiService.downloadSubmissionPackage(projectId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Submission_Package_Project_${projectId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download submission package:', err);
      alert('Failed to download submission package.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6 text-xs text-slate-300">

      {/* HEADER & DOWNLOAD ACTION */}
      <div className="p-6 rounded-3xl bg-indigo-950/30 border border-indigo-500/30 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-base font-black text-slate-100 flex items-center gap-2">
              <span>📦</span> Complete Final Submission Package (.zip)
            </h3>
            <p className="text-xs text-indigo-300/80">
              Bundles all project paper drafts, evidence traceability matrices, reproducibility logs, references, and research reports into a single ZIP archive.
            </p>
          </div>

          <button
            onClick={handleDownloadZip}
            disabled={downloading}
            className="btn-primary py-3 px-6 text-xs font-bold flex items-center gap-2 shadow-xl shadow-indigo-500/20"
          >
            <span>{downloading ? '⏳ Packaging...' : '📦 Download Submission Package (.zip)'}</span>
          </button>
        </div>
      </div>

      {/* SUBMISSION DELIVERABLES TREE STRUCTURE */}
      <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
        <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">ZIP Package Contents Structure</h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-indigo-400 block font-mono">📂 /paper/</span>
            <ul className="space-y-1 text-[11px] text-slate-300 font-mono">
              <li>📄 manuscript.pdf</li>
              <li>📊 manuscript.docx</li>
              <li>📝 manuscript.md</li>
              <li>🔷 manuscript.json</li>
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-emerald-400 block font-mono">📂 /evidence/</span>
            <ul className="space-y-1 text-[11px] text-slate-300 font-mono">
              <li>🟢 evidence_traceability.md</li>
              <li>🧪 experiment_log.md</li>
              <li>⚙ reproducibility.md</li>
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-purple-400 block font-mono">📂 /references/</span>
            <ul className="space-y-1 text-[11px] text-slate-300 font-mono">
              <li>📚 references.md (IEEE/APA)</li>
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-amber-400 block font-mono">📂 /report/</span>
            <ul className="space-y-1 text-[11px] text-slate-300 font-mono">
              <li>📑 research_report.md</li>
            </ul>
          </div>
        </div>
      </div>

    </div>
  );
}
