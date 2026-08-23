import React, { useState } from 'react';

export default function ReferenceManager({ references = [], citationStyle = 'IEEE', onStyleChange, onViewPaper }) {
  const [search, setSearch] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const filtered = references.filter(r =>
    r.title.toLowerCase().includes(search.toLowerCase()) ||
    r.authors.toLowerCase().includes(search.toLowerCase())
  );

  const copyCitation = (refItem) => {
    const text = citationStyle === 'IEEE' ? refItem.formatted_ieee : citationStyle === 'APA' ? refItem.formatted_apa : refItem.formatted_harvard;
    navigator.clipboard.writeText(text);
    setCopiedId(refItem.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-4 text-xs text-slate-300">

      {/* HEADER & STYLE SELECTOR */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="space-y-0.5">
          <h3 className="text-sm font-black text-slate-100 flex items-center gap-2">
            <span>📚</span> Verified Project Reference Manager ({references.length})
          </h3>
          <p className="text-[11px] text-slate-400">Strictly uses verified project paper metadata without bibliographic fabrication.</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Citation Style:</span>
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800">
            {['IEEE', 'APA', 'Harvard'].map((style) => (
              <button
                key={style}
                onClick={() => onStyleChange(style)}
                className={`px-3 py-1 rounded-lg text-[10px] font-extrabold transition-all ${
                  citationStyle === style ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {style}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SEARCH BAR */}
      <input
        type="text"
        placeholder="Search reference titles, authors..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full p-3 rounded-2xl bg-slate-950 border border-slate-800 text-slate-200 outline-none text-xs focus:border-indigo-500"
      />

      {/* REFERENCE LIST */}
      <div className="space-y-3 max-h-[60vh] overflow-y-auto custom-scrollbar">
        {filtered.length === 0 ? (
          <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-400">
            No matching references found.
          </div>
        ) : (
          filtered.map((ref) => {
            const formattedText = citationStyle === 'IEEE' ? ref.formatted_ieee : citationStyle === 'APA' ? ref.formatted_apa : ref.formatted_harvard;

            return (
              <div key={ref.id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-indigo-500/40 transition-all">
                <div className="flex items-start justify-between gap-3">
                  <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[10px]">
                    {ref.citation_key}
                  </span>

                  {!ref.has_complete_metadata && (
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold text-[10px]">
                      ⚠ Bibliographic Metadata Incomplete
                    </span>
                  )}
                </div>

                <p className="text-slate-200 font-mono leading-relaxed text-xs">{formattedText}</p>

                <div className="flex items-center justify-between border-t border-slate-800/80 pt-2 text-[11px]">
                  <div className="space-x-3 text-slate-400">
                    <span>DOI: <strong className="text-slate-300 font-mono">{ref.doi}</strong></span>
                    <span>Year: <strong className="text-slate-300 font-mono">{ref.publication_year}</strong></span>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => onViewPaper && onViewPaper(ref.paper_id)}
                      className="px-3 py-1 rounded-xl bg-slate-950 hover:bg-slate-800 text-indigo-300 font-bold border border-slate-800"
                    >
                      View Paper 📄
                    </button>
                    <button
                      onClick={() => copyCitation(ref)}
                      className="px-3 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold"
                    >
                      {copiedId === ref.id ? 'Copied! ✓' : 'Copy Citation 📋'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
