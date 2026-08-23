import React from 'react';

export default function RecentResearchActivity({ activityList = [] }) {
  if (!activityList || activityList.length === 0) {
    return (
      <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-400 text-xs">
        No recent project activity logged yet.
      </div>
    );
  }

  const formatTime = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return ts;
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'PAPER_ADDED': return '📄';
      case 'DIRECTION_SAVED': return '💡';
      case 'EXPERIMENT_CREATED': return '🧪';
      case 'PROPOSAL_CREATED': return '📝';
      default: return '📍';
    }
  };

  return (
    <div className="space-y-2 text-xs">
      {activityList.map((act) => (
        <div key={act.id} className="p-3 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="text-base">{getEventIcon(act.event_type)}</span>
            <div>
              <h5 className="font-bold text-slate-200">{act.title}</h5>
              <p className="text-[11px] text-slate-400">{act.description}</p>
            </div>
          </div>
          <span className="text-[10px] text-slate-500 font-mono font-semibold shrink-0">
            {formatTime(act.timestamp)}
          </span>
        </div>
      ))}
    </div>
  );
}
