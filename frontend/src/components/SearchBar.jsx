import React from 'react';

export default function SearchBar({
  value,
  onChange,
  searchMode = 'semantic',
  onModeChange,
  placeholder
}) {
  const isSemantic = searchMode === 'semantic';
  const currentPlaceholder = placeholder || (
    isSemantic 
      ? "Enter natural-language research query (e.g. driver drowsiness detection)..."
      : "Search research papers by title..."
  );

  return (
    <div className="flex flex-col sm:flex-row items-center gap-3 w-full max-w-2xl animate-fade-in">
      {/* Search Mode Toggle Buttons */}
      {onModeChange && (
        <div className="flex items-center p-1 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-lg self-stretch sm:self-auto flex-shrink-0">
          <button
            type="button"
            onClick={() => onModeChange('semantic')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-300 ${
              isSemantic
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-indigo-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Semantic AI
          </button>
          <button
            type="button"
            onClick={() => onModeChange('title')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-300 ${
              !isSemantic
                ? 'bg-slate-750 text-slate-100 shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Title Match
          </button>
        </div>
      )}

      {/* Input Field Box */}
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500">
          <svg className={`w-5 h-5 ${isSemantic ? 'text-indigo-400' : 'text-slate-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={currentPlaceholder}
          className={`w-full pl-12 pr-10 py-3 bg-slate-900/60 backdrop-blur-xl border rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none transition-all duration-300 shadow-xl text-sm ${
            isSemantic 
              ? 'border-indigo-900/50 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 hover:border-indigo-800/80' 
              : 'border-slate-800 focus:ring-2 focus:ring-slate-600 focus:border-slate-600 hover:border-slate-700'
          }`}
        />
        {value && (
          <button
            onClick={() => onChange('')}
            className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
            title="Clear search"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
