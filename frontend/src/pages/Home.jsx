import React from 'react';
import { Link } from 'react-router-dom';
import DragDropUpload from '../components/DragDropUpload';

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-12">
      
      {/* Hero Header Area */}
      <div className="text-center max-w-3xl mx-auto space-y-4 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-400">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
          Milestone 1 Core Foundation Active
        </div>
        
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight">
          <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            IntelliResearch
          </span>
        </h1>
        
        <p className="text-lg sm:text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-300 bg-clip-text text-transparent">
          AI-Based Research Gap Discovery & Recommendation System
        </p>
        
        <p className="text-slate-450 max-w-2xl mx-auto text-sm sm:text-base leading-relaxed">
          Accelerate your literature review. Upload your academic publications to extract abstract, metadata, and full-text text. Build an instantly searchable digital repository.
        </p>

        <div className="flex justify-center pt-2">
          <Link
            to="/dashboard"
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Go to Papers Dashboard
          </Link>
        </div>
      </div>

      {/* Main Upload Box */}
      <div className="pt-4">
        <DragDropUpload />
      </div>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8 max-w-5xl mx-auto">
        
        <div className="glass-card rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-slate-200">Multi-File Processing</h3>
          <p className="text-xs text-slate-450 leading-relaxed">
            Upload multiple research publications simultaneously. Supports standard PDF formats up to 50 MB per document.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-slate-200">Heuristic Extraction</h3>
          <p className="text-xs text-slate-450 leading-relaxed">
            Extract document titles and abstracts from first-page structural layouts and PyMuPDF text block font metrics.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-slate-200">Structured Repository</h3>
          <p className="text-xs text-slate-450 leading-relaxed">
            Stores PDFs and raw text exports on disk, while indexing metadata inside a robust relational SQL database.
          </p>
        </div>

      </div>

    </div>
  );
}
