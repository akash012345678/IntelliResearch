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
import StudentHelpTooltip from './StudentHelpTooltip';

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
  const [exportingFormat, setExportingFormat] = useState(null);

  // Version Restore & Compare States
  const [versions, setVersions] = useState([]);
  const [compareV1, setCompareV1] = useState(1);
  const [compareV2, setCompareV2] = useState(1);
  const [compareResult, setCompareResult] = useState(null);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [loadingCompare, setLoadingCompare] = useState(false);

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
      setVersions(manuRes.data.available_versions || []);
      setReferences(refRes.data || []);
      setQualityData(qualRes.data);
      setValidationData(valRes.data);
      setPreviewData(prevRes.data);

      if (manuRes.data.available_versions && manuRes.data.available_versions.length > 0) {
        setCompareV1(manuRes.data.available_versions[manuRes.data.available_versions.length - 1].version_number);
        setCompareV2(manuRes.data.current_version_number);
      }

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
      setVersions(res.data.available_versions || []);
      alert('Manuscript successfully regenerated from project evidence!');
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
      setVersions(res.data.available_versions || []);
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

  const handleRestoreVersion = async (vNum) => {
    if (!window.confirm(`Restore Version ${vNum} as a new active version?`)) return;
    setLoading(true);
    try {
      const res = await apiService.restoreManuscriptVersion(projectId, vNum);
      setManuscript(res.data);
      setSections(res.data.sections || []);
      setVersions(res.data.available_versions || []);
      alert(`Successfully restored Version ${vNum} as Version ${res.data.current_version_number}!`);
    } catch (err) {
      console.error('Failed to restore version:', err);
      alert('Failed to restore version.');
    } finally {
      setLoading(false);
    }
  };

  const handleCompareVersions = async () => {
    setLoadingCompare(true);
    try {
      const res = await apiService.compareManuscriptVersions(projectId, compareV1, compareV2);
      setCompareResult(res.data);
      setShowCompareModal(true);
    } catch (err) {
      console.error('Failed to compare versions:', err);
      alert('Failed to compare versions.');
    } finally {
      setLoadingCompare(false);
    }
  };

  const handleExport = async (format) => {
    setExportingFormat(format);
    try {
      const res = await apiService.exportManuscript(projectId, format);
      if (format === 'pdf' || format === 'docx') {
        const blob = new Blob([res.data], {
          type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        });
        downloadBlob(blob, `Academic_Manuscript_Project_${projectId}.${format}`);
      } else if (format === 'json') {
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `Academic_Manuscript_Project_${projectId}.json`);
      } else {
        const blob = new Blob([res.data.content || ''], { type: 'text/markdown' });
        downloadBlob(blob, res.data.filename || `Academic_Manuscript_Project_${projectId}.md`);
      }
      setShowExportModal(false);
    } catch (err) {
      console.error('Export failed:', err);
      alert(`Failed to export manuscript in ${format.toUpperCase()} format.`);
    } finally {
      setExportingFormat(null);
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
        <p className="text-xs text-slate-400 font-bold">Synthesizing 44 Academic Sections & Verifying Evidence Traceability...</p>
      </div>
    );
  }

  const activeSection = sections.find(s => s.section_key === activeSectionKey) || sections[0];
  const completeness = manuscript?.completeness || { overall_percentage: 0, rating_label: 'DRAFT' };
  const filteredSections = sections.filter(s => filterLevel === 'ALL' || s.evidence_level === filterLevel);

  const getDisplayTitle = (s) => {
    if (!s) return "";
    const secNum = (s.section_number || "").trim();
    let title = (s.title || "").trim();
    
    // Strip duplicate section number prefix if present
    if (secNum && title.startsWith(secNum)) {
      title = title.substring(secNum.length).trim();
    }
    title = title.replace(/^(?:\d+(?:\.\d+)?\.?|\bREF\b|\bAPP\b)\s*/, "").trim();

    if (!secNum || secNum === "REF" || secNum === "APP") {
      return title;
    }
    if (!secNum.includes(".")) {
      return `${secNum}. ${title}`;
    }
    return `${secNum} ${title}`;
  };

  // Group sections by chapter
  const chapterGroups = filteredSections.reduce((acc, sec) => {
    const ch = sec.chapter_title || 'FRONT MATTER';
    if (!acc[ch]) acc[ch] = [];
    acc[ch].push(sec);
    return acc;
  }, {});

  return (
    <div className="space-y-6 animate-fade-in text-xs text-slate-300">

      {/* ACADEMIC INTEGRITY BANNER */}
      <div className="p-4 rounded-3xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">🎓</span>
          <div>
            <h4 className="font-extrabold text-xs">EVIDENCE-GROUNDED ACADEMIC PAPER & THESIS SUITE</h4>
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
                📄 ACADEMIC THESIS (VERSION {manuscript?.current_version_number || 1})
              </span>
              <span className="text-xs text-slate-400">STATUS: <strong className="text-emerald-400">{manuscript?.status || 'DRAFT'}</strong></span>
            </div>
            <h2 className="text-xl font-black text-slate-100">{manuscript?.title || 'Academic Manuscript'}</h2>
          </div>

          {/* DUAL COMPLETENESS SCORE GAUGES */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-5 bg-slate-950/70 px-4 py-2.5 rounded-2xl border border-slate-800 shadow-inner">
              {/* MANUSCRIPT COMPLETION SCORE */}
              <div className="text-right border-r border-slate-800 pr-5">
                <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center justify-end gap-1">
                  Manuscript Completion
                  <StudentHelpTooltip
                    title="Manuscript Completion Score"
                    explanation="Measures whether the required academic sections have been meaningfully drafted. Proposed or planned sections may be complete as a draft but are not necessarily evidence-verified."
                  />
                </span>
                <span className="text-2xl font-black text-indigo-400">
                  {completeness.manuscript_completion_percentage ?? completeness.overall_percentage}%
                </span>
                <span className="text-[10px] font-mono text-indigo-300 font-bold block">
                  {completeness.manuscript_completion_label ?? completeness.rating_label}
                </span>
              </div>

              {/* EVIDENCE COMPLETENESS SCORE */}
              <div className="text-right">
                <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center justify-end gap-1">
                  Evidence Completeness
                  <StudentHelpTooltip
                    title="Evidence Completeness Score"
                    explanation="Measures the extent to which manuscript claims and empirical content are supported by verified project evidence and recorded experimental results."
                  />
                </span>
                <span className="text-2xl font-black text-emerald-400">
                  {completeness.evidence_completeness_percentage ?? completeness.overall_percentage}%
                </span>
                <span className="text-[10px] font-mono text-emerald-300 font-bold block">
                  {completeness.evidence_rating_label ?? completeness.rating_label}
                </span>
              </div>
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
                <span>💾</span> Version History ({versions.length})
              </button>
              <button
                onClick={() => setShowExportModal(true)}
                className="btn-primary py-2 px-4 text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-500/20"
              >
                <span>📥</span> Export Thesis
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
            <span>📝</span> Paper Editor ({sections.length} Sections)
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

      {/* MODE 1: 44-SECTION MANUSCRIPT EDITOR */}
      {activeTabMode === 'editor' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            {/* LEFT SIDEBAR SECTION NAVIGATION (BY CHAPTER) */}
            <div className="lg:col-span-4 glass-card rounded-3xl p-4 border border-slate-800 space-y-3 bg-slate-900/60 max-h-[80vh] overflow-y-auto custom-scrollbar">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">Academic Structure</h3>
                <select
                  value={filterLevel}
                  onChange={(e) => setFilterLevel(e.target.value)}
                  className="px-2 py-1 rounded-xl bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-bold"
                >
                  <option value="ALL">All Badges</option>
                  <option value="RECORDED_EVIDENCE">🟢 Recorded DB</option>
                  <option value="EXPERIMENTAL_RESULT">📊 Result DB</option>
                  <option value="DERIVED">🟡 Derived</option>
                  <option value="PROPOSED">🔵 Proposed</option>
                  <option value="MISSING">🔴 Missing</option>
                </select>
              </div>

              <div className="space-y-4">
                {Object.entries(chapterGroups).map(([chTitle, chSections]) => (
                  <div key={chTitle} className="space-y-1">
                    <h4 className="text-[10px] font-extrabold text-indigo-300 uppercase tracking-wider px-2 py-1 bg-indigo-950/40 rounded-xl border border-indigo-500/20">
                      {chTitle}
                    </h4>
                    {chSections.map((s) => {
                      const isActive = s.section_key === activeSectionKey;
                      const badgeIcon = (s.evidence_level === 'RECORDED_EVIDENCE' || s.evidence_level === 'RECORDED') ? '🟢' :
                                       (s.evidence_level === 'EXPERIMENTAL_RESULT' || s.evidence_level === 'RESULT') ? '📊' :
                                       (s.evidence_level === 'DERIVED' || s.evidence_level === 'PARTIALLY_SUPPORTED') ? '🟡' :
                                       s.evidence_level === 'PROPOSED' ? '🔵' : '🔴';

                      return (
                        <button
                          key={s.section_key}
                          onClick={() => setActiveSectionKey(s.section_key)}
                          className={`w-full text-left p-2 rounded-xl border transition-all flex items-center justify-between gap-2 ${
                            isActive ? 'bg-indigo-600/20 border-indigo-500/60 text-indigo-200 font-bold shadow-md' :
                            'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                          }`}
                        >
                          <span className="truncate font-medium text-[11px]">{getDisplayTitle(s)}</span>
                          <span className="text-[10px] font-mono shrink-0">{badgeIcon}</span>
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            {/* MAIN SECTION CONTENT PANE */}
            <div className="lg:col-span-8 glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
              {activeSection ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase block">{activeSection.chapter_title} &bull; {activeSection.student_label}</span>
                      <h3 className="text-lg font-black text-slate-100">{getDisplayTitle(activeSection)}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-full text-[11px] font-extrabold border ${
                        (activeSection.evidence_level === 'RECORDED_EVIDENCE' || activeSection.evidence_level === 'RECORDED') ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        (activeSection.evidence_level === 'EXPERIMENTAL_RESULT' || activeSection.evidence_level === 'RESULT') ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' :
                        (activeSection.evidence_level === 'DERIVED' || activeSection.evidence_level === 'PARTIALLY_SUPPORTED') ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                        activeSection.evidence_level === 'PROPOSED' ? 'bg-sky-500/10 border-sky-500/30 text-sky-300' :
                        'bg-rose-500/10 border-rose-500/30 text-rose-400'
                      }`}>
                        {activeSection.evidence_badge_text || activeSection.evidence_level}
                      </span>
                    </div>
                  </div>

                  {/* EDITOR TEXTAREA */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-[10px] text-slate-400 font-bold uppercase block">Section Text (Editable Academic Draft)</label>
                      {activeSection.is_edited && (
                        <span className="text-[10px] text-amber-400 font-bold block">● Manually Edited</span>
                      )}
                    </div>
                    <textarea
                      value={activeSection.content}
                      onChange={(e) => handleSectionTextChange(activeSection.section_key, e.target.value)}
                      rows={12}
                      className="w-full p-4 rounded-2xl bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono leading-relaxed focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none custom-scrollbar"
                    />
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500">Select a section from the navigation sidebar to view and edit content.</div>
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

      {/* VERSION MANAGEMENT MODAL */}
      {showVersionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-2xl glass-card rounded-3xl p-6 border border-slate-800 space-y-5 bg-slate-950 text-xs my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-black text-slate-100 flex items-center gap-2">
                <span>💾</span> Manuscript Version Control
              </h3>
              <button onClick={() => setShowVersionModal(false)} className="text-slate-400 hover:text-slate-200 font-bold text-sm">
                ✕
              </button>
            </div>

            {/* SAVE NEW VERSION FORM */}
            <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 space-y-3">
              <h4 className="font-extrabold text-indigo-300">Save Current Revisions as New Version</h4>
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="e.g. Revised literature matrix, added empirical metric interpretation"
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  className="w-full p-3 rounded-2xl bg-slate-900 border border-slate-800 text-slate-200 text-xs outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end">
                <button onClick={handleSaveNewVersion} disabled={savingVersion} className="btn-primary py-2 px-5 font-bold">
                  {savingVersion ? 'Saving...' : 'Save New Version'}
                </button>
              </div>
            </div>

            {/* COMPARE VERSIONS ROW */}
            {versions.length >= 2 && (
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="font-extrabold text-slate-200">Compare Saved Versions</h4>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-slate-400">Compare Version</span>
                  <select
                    value={compareV1}
                    onChange={(e) => setCompareV1(Number(e.target.value))}
                    className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold"
                  >
                    {versions.map(v => <option key={v.version_number} value={v.version_number}>Version {v.version_number}</option>)}
                  </select>
                  <span className="text-slate-400">with Version</span>
                  <select
                    value={compareV2}
                    onChange={(e) => setCompareV2(Number(e.target.value))}
                    className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold"
                  >
                    {versions.map(v => <option key={v.version_number} value={v.version_number}>Version {v.version_number}</option>)}
                  </select>
                  <button onClick={handleCompareVersions} disabled={loadingCompare} className="btn-secondary py-1.5 px-4 font-bold">
                    {loadingCompare ? 'Comparing...' : 'Compare Diffs'}
                  </button>
                </div>
              </div>
            )}

            {/* AVAILABLE VERSIONS LIST */}
            <div className="space-y-2">
              <h4 className="font-extrabold text-slate-200 uppercase tracking-wider">Version History ({versions.length})</h4>
              <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {versions.map(v => (
                  <div key={v.version_id} className="p-3 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100">Version {v.version_number}</span>
                        {v.version_number === manuscript?.current_version_number && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-[9px]">
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">{v.change_summary || 'No description provided'}</p>
                      <span className="text-[10px] text-slate-500 block">{new Date(v.created_at).toLocaleString()}</span>
                    </div>

                    {v.version_number !== manuscript?.current_version_number && (
                      <button
                        onClick={() => handleRestoreVersion(v.version_number)}
                        className="px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-700 text-indigo-300 font-bold text-[11px]"
                      >
                        Restore
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setShowVersionModal(false)} className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 font-bold">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* COMPARE VERSIONS DIFF MODAL */}
      {showCompareModal && compareResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-3xl glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-950 text-xs my-8 max-h-[85vh] overflow-y-auto custom-scrollbar">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-black text-slate-100">
                Comparing Version {compareResult.version_a} vs Version {compareResult.version_b}
              </h3>
              <button onClick={() => setShowCompareModal(false)} className="text-slate-400 hover:text-slate-200 font-bold text-sm">
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {compareResult.diffs.map(diff => {
                if (diff.status === 'UNCHANGED') return null;

                return (
                  <div key={diff.section_key} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-slate-100 text-xs">{diff.title}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        diff.status === 'MODIFIED' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                        diff.status === 'ADDED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        'bg-rose-500/10 border-rose-500/30 text-rose-400'
                      }`}>
                        {diff.status}
                      </span>
                    </div>

                    {diff.status === 'MODIFIED' && (
                      <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
                        <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/30 text-rose-200">
                          <span className="text-[9px] text-rose-400 font-bold block mb-1">Version {compareResult.version_a} (Old)</span>
                          <p>{diff.old_content || '(Empty)'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-200">
                          <span className="text-[9px] text-emerald-400 font-bold block mb-1">Version {compareResult.version_b} (New)</span>
                          <p>{diff.new_content || '(Empty)'}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setShowCompareModal(false)} className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 font-bold">
                Close Diff
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EXPORT MANUSCRIPT MODAL */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="w-full max-w-md glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-950 text-xs">
            <h3 className="text-base font-black text-slate-100">Export Academic Manuscript / Thesis</h3>
            <p className="text-slate-400 text-[11px]">Select your preferred university submission export format:</p>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                onClick={() => handleExport('pdf')}
                disabled={!!exportingFormat}
                className="p-4 rounded-2xl bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-500/40 text-left space-y-1"
              >
                <span className="text-base font-black text-indigo-200 block">📄 Academic PDF (.pdf)</span>
                <span className="text-[10px] text-slate-400 block">University-style formatting (Times New Roman, A4, 1.5 spacing, TOC)</span>
              </button>

              <button
                onClick={() => handleExport('docx')}
                disabled={!!exportingFormat}
                className="p-4 rounded-2xl bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-500/40 text-left space-y-1"
              >
                <span className="text-base font-black text-indigo-200 block">📊 Word DOCX (.docx)</span>
                <span className="text-[10px] text-slate-400 block">Editable Word thesis format matching PDF structure</span>
              </button>

              <button
                onClick={() => handleExport('markdown')}
                disabled={!!exportingFormat}
                className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1"
              >
                <span className="text-base font-black text-slate-200 block">📝 Markdown (.md)</span>
                <span className="text-[10px] text-slate-400 block">Raw source text format</span>
              </button>

              <button
                onClick={() => handleExport('json')}
                disabled={!!exportingFormat}
                className="p-4 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-left space-y-1"
              >
                <span className="text-base font-black text-slate-200 block">🔷 JSON (.json)</span>
                <span className="text-[10px] text-slate-400 block">Structured claim metadata & sections</span>
              </button>
            </div>

            {exportingFormat && (
              <p className="text-center text-indigo-400 font-bold text-[11px] animate-pulse">
                Generating {exportingFormat.toUpperCase()} deliverable...
              </p>
            )}

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
