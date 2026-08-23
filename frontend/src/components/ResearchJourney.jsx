import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import RecentResearchActivity from './RecentResearchActivity';
import ResearchJourneyTrace from './ResearchJourneyTrace';

export default function ResearchJourney({ projectId, onSelectTab }) {
  const [journeyData, setJourneyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchJourney();
  }, [projectId]);

  const fetchJourney = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getProjectResearchJourney(projectId);
      setJourneyData(res.data);
    } catch (err) {
      console.error('Failed to load project research journey:', err);
      setError('Unable to load research journey.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-3 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 mx-auto flex items-center justify-center text-indigo-400 font-bold animate-spin">
          🧭
        </div>
        <p className="text-xs text-slate-400 font-bold">Calculating Unified Research Journey...</p>
      </div>
    );
  }

  const progress = journeyData?.progress || { completed_stages: 0, total_stages: 10, progress_percentage: 0, is_complete: false };
  const nextAction = journeyData?.next_action;
  const stages = journeyData?.stages || [];
  const milestones = journeyData?.milestones || [];
  const activity = journeyData?.recent_activity || [];
  const traceNodes = journeyData?.trace_nodes || [];
  const isArchived = journeyData?.project_status === 'ARCHIVED';

  return (
    <div className="space-y-8 animate-fade-in text-xs text-slate-300">

      {/* ARCHIVED BANNER */}
      {isArchived && (
        <div className="p-4 rounded-3xl bg-amber-950/30 border border-amber-500/30 text-amber-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">📦</span>
            <div>
              <h4 className="font-extrabold text-xs">ARCHIVED PROJECT WORKSPACE</h4>
              <p className="text-[11px] text-amber-300/80">Research activity is preserved in read-only mode for academic reference.</p>
            </div>
          </div>
        </div>
      )}

      {/* WORKSPACE HEADER & PROGRESS */}
      <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold text-[11px]">
                🧭 YOUR RESEARCH JOURNEY
              </span>
              <span className="text-xs text-slate-400">PROJECT • <strong>{journeyData?.paper_count || 0} PAPERS</strong></span>
            </div>
            <h2 className="text-xl font-black text-slate-100">From Literature to Experimental Evidence & Report</h2>
            <p className="text-xs text-slate-400">
              Follow your guided 10-stage workflow to systematically discover gaps, validate ideas, execute experiments, and draft proposals.
            </p>
          </div>

          <div className="text-right space-y-1">
            <span className="text-[11px] text-slate-400 font-bold uppercase block">Research Progress</span>
            <span className="text-2xl font-black text-indigo-400">{progress.completed_stages} / 10 Stages</span>
            <span className="text-xs font-mono font-bold text-slate-400 block">({progress.progress_percentage}% Complete)</span>
          </div>
        </div>

        {/* PROGRESS BAR */}
        <div className="space-y-1">
          <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden border border-slate-800 p-0.5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-600 via-purple-500 to-emerald-400 transition-all duration-700"
              style={{ width: `${progress.progress_percentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* TOP "NEXT STEP" CARD */}
      {nextAction && (
        <div className="glass-card rounded-3xl p-6 border border-indigo-500/40 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-950 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-indigo-400 animate-ping"></span>
              <h3 className="text-sm font-extrabold text-indigo-200 uppercase tracking-wider">🎯 YOUR RECOMMENDED NEXT STEP</h3>
            </div>
            <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[11px]">
              STAGE {progress.current_stage_id} OF 10
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-center">
            <div className="lg:col-span-2 space-y-2">
              <h4 className="text-lg font-black text-slate-100">{nextAction.title}</h4>
              <p className="text-xs text-slate-300 font-medium">{nextAction.description}</p>
              <div className="p-3 rounded-2xl bg-indigo-950/50 border border-indigo-500/20 text-indigo-200 text-xs">
                <strong>💡 WHY SHOULD I DO THIS?</strong> {nextAction.why_explanation}
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => onSelectTab && onSelectTab(nextAction.target_tab)}
                className="btn-primary py-3 px-6 text-xs font-extrabold shadow-lg shadow-indigo-500/30 flex items-center gap-2 transform hover:-translate-y-0.5 transition-all w-full sm:w-auto justify-center"
              >
                <span>{nextAction.action_label}</span> →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TRACE FLOW */}
      <ResearchJourneyTrace traceNodes={traceNodes} onSelectTab={onSelectTab} />

      {/* 10 STAGES TIMELINE GRID */}
      <div className="space-y-3">
        <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>🧭</span> 10-Stage Guided Research Journey
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
          {stages.map((st) => {
            const isDone = st.status === 'COMPLETED';
            const isCurrent = st.stage_id === progress.current_stage_id;

            return (
              <div
                key={st.stage_id}
                className={`glass-card rounded-3xl p-5 border transition-all flex flex-col justify-between space-y-3 ${
                  isCurrent ? 'border-indigo-500/60 bg-slate-900/90 shadow-lg shadow-indigo-950/40 ring-1 ring-indigo-500/40' :
                  isDone ? 'border-emerald-500/30 bg-slate-900/50' : 'border-slate-800/80 bg-slate-950/60 opacity-80'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">Stage 0{st.stage_id}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                      isDone ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                      isCurrent ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300 animate-pulse' :
                      'bg-slate-800 border-slate-700 text-slate-400'
                    }`}>
                      {isDone ? '✓ COMPLETED' : isCurrent ? '→ CURRENT STEP' : st.status}
                    </span>
                  </div>

                  <h4 className="text-sm font-extrabold text-slate-100">{st.title}</h4>
                  <p className="text-[11px] text-indigo-300/90 italic font-medium">"{st.question}"</p>
                  <p className="text-xs text-slate-400 leading-relaxed">{st.summary_text}</p>
                </div>

                <div className="border-t border-slate-800/80 pt-3 flex items-center justify-end">
                  <button
                    onClick={() => onSelectTab && onSelectTab(st.target_tab)}
                    className={`py-1.5 px-4 rounded-xl font-bold text-xs transition-all ${
                      isCurrent ? 'btn-primary' : 'btn-secondary'
                    }`}
                  >
                    {st.action_label} →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* MILESTONES & RECENT ACTIVITY DUAL GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MILESTONES */}
        <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
          <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <span>🏆</span> Research Project Milestones ({milestones.filter(m => m.completed).length}/{milestones.length})
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {milestones.map((m) => (
              <div
                key={m.key}
                className={`p-3 rounded-2xl border flex items-center gap-2.5 transition-all ${
                  m.completed ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200' : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                <span className="text-base">{m.completed ? '🏆' : '⚪'}</span>
                <span className="text-xs font-bold truncate">{m.title}</span>
              </div>
            ))}
          </div>
        </div>

        {/* RECENT ACTIVITY */}
        <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 bg-slate-900/60">
          <h3 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <span>📜</span> Recent Research Activity Log
          </h3>

          <RecentResearchActivity activityList={activity} />
        </div>
      </div>

      {/* HELP FOOTER */}
      <div className="p-6 rounded-3xl bg-slate-900/40 border border-slate-800 space-y-2 text-slate-400 text-xs">
        <h4 className="font-extrabold text-slate-200 flex items-center gap-1.5">
          <span>💡</span> How Does the IntelliResearch Research Journey Work?
        </h4>
        <p className="leading-relaxed">
          IntelliResearch organizes your paper collection, literature gap analysis, experiment execution, and proposal drafting into an evidence-grounded workflow. The system guides your research steps based on your actual persisted data without fabricating experimental results or novelty claims.
        </p>
      </div>

    </div>
  );
}
