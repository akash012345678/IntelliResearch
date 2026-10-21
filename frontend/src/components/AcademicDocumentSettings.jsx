import React, { useState } from 'react';

export default function AcademicDocumentSettings({
  config,
  onConfigChange,
  onSave,
  saving = false,
  saveSuccess = false,
  onSwitchToPreview
}) {
  const [localFeedback, setLocalFeedback] = useState(false);

  const updateField = (field, val) => {
    onConfigChange({ ...config, [field]: val });
  };

  const handleSaveClick = async () => {
    if (onSave) {
      await onSave(config);
      setLocalFeedback(true);
      setTimeout(() => setLocalFeedback(false), 3500);
    }
  };

  const isSavedFeedbackVisible = saveSuccess || localFeedback;

  return (
    <div className="space-y-6 text-xs text-slate-300">

      {/* TOP ACTION & STATUS BANNER */}
      <div className="p-5 rounded-3xl bg-gradient-to-r from-indigo-950/60 via-slate-900/90 to-purple-950/40 border border-indigo-500/30 flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">📐</span>
            <h3 className="text-sm font-black text-slate-100 tracking-wide">
              Academic Document Formatting & Institutional Metadata
            </h3>
            {isSavedFeedbackVisible && (
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-extrabold text-[10px] flex items-center gap-1 animate-pulse">
                <span>✓</span> Saved & Applied to Report
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 max-w-2xl leading-relaxed">
            Configure formatting profile, typography, margins, and institution details. Saved settings are automatically applied to your <strong className="text-indigo-300">Live Document Preview</strong>, <strong className="text-indigo-300">Exported Thesis (.pdf / .docx / .md)</strong>, and consolidated <strong className="text-indigo-300">Project Reports</strong>.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onSwitchToPreview && (
            <button
              onClick={onSwitchToPreview}
              type="button"
              className="px-3.5 py-2 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all"
            >
              <span>👁️</span> Document Preview
            </button>
          )}

          <button
            onClick={handleSaveClick}
            disabled={saving}
            type="button"
            className="px-5 py-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
          >
            {saving ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Saving Settings...</span>
              </>
            ) : (
              <>
                <span>💾</span>
                <span>Save Formatting Settings</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* DOCUMENT FORMAT PROFILES */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <span>🎓</span> Select Academic Formatting Profile
          </h4>
          <span className="text-[10px] text-slate-400 font-mono">
            Active: <strong className="text-indigo-300 font-bold">{(config.profile || 'COLLEGE_PROJECT').replace('_', ' ')}</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {[
            {
              id: 'COLLEGE_PROJECT',
              icon: '🎓',
              name: 'College Project Report',
              badge: 'Recommended for Engineering',
              desc: 'Standard university final year project report with title page, certificates, table of contents, lists of figures/tables, and appendices.'
            },
            {
              id: 'RESEARCH_PAPER',
              icon: '📄',
              name: 'Academic Research Paper',
              badge: 'Conference / Journal Style',
              desc: 'IEEE / ACM / Springer style publication paper with abstract, indexed keywords, 2-column methodology, and verified evidence badges.'
            },
            {
              id: 'THESIS',
              icon: '📚',
              name: 'University Thesis Style',
              badge: 'Graduate / Master Thesis',
              desc: 'Comprehensive 8-chapter graduate thesis structure with extensive literature review matrix, full reproducibility log, and experiment matrices.'
            },
          ].map((profile) => (
            <button
              key={profile.id}
              onClick={() => updateField('profile', profile.id)}
              type="button"
              className={`p-4 rounded-2xl border text-left transition-all space-y-2 relative group ${
                config.profile === profile.id
                  ? 'bg-indigo-600/20 border-indigo-500/80 text-indigo-100 shadow-lg shadow-indigo-950/50 ring-2 ring-indigo-500/30'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-base">{profile.icon}</span>
                <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                  config.profile === profile.id
                    ? 'bg-indigo-500/30 text-indigo-200 border-indigo-400/40'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {profile.badge}
                </span>
              </div>
              <div>
                <span className="text-xs font-black block text-slate-100">{profile.name}</span>
                <span className="text-[10px] text-slate-400 block font-normal leading-relaxed mt-1">{profile.desc}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* PAGE & TYPOGRAPHY SETTINGS */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800/80 pb-3">
          <span>⚙️</span> Page Layout & Typography Configuration
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
            <label className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Page Size</label>
            <select
              value={config.page_size}
              onChange={(e) => updateField('page_size', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold text-xs outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="A4">Standard A4 (210 x 297 mm)</option>
              <option value="LETTER">US Letter (8.5 x 11 in)</option>
            </select>
            <span className="text-[9px] text-slate-500 block">Universal academic print standard</span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
            <label className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Margins</label>
            <select
              value={config.margins}
              onChange={(e) => updateField('margins', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold text-xs outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="NORMAL">Normal (1.25 in Left / 1.0 in)</option>
              <option value="NARROW">Narrow (0.75 in All Sides)</option>
            </select>
            <span className="text-[9px] text-slate-500 block">Normal margin includes thesis binding offset</span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
            <label className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Font Family</label>
            <select
              value={config.font_family}
              onChange={(e) => updateField('font_family', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold text-xs outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="Times New Roman">Times New Roman (Academic Standard)</option>
              <option value="Arial">Arial (Clean Sans-Serif)</option>
              <option value="Calibri">Calibri (Modern Professional)</option>
            </select>
            <span className="text-[9px] text-slate-500 block">Applied across PDF, DOCX, and Preview</span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
            <label className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Line Spacing</label>
            <select
              value={config.line_spacing}
              onChange={(e) => updateField('line_spacing', parseFloat(e.target.value))}
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold text-xs outline-none focus:border-indigo-500 transition-colors"
            >
              <option value={1.0}>1.0 Single Spacing</option>
              <option value={1.15}>1.15 Standard Spacing</option>
              <option value={1.5}>1.5 College Project Spacing (Recommended)</option>
              <option value={2.0}>2.0 Double Spacing (Journal Draft)</option>
            </select>
            <span className="text-[9px] text-slate-500 block">Controls paragraph readability density</span>
          </div>
        </div>
      </div>

      {/* STUDENT & INSTITUTION METADATA */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <span>🏛️</span> Title Page & Institutional Credentials
          </h4>
          <span className="text-[10px] text-slate-400">
            Rendered directly on Title Page, Cover, and Supervision Certificate
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Student / Author Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Akash K"
              value={config.student_name || ''}
              onChange={(e) => updateField('student_name', e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-bold outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Register / Roll Number <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. 2312002"
              value={config.register_number || ''}
              onChange={(e) => updateField('register_number', e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-mono font-bold outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Institution Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. National Engineering College"
              value={config.institution || ''}
              onChange={(e) => updateField('institution', e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-bold outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Department
            </label>
            <input
              type="text"
              placeholder="e.g. Department of Computer Science & Engineering"
              value={config.department || ''}
              onChange={(e) => updateField('department', e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Faculty Guide / Supervisor
            </label>
            <input
              type="text"
              placeholder="e.g. Dr. Faculty Supervisor, Ph.D."
              value={config.supervisor || config.guide_name || ''}
              onChange={(e) => {
                updateField('supervisor', e.target.value);
                updateField('guide_name', e.target.value);
              }}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">
              Academic Year
            </label>
            <input
              type="text"
              placeholder="e.g. 2025-2026"
              value={config.academic_year || ''}
              onChange={(e) => updateField('academic_year', e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 font-mono outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* REPORT APPLICATION GUIDE & BOTTOM SAVE BAR */}
      <div className="p-5 rounded-3xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[11px] font-bold text-slate-200 flex items-center gap-1.5">
            <span>🛡️</span> Zero-Fabrication Academic Report Binding
          </span>
          <p className="text-[10px] text-slate-400">
            Saving formatting settings updates the project record in the database. When you click <strong className="text-slate-300">Export Thesis</strong> or download the <strong className="text-slate-300">Submission Package (.zip)</strong>, all deliverables will automatically include your name, roll number, and institution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isSavedFeedbackVisible && (
            <span className="text-emerald-400 font-bold text-xs flex items-center gap-1">
              <span>✓</span> Saved to Project!
            </span>
          )}

          <button
            onClick={handleSaveClick}
            disabled={saving}
            type="button"
            className="px-6 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
          >
            {saving ? 'Saving...' : '💾 Save & Apply to Reports'}
          </button>
        </div>
      </div>

    </div>
  );
}
