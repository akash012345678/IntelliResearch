import React, { useState } from 'react';

const INITIAL_CHECKLIST_ITEMS = [
  { id: 'c1', label: 'Verify every paper citation', checked: false },
  { id: 'c2', label: 'Verify author names and credentials', checked: false },
  { id: 'c3', label: 'Verify publication years', checked: false },
  { id: 'c4', label: 'Verify DOI and source URLs', checked: false },
  { id: 'c5', label: 'Verify dataset sources and versions', checked: false },
  { id: 'c6', label: 'Verify baseline vs proposed experiment metrics', checked: false },
  { id: 'c7', label: 'Verify statistical claims and multi-run ranges', checked: false },
  { id: 'c8', label: 'Verify figures and source table references', checked: false },
  { id: 'c9', label: 'Review hardware and software setup details', checked: false },
  { id: 'c10', label: 'Review project limitations section', checked: false },
  { id: 'c11', label: 'Review novelty claim safety warnings', checked: false },
  { id: 'c12', label: 'Check plagiarism independently', checked: false },
  { id: 'c13', label: 'Follow university and conference formatting rules', checked: false },
];

export default function ManuscriptReviewChecklist() {
  const [items, setItems] = useState(INITIAL_CHECKLIST_ITEMS);

  const toggleCheck = (id) => {
    setItems(prev => prev.map(i => i.id === id ? { ...i, checked: !i.checked } : i));
  };

  const markAll = () => {
    setItems(prev => prev.map(i => ({ ...i, checked: true })));
  };

  const checkedCount = items.filter(i => i.checked).length;

  return (
    <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 text-xs text-slate-300">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="space-y-0.5">
          <h4 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
            <span>🎓</span> Final Academic Pre-Submission Review Checklist ({checkedCount}/13)
          </h4>
          <p className="text-xs text-slate-400">Complete all student verification steps before submitting your final manuscript.</p>
        </div>

        <button
          onClick={markAll}
          className="btn-secondary py-1.5 px-4 text-xs font-bold"
        >
          Mark All Completed ✓
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {items.map((item) => (
          <label
            key={item.id}
            className={`p-3 rounded-2xl border transition-all flex items-center gap-3 cursor-pointer ${
              item.checked ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200 font-semibold' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <input
              type="checkbox"
              checked={item.checked}
              onChange={() => toggleCheck(item.id)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-900 border-slate-700"
            />
            <span className="text-xs">{item.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
