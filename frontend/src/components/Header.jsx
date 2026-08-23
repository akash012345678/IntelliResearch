import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Header() {
  const location = useLocation();

  const isLinkActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-950/75 backdrop-blur-md border-b border-slate-800/80 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo Brand Area */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 group-hover:shadow-indigo-500/40 transition-all duration-300">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-400 bg-clip-text text-transparent">
                  IntelliResearch
                </span>
                <span className="text-[10px] text-indigo-400/80 font-medium uppercase tracking-widest hidden sm:inline">
                  AI Research Platform
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-2">
            <Link
              to="/"
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                isLinkActive('/') && location.pathname === '/'
                  ? 'bg-slate-900 text-indigo-400 border border-slate-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>🏠</span> Home
              </div>
            </Link>

            <Link
              to="/dashboard"
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                isLinkActive('/dashboard')
                  ? 'bg-slate-900 text-indigo-400 border border-slate-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>📚</span> Research Library
              </div>
            </Link>

            <Link
              to="/research-projects"
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                isLinkActive('/research-projects')
                  ? 'bg-slate-900 text-indigo-400 border border-slate-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>🗂</span> My Projects
              </div>
            </Link>

            <Link
              to="/research-intelligence"
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                isLinkActive('/research-intelligence')
                  ? 'bg-slate-900 text-indigo-400 border border-slate-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>🔎</span> Research Intelligence
              </div>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
