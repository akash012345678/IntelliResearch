import React from 'react';

export default function AcademicDocumentSettings({ config, onConfigChange }) {
  const updateField = (field, val) => {
    onConfigChange({ ...config, [field]: val });
  };

  return (
    <div className="space-y-6 text-xs text-slate-300">

      {/* DOCUMENT FORMAT PROFILES */}
      <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3">
        <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <span>🎓</span> Select Academic Formatting Profile
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { id: 'COLLEGE_PROJECT', name: '🎓 College Project Report', desc: 'Title page, Table of Contents, Lists of Figures/Tables, Appendices' },
            { id: 'RESEARCH_PAPER', name: '📄 Academic Research Paper', desc: 'IEEE / ACM / Springer standard 2-column style' },
            { id: 'THESIS', name: '📚 University Thesis Style', desc: 'Comprehensive chapter divisions, experiment log, & detailed methodology' },
          ].map((profile) => (
            <button
              key={profile.id}
              onClick={() => updateField('profile', profile.id)}
              className={`p-4 rounded-2xl border text-left transition-all space-y-1 ${
                config.profile === profile.id ? 'bg-indigo-600/20 border-indigo-500/60 text-indigo-200 shadow-md font-bold' :
                'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="text-xs font-extrabold block">{profile.name}</span>
              <span className="text-[10px] text-slate-400 block font-normal">{profile.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* PAGE & TYPOGRAPHY SETTINGS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <label className="text-[10px] text-slate-400 font-bold uppercase block">Page Size</label>
          <select
            value={config.page_size}
            onChange={(e) => updateField('page_size', e.target.value)}
            className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold text-xs"
          >
            <option value="A4">Standard A4 (210 x 297 mm)</option>
            <option value="LETTER">US Letter (8.5 x 11 in)</option>
          </select>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <label className="text-[10px] text-slate-400 font-bold uppercase block">Margins</label>
          <select
            value={config.margins}
            onChange={(e) => updateField('margins', e.target.value)}
            className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold text-xs"
          >
            <option value="NORMAL">Normal (1 inch / 25.4 mm)</option>
            <option value="NARROW">Narrow (0.5 inch / 12.7 mm)</option>
          </select>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <label className="text-[10px] text-slate-400 font-bold uppercase block">Font Family</label>
          <select
            value={config.font_family}
            onChange={(e) => updateField('font_family', e.target.value)}
            className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold text-xs"
          >
            <option value="Times New Roman">Times New Roman (Academic)</option>
            <option value="Arial">Arial (Clean Sans-Serif)</option>
            <option value="Calibri">Calibri (Modern Professional)</option>
          </select>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <label className="text-[10px] text-slate-400 font-bold uppercase block">Line Spacing</label>
          <select
            value={config.line_spacing}
            onChange={(e) => updateField('line_spacing', parseFloat(e.target.value))}
            className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-bold text-xs"
          >
            <option value={1.0}>1.0 Single Spacing</option>
            <option value={1.15}>1.15 Standard Spacing</option>
            <option value={1.5}>1.5 College Project Spacing</option>
            <option value={2.0}>2.0 Double Spacing</option>
          </select>
        </div>
      </div>

      {/* STUDENT & INSTITUTION METADATA */}
      <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-3">
        <h4 className="text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <span>🏛️</span> Title Page & Institution Metadata
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Student Name</label>
            <input
              type="text"
              placeholder="e.g. Alex Rivera"
              value={config.student_name || ''}
              onChange={(e) => updateField('student_name', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Register / Roll Number</label>
            <input
              type="text"
              placeholder="e.g. 2024-CS-892"
              value={config.register_number || ''}
              onChange={(e) => updateField('register_number', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Institution</label>
            <input
              type="text"
              placeholder="e.g. Stanford University"
              value={config.institution || ''}
              onChange={(e) => updateField('institution', e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

    </div>
  );
}
