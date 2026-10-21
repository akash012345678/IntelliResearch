import React, { useState } from 'react';

export default function AcademicDocumentPreview({ previewData }) {
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  if (!previewData || !previewData.pages || previewData.pages.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400">
        No document preview pages available.
      </div>
    );
  }

  const pages = previewData.pages;
  const activePage = pages[currentPageIndex] || pages[0];

  return (
    <div className="space-y-4 text-xs text-slate-300">

      {/* PAGE NAVIGATOR BAR */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="space-y-0.5">
          <h4 className="text-sm font-black text-slate-100 flex items-center gap-2">
            <span>👁️</span> Live Page-by-Page Document Layout Preview
          </h4>
          <p className="text-[11px] text-slate-400">
            Profile: <strong className="text-slate-200">{previewData.profile}</strong> | Total Pages: <strong className="text-slate-200">{previewData.total_pages}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            disabled={currentPageIndex === 0}
            onClick={() => setCurrentPageIndex(prev => Math.max(0, prev - 1))}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 font-bold text-xs disabled:opacity-40"
          >
            ← Previous Page
          </button>

          <span className="font-mono text-xs font-bold text-indigo-400">
            Page {activePage.page_number} of {previewData.total_pages}
          </span>

          <button
            disabled={currentPageIndex === pages.length - 1}
            onClick={() => setCurrentPageIndex(prev => Math.min(pages.length - 1, prev + 1))}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 font-bold text-xs disabled:opacity-40"
          >
            Next Page →
          </button>
        </div>
      </div>

      {/* PAGE SIMULATOR CANVAS */}
      <div className="p-8 bg-slate-950 rounded-3xl border border-slate-800 flex justify-center">
        <div
          className={`w-full max-w-3xl bg-white text-slate-900 rounded-2xl shadow-2xl min-h-[700px] border border-slate-300 ${
            previewData?.config?.margins === 'NARROW' ? 'p-6 sm:p-8' : 'p-8 sm:p-12'
          }`}
          style={{
            fontFamily: previewData?.config?.font_family ? `"${previewData.config.font_family}", serif` : 'serif',
            lineHeight: previewData?.config?.line_spacing || 1.5
          }}
        >
          <div className="flex items-center justify-between border-b border-slate-200 pb-2 text-[10px] text-slate-500 font-sans uppercase font-bold mb-6">
            <span>{previewData.project_name}</span>
            <span className="px-2 py-0.5 rounded bg-slate-100 text-indigo-700 font-mono text-[9px]">
              {previewData?.config?.profile ? previewData.config.profile.replace('_', ' ') : 'ACADEMIC DELIVERABLE'}
            </span>
            <span>{activePage.title}</span>
          </div>

          <div
            className="prose max-w-none text-slate-800 text-sm"
            style={{
              fontFamily: previewData?.config?.font_family ? `"${previewData.config.font_family}", serif` : 'inherit',
              lineHeight: previewData?.config?.line_spacing || 1.5
            }}
            dangerouslySetInnerHTML={{ __html: activePage.html_content }}
          />

          <div className="mt-12 pt-4 border-t border-slate-200 text-center text-[10px] text-slate-400 font-sans">
            Page {activePage.page_number}
          </div>
        </div>
      </div>

    </div>
  );
}
