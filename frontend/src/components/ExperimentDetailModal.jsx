import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function ExperimentDetailModal({ experiment, projectId, onClose, onRefresh }) {
  const [exp, setExp] = useState(experiment);
  const [activeTab, setActiveTab] = useState('config'); // 'config' | 'results' | 'reproducibility' | 'notes'
  const [saving, setSaving] = useState(false);

  // Form states for configuration
  const [status, setStatus] = useState(exp.status || 'PLANNED');
  const [datasetName, setDatasetName] = useState(exp.dataset_config?.dataset_name || '');
  const [datasetSamples, setDatasetSamples] = useState(exp.dataset_config?.samples || '');
  const [baselineAlg, setBaselineAlg] = useState(exp.baseline_config?.algorithm || '');
  const [proposedArch, setProposedArch] = useState(exp.proposed_config?.architecture || '');
  const [gpuEnv, setGpuEnv] = useState(exp.environment_config?.gpu || '');
  const [externalUrl, setExternalUrl] = useState(exp.execution_config?.external_url || '');

  // Result entry state
  const [newRunSeed, setNewRunSeed] = useState(42);
  const [newMetricName, setNewMetricName] = useState('Accuracy');
  const [newBaselineVal, setNewBaselineVal] = useState('');
  const [newProposedVal, setNewProposedVal] = useState('');
  const [newMetricUnit, setNewMetricUnit] = useState('0-1');
  const [recordingResult, setRecordingResult] = useState(false);

  // Notes & Limitations
  const [notes, setNotes] = useState(exp.notes || '');
  const [limitations, setLimitations] = useState(exp.limitations || '');

  // Reproducibility Checklist
  const DEFAULT_CHECKLIST = [
    'Dataset recorded with version/source',
    'Split strategy documented (Train/Val/Test)',
    'Preprocessing steps recorded',
    'Model architecture & hyperparameters specified',
    'Random seed explicitly set',
    'Hardware / GPU environment logged',
    'Software & library versions recorded',
    'Code repository / notebook link saved',
    'Evaluation metrics clearly defined',
    'Empirical results entered without fabrication'
  ];
  const [checklist, setChecklist] = useState(exp.reproducibility_checklist?.length ? exp.reproducibility_checklist : []);

  const toggleChecklist = (item) => {
    if (checklist.includes(item)) {
      setChecklist(checklist.filter(i => i !== item));
    } else {
      setChecklist([...checklist, item]);
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    setSaving(true);
    try {
      const res = await apiService.updateProjectExperiment(projectId, exp.id, {
        status: newStatus,
        dataset_config: { ...exp.dataset_config, dataset_name: datasetName, samples: datasetSamples },
        baseline_config: { ...exp.baseline_config, algorithm: baselineAlg },
        proposed_config: { ...exp.proposed_config, architecture: proposedArch },
        environment_config: { ...exp.environment_config, gpu: gpuEnv },
        execution_config: { ...exp.execution_config, external_url: externalUrl },
        notes,
        limitations,
        reproducibility_checklist: checklist
      });
      setStatus(newStatus);
      setExp(res.data);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to update experiment status:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleRecordNewRunAndResults = async () => {
    if (!newMetricName.trim()) return;
    setRecordingResult(true);
    try {
      // 1. Create Run
      const runRes = await apiService.createExperimentRun(projectId, exp.id, {
        seed: Number(newRunSeed) || 42,
        notes: 'Empirical result run recorded by student.'
      });
      const runId = runRes.data.id;

      // 2. Record Baseline and Proposed Results if entered
      const resultsToCreate = [];
      if (newBaselineVal.trim()) {
        resultsToCreate.push({
          metric_name: newMetricName,
          metric_value: newBaselineVal,
          unit: newMetricUnit,
          method_type: 'baseline'
        });
      }
      if (newProposedVal.trim()) {
        resultsToCreate.push({
          metric_name: newMetricName,
          metric_value: newProposedVal,
          unit: newMetricUnit,
          method_type: 'proposed'
        });
      }

      if (resultsToCreate.length > 0) {
        await apiService.recordExperimentResults(projectId, runId, resultsToCreate);
      }

      // Fetch refreshed experiment
      const freshExp = await apiService.getProjectExperimentDetail(projectId, exp.id);
      setExp(freshExp.data);
      if (freshExp.data.status === 'PLANNED' || freshExp.data.status === 'READY') {
        await handleUpdateStatus('COMPLETED');
      } else if (onRefresh) {
        onRefresh();
      }

      // Reset inputs
      setNewBaselineVal('');
      setNewProposedVal('');
    } catch (err) {
      console.error('Failed to record run results:', err);
    } finally {
      setRecordingResult(false);
    }
  };

  // Extract all recorded results across runs
  const allRuns = exp.runs || [];
  const latestRun = allRuns.length > 0 ? allRuns[allRuns.length - 1] : null;
  const baselineResults = latestRun ? latestRun.results.filter(r => r.method_type === 'baseline') : [];
  const proposedResults = latestRun ? latestRun.results.filter(r => r.method_type === 'proposed') : [];

  // Calculate difference if both numeric
  const getMetricDiff = (metricName) => {
    const b = baselineResults.find(r => r.metric_name === metricName);
    const p = proposedResults.find(r => r.metric_name === metricName);
    if (!b || !p) return null;
    const bVal = parseFloat(b.metric_value);
    const pVal = parseFloat(p.metric_value);
    if (isNaN(bVal) || isNaN(pVal)) return null;
    const absDiff = (pVal - bVal).toFixed(4);
    const relDiff = bVal !== 0 ? (((pVal - bVal) / Math.abs(bVal)) * 100).toFixed(2) + '%' : 'N/A';
    return { bVal, pVal, absDiff, relDiff };
  };

  const exportMarkdown = () => {
    const md = `# Experiment Report: ${exp.name}
**Type:** ${exp.experiment_type}
**Status:** ${exp.status}
**Dataset:** ${exp.dataset_config?.dataset_name || 'Not recorded'}

## Purpose
${exp.purpose || 'Not specified'}

## Research Question & Hypotheses
- **RQ:** ${exp.research_question || 'Not specified'}
- **H0:** ${exp.hypothesis_h0 || 'Not specified'}
- **H1:** ${exp.hypothesis_h1 || 'Not specified'}

## Baseline vs Proposed Configuration
- **Baseline:** ${exp.baseline_config?.algorithm || 'Not recorded'}
- **Proposed Architecture:** ${exp.proposed_config?.architecture || 'Not recorded'}

## Empirical Results
${allRuns.length === 0 ? '_Results not yet recorded._' : allRuns.map(r => `
### Run #${r.run_number} (Seed ${r.seed})
${r.results.map(res => `- **${res.method_type.toUpperCase()}** ${res.metric_name}: ${res.metric_value} ${res.unit || ''}`).join('\n')}
`).join('\n')}

## Reproducibility (${checklist.length}/${DEFAULT_CHECKLIST.length})
${DEFAULT_CHECKLIST.map(item => `- [${checklist.includes(item) ? 'x' : ' '}] ${item}`).join('\n')}

## Limitations
${limitations || 'No specific limitations recorded.'}

---
*Generated by IntelliResearch Experiment Workspace. Recorded values are student-entered empirical measurements.*
`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Experiment_${exp.id}_Report.md`;
    a.click();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 sm:pt-24 pb-6 px-3 sm:px-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="w-full max-w-4xl glass-card rounded-3xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6 max-h-[calc(100vh-7rem)] overflow-y-auto custom-scrollbar relative text-xs text-slate-300">

        {/* HEADER */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono font-bold text-[11px]">
                {exp.experiment_type}
              </span>
              <span className={`px-3 py-1 rounded-full text-[11px] font-extrabold border ${
                status === 'COMPLETED' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                status === 'IN_PROGRESS' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                'bg-slate-800 border-slate-700 text-slate-300'
              }`}>
                {status}
              </span>
            </div>
            <h2 className="text-2xl font-black text-slate-100">{exp.name}</h2>
            <p className="text-xs text-slate-400">{exp.purpose}</p>
          </div>

          <button onClick={onClose} className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all font-bold">
            ✕ Close
          </button>
        </div>

        {/* STATUS CHANGERS */}
        <div className="flex flex-wrap items-center gap-2 p-3 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] text-slate-400 font-bold uppercase mr-2">Change Status:</span>
          {['PLANNED', 'READY', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'CANCELLED'].map((st) => (
            <button
              key={st}
              onClick={() => handleUpdateStatus(st)}
              disabled={saving}
              className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
                status === st ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-850 text-slate-400 hover:text-slate-200 border border-slate-700/50'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* WORKSPACE NAVIGATION TABS */}
        <div className="flex border-b border-slate-800 gap-2 font-bold scrollbar-none">
          <button
            onClick={() => setActiveTab('config')}
            className={`pb-2.5 px-4 transition-all border-b-2 whitespace-nowrap ${
              activeTab === 'config' ? 'border-indigo-500 text-indigo-400 font-extrabold' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            ⚙ Config & Setup
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`pb-2.5 px-4 transition-all border-b-2 whitespace-nowrap ${
              activeTab === 'results' ? 'border-indigo-500 text-indigo-400 font-extrabold' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📊 Record Results ({allRuns.length} Runs)
          </button>
          <button
            onClick={() => setActiveTab('reproducibility')}
            className={`pb-2.5 px-4 transition-all border-b-2 whitespace-nowrap ${
              activeTab === 'reproducibility' ? 'border-indigo-500 text-indigo-400 font-extrabold' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🔁 Reproducibility ({checklist.length}/10)
          </button>
        </div>

        {/* TAB 1: CONFIGURATION */}
        {activeTab === 'config' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <span>📦</span> Dataset Configuration
                </h4>
                <div className="space-y-2">
                  <div>
                    <label className="text-[10px] text-slate-400 block font-bold">Dataset Name</label>
                    <input
                      type="text"
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                      placeholder="e.g. NTHU-DDD, Kaggle Driver Drowsiness"
                      className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block font-bold">Sample Count / Splits</label>
                    <input
                      type="text"
                      value={datasetSamples}
                      onChange={(e) => setDatasetSamples(e.target.value)}
                      placeholder="e.g. 10,000 images (80/10/10)"
                      className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <span>🧠</span> Model Setup
                </h4>
                <div className="space-y-2">
                  <div>
                    <label className="text-[10px] text-slate-400 block font-bold">Baseline Algorithm</label>
                    <input
                      type="text"
                      value={baselineAlg}
                      onChange={(e) => setBaselineAlg(e.target.value)}
                      placeholder="e.g. ResNet-50 Baseline"
                      className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block font-bold">Proposed Architecture</label>
                    <input
                      type="text"
                      value={proposedArch}
                      onChange={(e) => setProposedArch(e.target.value)}
                      placeholder="e.g. Proposed Spatial-Temporal Transformer"
                      className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <span>💻</span> Environment & Execution Reference
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Hardware / GPU</label>
                  <input
                    type="text"
                    value={gpuEnv}
                    onChange={(e) => setGpuEnv(e.target.value)}
                    placeholder="e.g. NVIDIA RTX 3090 / Colab T4 GPU"
                    className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">External Run URL (Colab / GitHub)</label>
                  <input
                    type="text"
                    value={externalUrl}
                    onChange={(e) => setExternalUrl(e.target.value)}
                    placeholder="https://colab.research.google.com/..."
                    className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => handleUpdateStatus(status)}
                disabled={saving}
                className="btn-primary py-2 px-5 text-xs font-bold"
              >
                {saving ? 'Saving...' : '💾 Save Configuration Updates'}
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: RECORD RESULTS */}
        {activeTab === 'results' && (
          <div className="space-y-6">
            {/* ENTER NEW RESULT FORM */}
            <div className="p-5 rounded-3xl bg-indigo-950/20 border border-indigo-500/30 space-y-4">
              <div className="flex items-center justify-between border-b border-indigo-500/20 pb-2">
                <h4 className="text-xs font-extrabold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                  <span>📝</span> Enter Empirical Result Measurement
                </h4>
                <span className="text-[10px] text-slate-400 font-bold">Student Lab Entry</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Metric</label>
                  <select
                    value={newMetricName}
                    onChange={(e) => setNewMetricName(e.target.value)}
                    className="w-full mt-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none font-bold"
                  >
                    <option value="Accuracy">Accuracy</option>
                    <option value="Precision">Precision</option>
                    <option value="Recall">Recall</option>
                    <option value="F1-score">F1-score</option>
                    <option value="MAE">MAE</option>
                    <option value="RMSE">RMSE</option>
                    <option value="mAP">mAP</option>
                    <option value="Latency (ms)">Latency (ms)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Baseline Value</label>
                  <input
                    type="text"
                    value={newBaselineVal}
                    onChange={(e) => setNewBaselineVal(e.target.value)}
                    placeholder="e.g. 0.82"
                    className="w-full mt-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Proposed Value</label>
                  <input
                    type="text"
                    value={newProposedVal}
                    onChange={(e) => setNewProposedVal(e.target.value)}
                    placeholder="e.g. 0.86"
                    className="w-full mt-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Unit / Scale</label>
                  <input
                    type="text"
                    value={newMetricUnit}
                    onChange={(e) => setNewMetricUnit(e.target.value)}
                    placeholder="0-1 or %"
                    className="w-full mt-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block font-bold">Random Seed</label>
                  <input
                    type="number"
                    value={newRunSeed}
                    onChange={(e) => setNewRunSeed(e.target.value)}
                    className="w-full mt-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <button
                  onClick={handleRecordNewRunAndResults}
                  disabled={recordingResult || (!newBaselineVal.trim() && !newProposedVal.trim())}
                  className="btn-primary py-2 px-5 text-xs font-bold disabled:opacity-50"
                >
                  {recordingResult ? 'Saving...' : '💾 Record Measurement Run'}
                </button>
              </div>
            </div>

            {/* RECORDED RESULTS & COMPARISON TABLE */}
            <div className="space-y-3">
              <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <span>⚖</span> Baseline vs Proposed Result Comparison Matrix
              </h4>

              {allRuns.length === 0 ? (
                <div className="p-8 rounded-3xl bg-slate-900/40 border border-slate-800 text-center text-slate-400 space-y-2">
                  <span className="text-2xl block">📊</span>
                  <p className="text-xs font-bold text-slate-300">Results not yet recorded.</p>
                  <p className="text-[11px] text-slate-500">Run your experiment externally and enter real measurements above to calculate differences.</p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-slate-800">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-bold text-[10px] uppercase">
                        <th className="p-3">Run #</th>
                        <th className="p-3">Metric</th>
                        <th className="p-3">Baseline</th>
                        <th className="p-3">Proposed Method</th>
                        <th className="p-3">Abs Diff</th>
                        <th className="p-3">Rel Gain</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-slate-950/60">
                      {allRuns.map((r) => {
                        const bMetric = r.results.find(res => res.method_type === 'baseline');
                        const pMetric = r.results.find(res => res.method_type === 'proposed');
                        const metricName = (bMetric || pMetric)?.metric_name || 'Metric';
                        const diffData = getMetricDiff(metricName);

                        return (
                          <tr key={r.id} className="hover:bg-slate-900/50 transition-all">
                            <td className="p-3 font-mono font-bold text-indigo-400">Run #{r.run_number}</td>
                            <td className="p-3 font-bold text-slate-200">{metricName}</td>
                            <td className="p-3 text-slate-300 font-mono">{bMetric ? `${bMetric.metric_value} ${bMetric.unit || ''}` : <span className="text-slate-500 italic">Not recorded</span>}</td>
                            <td className="p-3 text-indigo-300 font-mono font-bold">{pMetric ? `${pMetric.metric_value} ${pMetric.unit || ''}` : <span className="text-slate-500 italic">Not recorded</span>}</td>
                            <td className="p-3 font-mono font-bold text-emerald-400">
                              {diffData ? (diffData.absDiff > 0 ? `+${diffData.absDiff}` : diffData.absDiff) : <span className="text-slate-500 italic">N/A</span>}
                            </td>
                            <td className="p-3 font-mono font-bold text-emerald-300">
                              {diffData ? diffData.relDiff : <span className="text-slate-500 italic">Comparison unavailable</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: REPRODUCIBILITY */}
        {activeTab === 'reproducibility' && (
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center justify-between">
              <span>🔁</span> 10-Point Reproducibility Checklist ({checklist.length}/10 Completed)
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {DEFAULT_CHECKLIST.map((item, idx) => {
                const isDone = checklist.includes(item);
                return (
                  <div
                    key={idx}
                    onClick={() => toggleChecklist(item)}
                    className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 ${
                      isDone ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200' : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <input type="checkbox" checked={isDone} onChange={() => {}} className="mt-0.5 rounded accent-emerald-500" />
                    <span className="text-xs font-medium">{item}</span>
                  </div>
                );
              })}
            </div>

            <div className="space-y-2 pt-2">
              <label className="text-[10px] text-slate-400 font-bold block">Experiment Limitations & Failure Notes</label>
              <textarea
                value={limitations}
                onChange={(e) => setLimitations(e.target.value)}
                placeholder="Record dataset imbalance, hardware constraints, or unexpected failure cases..."
                className="w-full h-24 p-3 rounded-2xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none"
              />
            </div>
          </div>
        )}

        {/* FOOTER ACTIONS */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
          <button onClick={exportMarkdown} className="px-4 py-2 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5">
            <span>📝</span> Export Experiment Report (MD)
          </button>

          <button
            onClick={() => handleUpdateStatus('COMPLETED')}
            disabled={saving}
            className="btn-primary py-2 px-6 text-xs font-bold shadow-lg shadow-indigo-500/20"
          >
            {saving ? 'Updating...' : '✓ Mark Experiment Complete'}
          </button>
        </div>

      </div>
    </div>
  );
}
