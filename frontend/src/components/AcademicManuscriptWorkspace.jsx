import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import ClaimEvidencePanel from './ClaimEvidencePanel';
import ReferenceManager from './ReferenceManager';
import AcademicQualityPanel from './AcademicQualityPanel';
import ManuscriptReviewChecklist from './ManuscriptReviewChecklist';
import AcademicDocumentSettings from './AcademicDocumentSettings';
import AcademicDocumentValidator from './AcademicDocumentValidator';
import AcademicDocumentPreview from './AcademicDocumentPreview';
import AcademicSubmissionPackage from './AcademicSubmissionPackage';
import PaperViewModal from './PaperViewModal';

export default function AcademicManuscriptWorkspace({ projectId }) {
  const [manuscript, setManuscript] = useState(null);
  const [references, setReferences] = useState([]);
  const [qualityData, setQualityData] = useState(null);
  const [validationData, setValidationData] = useState(null);
  const [previewData, setPreviewData] = useState(null);

  const [docConfig, setDocConfig] = useState({
    profile: 'COLLEGE_PROJECT',
    page_size: 'A4',
    margins: 'NORMAL',
    font_family: 'Times New Roman',
    font_size: 12,
    line_spacing: 1.5,
    citation_style: 'IEEE',
    student_name: '',
    register_number: '',
    institution: '',
    show_evidence_badges: true
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSectionKey, setActiveSectionKey] = useState('TITLE');
  const [sections, setSections] = useState([]);
  const [filterLevel, setFilterLevel] = useState('ALL');
  const [activeTabMode, setActiveTabMode] = useState('editor'); // 'editor' | 'references' | 'quality' | 'checklist' | 'formatting' | 'preview' | 'package'
  const [viewingPaperId, setViewingPaperId] = useState(null);

  const [savingVersion, setSavingVersion] = useState(false);
  const [changeSummary, setChangeSummary] = useState('');
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  useEffect(() => {
    fetchWorkspaceData();
  }, [projectId]);

  const fetchWorkspaceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [manuRes, refRes, qualRes, valRes, prevRes] = await Promise.all([
        apiService.getProjectManuscript(projectId),
        apiService.getManuscriptCitations(projectId),
        apiService.getManuscriptQuality(projectId),
        apiService.validateAcademicDocument(projectId),
        apiService.getDocumentPreview(projectId, docConfig),
      ]);
      setManuscript(manuRes.data);
      setSections(manuRes.data.sections || []);
      setReferences(refRes.data || []);
      setQualityData(qualRes.data);
      setValidationData(valRes.data);
      setPreviewData(prevRes.data);

      if (manuRes.data.sections && manuRes.data.sections.length > 0) {
        setActiveSectionKey(manuRes.data.sections[0].section_key);
      }
    } catch (err) {
      console.error('Failed to load project manuscript workspace:', err);
      setError('Unable to load academic manuscript workspace.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = async (newConfig) => {
    setDocConfig(newConfig);
    try {
      const res = await apiService.getDocumentPreview(projectId, newConfig);
      setPreviewData(res.data);
    } catch (err) {
      console.error('Failed to update preview layout:', err);
    }
  };

  const handleRegenerate = async () => {
    if (!window.confirm('Re-generating manuscript will refresh draft text from current project evidence. Continue?')) return;
    setLoading(true);
    try {
      const res = await apiService.generateProjectManuscript(projectId);
      setManuscript(res.data);
      setSections(res.data.sections || []);
    } catch (err) {
      console.error('Failed to regenerate manuscript:', err);
      alert('Failed to regenerate manuscript.');
    } finally {
      setLoading(false);
    }
  };

  const handleSectionTextChange = (key, newContent) => {
    setSections(prev => prev.map(s => {
      if (s.section_key === key) {
        return { ...s, content: newContent, is_edited: true };
      }
      return s;
    }));
  };

  const handleSaveNewVersion = async () => {
    setSavingVersion(true);
    try {
      const payload = {
        title: manuscript?.title || 'Academic Manuscript',
        sections: sections,
        change_summary: changeSummary || 'Manual student manuscript revisions'
      };
      const res = await apiService.saveManuscriptVersion(projectId, payload);
      setManuscript(res.data);
      setSections(res.data.sections || []);
      setShowVersionModal(false);
      setChangeSummary('');
      alert(`Successfully saved Version ${res.data.current_version_number}!`);
    } catch (err) {
      console.error('Failed to save manuscript version:', err);
      alert('Failed to save manuscript version.');
    } finally {
      setSavingVersion(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await apiService.exportManuscript(projectId, format);
      const data = res.data;
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `${data.filename || 'manuscript'}.json`);
      } else {
        const blob = new Blob([data.content], { type: 'text/markdown' });
        downloadBlob(blob, data.filename || `Manuscript_Project_${projectId}.md`);
      }
      setShowExportModal(false);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export manuscript.');
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 mx-auto flex items-center justify-center text-indigo-400 font-bold animate-spin">
          📄
        </div>
        <p className="text-xs text-slate-400 font-bold">Auditing Document Formatting & Packaging Deliverables...</p>
      </div>
    );
  }

  const activeSection = sections.find(s => s.section_key === activeSectionKey) || sections[0];
  const completeness = manuscript?.completeness || { overall_percentage: 0, rating_label: 'DRAFT' };
  const filteredSections = sections.filter(s => filterLevel === 'ALL' || s.evidence_level === filterLevel);

  return (
    <div className="space-y-6 animate-fade-in text-xs text-slate-300">

      {/* ACADEMIC INTEGRITY BANNER */}
      <div className="p-4 rounded-3xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">🎓</span>
          <div>
            <h4 className="font-extrabold text-xs">EVIDENCE-GROUNDED ACADEMIC MANUSCRIPT & SUBMISSION SUITE</h4>
            <p className="text-[11px] text-indigo-300/80">{manuscript?.academic_integrity_notice}</p>
          </div>
        </div>
      </div>

      {/* HEADER & TOP CONTROLS */}
      <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
                📄 ACADEMIC MANUSCRIPT (VERSION {manuscript?.current_version_number || 1})
              </span>
              <span className="text-xs text-slate-400">STATUS: <strong>{manuscript?.status || 'DRAFT'}</strong></span>
            </div>
            <h2 className="text-xl font-black text-slate-100">{manuscript?.title || 'Academic Manuscript'}</h2>
          </div>

          {/* COMPLETENESS SCORE GAUGE */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Evidence Completeness</span>
              <span className="text-2xl font-black text-emerald-400">{completeness.overall_percentage}%</span>
              <span className="text-[10px] font-mono text-emerald-300 font-bold block">{completeness.rating_label}</span>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleRegenerate}
                className="px-3 py-2 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5"
              >
                <span>✨</span> Re-generate
              </button>
              <button
                onClick={() => setShowVersionModal(true)}
                className="btn-secondary py-2 px-3 text-xs font-bold flex items-center gap-1.5"
              >
                <span>💾</span> Save Version
              </button>
              <button
                onClick={() => setShowExportModal(true)}
                className="btn-primary py-2 px-4 text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-500/20"
              >
                <span>📥</span> Export Manuscript
              </button>
            </div>
          </div>
        </div>

        {/* WORKSPACE SUB-TAB NAVIGATION */}
        <div className="flex flex-wrap border-b border-slate-800 gap-4 text-xs font-bold">
          <button
            onClick={() => setActiveTabMode('editor')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'editor' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📝</span> Manuscript Editor
          </button>

          <button
            onClick={() => setActiveTabMode('references')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'references' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📚</span> References ({references.length})
          </button>

          <button
            onClick={() => setActiveTabMode('quality')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'quality' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>⚠️</span> Quality Audit {qualityData?.issues?.length > 0 && `(${qualityData.issues.length})`}
          </button>

          <button
            onClick={() => setActiveTabMode('formatting')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'formatting' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📐</span> Formatting Settings
          </button>

          <button
            onClick={() => setActiveTabMode('preview')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'preview' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>👁️</span> Document Preview
          </button>

          <button
            onClick={() => setActiveTabMode('package')}
            className={`pb-2 transition-all border-b-2 flex items-center gap-1.5 ${
              activeTabMode === 'package' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📦</span> Submission Package (.zip)
          </button>
        </div>
      </div>

      {/* MODE 1: 29-SECTION MANUSCRIPT EDITOR */}
      {activeTabMode === 'editor' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            {/* LEFT SIDEBAR SECTION NAVIGATION */}
            <div className="lg:col-span-4 glass-card rounded-3xl p-4 border border-slate-800 space-y-3 bg-slate-900/60 max-h-[80vh] overflow-y-auto custom-scrollbar">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">29 Manuscript Sections</h3>
                <select
                  value={filterLevel}
                  onChange={(e) => setFilterLevel(e.target.value)}
                  className="px-2 py-1 rounded-xl bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-bold"
                >
                  <option value="ALL">All Badges</option>
                  <option value="RECORDED">🟢 Recorded</option>
                  <option value="DERIVED">🟡 Derived</option>
                  <option value="PROPOSED">🔵 Proposed</option>
                  <option value="MISSING">🔴 Missing</option>
                </select>
              </div>

              <div className="space-y-1">
                {filteredSections.map((s) => {
                  const isActive = s.section_key === activeSectionKey;
                  return (
                    <button
                      key={s.section_key}
                      onClick={() => setActiveSectionKey(s.section_key)}
                      className={`w-full text-left p-2.5 rounded-2xl border transition-all flex items-center justify-between gap-2 ${
                        isActive ? 'bg-indigo-600/20 border-indigo-500/60 text-indigo-200 font-bold shadow-md' :
                        'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                      }`}
                    >
                      <span className="truncate font-semibold">{s.title}</span>
                      <span className="text-[10px] font-mono shrink-0">{s.evidence_badge_text.split(' ')[0]}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* MAIN SECTION CONTENT PANE */}
            <div className="lg:col-span-8 glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
              {activeSection ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase block">{activeSection.student_label}</span>
                      <h3 className="text-lg font-black text-slate-100">{activeSection.title}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-full text-[11px] font-extrabold border ${
                        activeSection.evidence_level === 'RECORDED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        activeSection.evidence_level === 'DERIVED' ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' :
                        activeSection.evidence_level === 'PROPOSED' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                        'bg-rose-500/10 border-rose-500/30 text-rose-400'
                      }`}>
                        {activeSection.evidence_badge_text}
                      </span>
                    </div>
                  </div>

                  {/* EDITOR TEXTAREA */}
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-400 font-bold uppercase block">Section Text (Editable Draft)</label>
                    <textarea
                      value={activeSection.content}
                      onChange={(e) => handleSectionTextChange(activeSection.section_key, e.target.value)}
                      rows={10}
                      className="w-full p-4 rounded-2xl bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono leading-relaxed focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none custom-scrollbar"
                    />
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500">Select a section to view and edit content.</div>
              )}
            </div>

          </div>

          <ClaimEvidencePanel activeSection={activeSection} onViewPaper={(id) => setViewingPaperId(id)} />
        </div>
      )}

      {/* MODE 2: REFERENCE MANAGER */}
      {activeTabMode === 'references' && (
        <ReferenceManager
          references={references}
          citationStyle={docConfig.citation_style}
          onStyleChange={(st) => handleConfigChange({ ...docConfig, citation_style: st })}
          onViewPaper={(id) => setViewingPaperId(id)}
        />
      )}

      {/* MODE 3: ACADEMIC QUALITY AUDIT */}
      {activeTabMode === 'quality' && (
        <div className="space-y-6">
          <AcademicQualityPanel qualityData={qualityData} />
          <AcademicDocumentValidator validationData={validationData} onRevalidate={fetchWorkspaceData} />
          <ManuscriptReviewChecklist />
        </div>
      )}

      {/* MODE 4: FORMATTING SETTINGS */}
      {activeTabMode === 'formatting' && (
        <AcademicDocumentSettings config={docConfig} onConfigChange={handleConfigChange} />
      )}

      {/* MODE 5: DOCUMENT PREVIEW */}
      {activeTabMode === 'preview' && (
        <AcademicDocumentPreview previewData={previewData} />
      )}

      {/* MODE 6: SUBMISSION PACKAGE */}
      {activeTabMode === 'package' && (
        <AcademicSubmissionPackage projectId={projectId} />
      )}

      {/* SAVE VERSION MODAL */}
      {showVersionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="w-full max-w-md glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-950 text-xs">
            <h3 className="text-base font-black text-slate-100">Save Manuscript Version</h3>
            <div className="space-y-2">
              <label className="text-slate-400 font-bold block">Change Summary</label>
              <input
                type="text"
                placeholder="e.g. Revised literature review and empirical results interpretation"
                value={changeSummary}
                onChange={(e) => setChangeSummary(e.target.value)}
                className="w-full p-3 rounded-2xl bg-slate-900 border border-slate-800 text-slate-200 text-xs outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowVersionModal(false)} className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 font-bold">
                Cancel
              </button>
              <button onClick={handleSaveNewVersion} disabled={savingVersion} className="btn-primary py-2 px-5 font-bold">
                {savingVersion ? 'Saving...' : 'Save Version'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EXPORT MODAL */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="w-full max-w-md glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-950 text-xs">
            <h3 className="text-base font-black text-slate-100">Export Academic Manuscript</h3>
            <div className="grid grid-cols-2 gap-3 pt-2">
              <button onClick={() => handleExport('markdown')} className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1">
                <span className="text-base font-black block">📝 Markdown (.md)</span>
              </button>
              <button onClick={() => handleExport('pdf')} className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1">
                <span className="text-base font-black block">📄 Academic PDF (.pdf)</span>
              </button>
              <button onClick={() => handleExport('docx')} className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1">
                <span className="text-base font-black block">📊 Word DOCX (.docx)</span>
              </button>
              <button onClick={() => handleExport('json')} className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1">
                <span className="text-base font-black block">🔷 JSON (.json)</span>
              </button>
            </div>
            <div className="flex justify-end pt-2">
              <button onClick={() => setShowExportModal(false)} className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 font-bold">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

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
