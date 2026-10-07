import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function RecordResultModal({ experiment, projectId, onClose, onSaveSuccess }) {
  if (!experiment) return null;

  const expType = (experiment.experiment_type || 'BASELINE_COMPARISON').toUpperCase();

  // Mode: 'SINGLE' for Baseline-only, Proposed-only, Ablation, Latency; 'DUAL' for Comparative
  const initialIsDual = expType === 'DUAL_COMPARISON';
  const [isDualMode, setIsDualMode] = useState(initialIsDual);

  // Determine method type for single mode
  const singleMethodType = expType === 'BASELINE_COMPARISON' ? 'baseline' :
                           expType === 'ABLATION' ? 'ablation' : 'proposed';

  // Configured metrics
  const defaultMetrics = Array.isArray(experiment.configured_metrics) && experiment.configured_metrics.length > 0
    ? experiment.configured_metrics
    : expType === 'LATENCY_EFFICIENCY'
      ? ['Latency (ms)', 'FPS', 'Memory Usage (MB)', 'Throughput']
      : ['Precision', 'Recall', 'F1-score', 'mAP@0.5', 'IoU'];

  const [metricRows, setMetricRows] = useState(
    defaultMetrics.map(name => ({
      metric_name: name,
      actual_val: '',
      baseline_val: '',
      proposed_val: '',
      unit: name.toLowerCase().includes('latency') ? 'ms' : name.toLowerCase().includes('fps') ? 'fps' : '0-1'
    }))
  );

  const [customMetricName, setCustomMetricName] = useState('');
  const [ablationVariant, setAblationVariant] = useState('');
  const [seed, setSeed] = useState(42);
  const [gpuEnv, setGpuEnv] = useState(experiment.environment_config?.gpu || 'NVIDIA RTX 3090 / Colab T4');
  const [framework, setFramework] = useState('PyTorch 2.2 / CUDA 12.1');
  const [datasetSplit, setDatasetSplit] = useState(experiment.dataset_config?.samples || 'Test Split (80/10/10)');
  const [limitations, setLimitations] = useState(experiment.recorded_limitations || experiment.limitations || '');
  const [notes, setNotes] = useState('Empirical measurement run recorded by researcher.');

  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  const addCustomMetric = () => {
    if (!customMetricName.trim()) return;
    const name = customMetricName.trim();
    if (metricRows.some(r => r.metric_name.toLowerCase() === name.toLowerCase())) return;
    setMetricRows([
      ...metricRows,
      {
        metric_name: name,
        actual_val: '',
        baseline_val: '',
        proposed_val: '',
        unit: name.toLowerCase().includes('latency') ? 'ms' : name.toLowerCase().includes('fps') ? 'fps' : '0-1'
      }
    ]);
    setCustomMetricName('');
  };

  const removeMetricRow = (idx) => {
    setMetricRows(metricRows.filter((_, i) => i !== idx));
  };

  const handleRowChange = (idx, field, value) => {
    const updated = [...metricRows];
    updated[idx][field] = value;
    setMetricRows(updated);

    if (validationErrors[`${idx}_${field}`]) {
      setValidationErrors(prev => {
        const next = { ...prev };
        delete next[`${idx}_${field}`];
        return next;
      });
    }
  };

  const validateInputs = () => {
    const errs = {};
    let hasAnyValue = false;

    metricRows.forEach((row, idx) => {
      const checkFields = isDualMode ? ['baseline_val', 'proposed_val'] : ['actual_val'];

      checkFields.forEach(field => {
        const val = (row[field] || '').trim();
        if (val !== '') {
          hasAnyValue = true;
          const num = Number(val);
          if (isNaN(num)) {
            errs[`${idx}_${field}`] = 'Must be numeric';
          } else {
            const mName = row.metric_name.toLowerCase();
            // Validate 0-1 metrics
            if (['precision', 'recall', 'f1', 'f1-score', 'map', 'map@0.5', 'iou', 'accuracy'].some(m => mName.includes(m))) {
              if (num < 0 || num > 1) {
                if (num > 1 && num <= 100) {
                  // Percentage entered, acceptable
                } else {
                  errs[`${idx}_${field}`] = 'Expected range 0 to 1 (or 0-100%)';
                }
              }
            }
            // Validate positive values for latency/fps/error
            if (['latency', 'fps', 'error', 'loss', 'memory'].some(m => mName.includes(m)) && num < 0) {
              errs[`${idx}_${field}`] = 'Must be non-negative';
            }
          }
        }
      });
    });

    if (!hasAnyValue) {
      setErrorMsg('Please enter at least one verified empirical measurement value.');
      return false;
    }

    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!validateInputs()) return;

    setSaving(true);
    try {
      // 1. Create Experiment Run
      const runRes = await apiService.createExperimentRun(projectId, experiment.experiment_id || experiment.id, {
        seed: Number(seed) || 42,
        notes: `${notes} [Variant: ${ablationVariant || 'Default'} | Framework: ${framework} | Hardware: ${gpuEnv}]`
      });
      const runId = runRes.data.id;

      // 2. Format Results Payload
      const resultsToCreate = [];
      metricRows.forEach(row => {
        if (isDualMode) {
          if (row.baseline_val.trim() !== '') {
            resultsToCreate.push({
              metric_name: row.metric_name,
              metric_value: row.baseline_val.trim(),
              unit: row.unit,
              method_type: 'baseline'
            });
          }
          if (row.proposed_val.trim() !== '') {
            resultsToCreate.push({
              metric_name: row.metric_name,
              metric_value: row.proposed_val.trim(),
              unit: row.unit,
              method_type: 'proposed'
            });
          }
        } else {
          if (row.actual_val.trim() !== '') {
            resultsToCreate.push({
              metric_name: row.metric_name,
              metric_value: row.actual_val.trim(),
              unit: row.unit,
              method_type: singleMethodType
            });
          }
        }
      });

      if (resultsToCreate.length > 0) {
        await apiService.recordExperimentResults(projectId, runId, resultsToCreate);
      }

      // 3. Update experiment status to COMPLETED & save limitations
      await apiService.updateProjectExperiment(projectId, experiment.experiment_id || experiment.id, {
        status: 'COMPLETED',
        limitations: limitations || experiment.recorded_limitations || ''
      });

      if (onSaveSuccess) onSaveSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to record empirical results:', err);
      const detail = err.response?.data?.detail || 'Failed to save empirical results.';
      setErrorMsg(detail);
    } finally {
      setSaving(false);
    }
  };

  // Header Title & Section Subtitle based on Experiment Type
  const headerTitle = expType === 'BASELINE_COMPARISON' ? 'RECORD BASELINE MEASUREMENTS' :
                      expType === 'PROPOSED_METHOD' ? 'RECORD PROPOSED METHOD MEASUREMENTS' :
                      expType === 'ABLATION' ? 'RECORD ABLATION MEASUREMENTS' :
                      expType === 'LATENCY_EFFICIENCY' ? 'RECORD LATENCY & PERFORMANCE MEASUREMENTS' :
                      'RECORD EXPERIMENT MEASUREMENTS';

  const headerSubtitle = expType === 'BASELINE_COMPARISON' ? 'Enter actual empirical measurements for the standalone baseline model.' :
                        expType === 'PROPOSED_METHOD' ? 'Enter actual empirical measurements for the proposed model/architecture.' :
                        expType === 'ABLATION' ? 'Enter actual empirical measurements for architectural variants or component removals.' :
                        expType === 'LATENCY_EFFICIENCY' ? 'Enter actual empirical measurements for latency, FPS, memory, or throughput.' :
                        'Enter verified empirical measurements for configured metrics.';

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-16 sm:pt-20 pb-6 px-3 sm:px-4 bg-slate-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="w-full max-w-3xl glass-card rounded-3xl p-6 sm:p-8 border border-indigo-500/30 bg-slate-950 shadow-2xl space-y-6 max-h-[calc(100vh-5rem)] overflow-y-auto custom-scrollbar relative text-xs text-slate-300">

        {/* HEADER */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono font-bold text-[10px]">
                EXP #{experiment.experiment_number || 1}
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-[10px]">
                {expType}
              </span>
            </div>
            <h2 className="text-xl font-black text-slate-100">{experiment.experiment_name || experiment.name}</h2>
            <p className="text-xs text-slate-400">
              {experiment.purpose || 'Record actual experimental measurements for this experiment.'}
            </p>
          </div>

          <button onClick={onClose} className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all font-bold">
            ✕ Close
          </button>
        </div>

        {/* ERROR / VALIDATION BANNER */}
        {errorMsg && (
          <div className="p-3.5 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-semibold flex items-center gap-2">
            <span>⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* SECTION 1: METRIC MEASUREMENTS ENTRY HEADER & MODE TOGGLE */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-2 gap-2">
              <div>
                <h4 className="text-xs font-extrabold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                  <span>📝</span> {headerTitle}
                </h4>
                <p className="text-[11px] text-slate-400">{headerSubtitle}</p>
              </div>

              {/* DUAL VS SINGLE MODE TOGGLE */}
              <button
                type="button"
                onClick={() => setIsDualMode(!isDualMode)}
                className="px-3 py-1 rounded-xl bg-slate-900 border border-slate-700 text-indigo-300 text-[10px] font-bold hover:bg-slate-800 transition-all"
              >
                {isDualMode ? 'Switch to Single Method Mode' : 'Switch to Dual Comparison Mode'}
              </button>
            </div>

            {/* ABLATION VARIANT INPUT (IF ABLATION) */}
            {expType === 'ABLATION' && (
              <div className="p-3 rounded-2xl bg-amber-950/20 border border-amber-500/30 space-y-1">
                <label className="text-[10px] text-amber-300 font-bold block uppercase">Ablation Variant / Removed Component</label>
                <input
                  type="text"
                  value={ablationVariant}
                  onChange={(e) => setAblationVariant(e.target.value)}
                  placeholder="e.g. Variant A (Removed Spatial Transformer Module)"
                  className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs outline-none"
                />
              </div>
            )}

            {/* METRICS ENTRY TABLE */}
            <div className="space-y-2">
              {!isDualMode ? (
                /* SINGLE METHOD ENTRY MODE */
                <>
                  <div className="grid grid-cols-12 gap-2 text-[10px] text-slate-400 font-bold uppercase px-2">
                    <div className="col-span-6">Metric Name</div>
                    <div className="col-span-4">Actual Value</div>
                    <div className="col-span-2 text-right">Unit / Remove</div>
                  </div>

                  {metricRows.map((row, idx) => {
                    const err = validationErrors[`${idx}_actual_val`];
                    return (
                      <div key={idx} className="p-2.5 rounded-2xl bg-slate-900/60 border border-slate-800 grid grid-cols-12 gap-2 items-center hover:border-slate-700 transition-all">
                        <div className="col-span-6 font-bold text-slate-200 truncate">
                          {row.metric_name}
                        </div>

                        <div className="col-span-4 relative">
                          <input
                            type="text"
                            value={row.actual_val}
                            onChange={(e) => handleRowChange(idx, 'actual_val', e.target.value)}
                            placeholder="Enter measurement value"
                            className={`w-full px-3 py-1.5 rounded-xl bg-slate-950 border text-indigo-300 font-bold text-xs focus:border-indigo-500 outline-none font-mono ${
                              err ? 'border-rose-500 text-rose-300' : 'border-slate-800'
                            }`}
                          />
                          {err && <span className="text-[9px] text-rose-400 block font-bold mt-0.5">{err}</span>}
                        </div>

                        <div className="col-span-2 flex items-center justify-end gap-2">
                          <span className="text-[10px] text-slate-500 font-mono truncate">{row.unit}</span>
                          <button
                            type="button"
                            onClick={() => removeMetricRow(idx)}
                            className="text-slate-500 hover:text-rose-400 text-xs font-bold px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800"
                            title="Remove Metric"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </>
              ) : (
                /* DUAL COMPARISON ENTRY MODE */
                <>
                  <div className="grid grid-cols-12 gap-2 text-[10px] text-slate-400 font-bold uppercase px-2">
                    <div className="col-span-4">Metric Name</div>
                    <div className="col-span-3">Baseline Value</div>
                    <div className="col-span-3">Proposed Value</div>
                    <div className="col-span-2 text-right">Unit / Remove</div>
                  </div>

                  {metricRows.map((row, idx) => {
                    const errB = validationErrors[`${idx}_baseline_val`];
                    const errP = validationErrors[`${idx}_proposed_val`];

                    return (
                      <div key={idx} className="p-2.5 rounded-2xl bg-slate-900/60 border border-slate-800 grid grid-cols-12 gap-2 items-center hover:border-slate-700 transition-all">
                        <div className="col-span-4 font-bold text-slate-200 truncate">
                          {row.metric_name}
                        </div>

                        <div className="col-span-3 relative">
                          <input
                            type="text"
                            value={row.baseline_val}
                            onChange={(e) => handleRowChange(idx, 'baseline_val', e.target.value)}
                            placeholder="Baseline value"
                            className={`w-full px-2.5 py-1.5 rounded-xl bg-slate-950 border text-slate-200 text-xs focus:border-indigo-500 outline-none font-mono ${
                              errB ? 'border-rose-500 text-rose-300' : 'border-slate-800'
                            }`}
                          />
                          {errB && <span className="text-[9px] text-rose-400 block font-bold mt-0.5">{errB}</span>}
                        </div>

                        <div className="col-span-3 relative">
                          <input
                            type="text"
                            value={row.proposed_val}
                            onChange={(e) => handleRowChange(idx, 'proposed_val', e.target.value)}
                            placeholder="Proposed value"
                            className={`w-full px-2.5 py-1.5 rounded-xl bg-slate-950 border text-indigo-300 font-bold text-xs focus:border-indigo-500 outline-none font-mono ${
                              errP ? 'border-rose-500 text-rose-300' : 'border-slate-800'
                            }`}
                          />
                          {errP && <span className="text-[9px] text-rose-400 block font-bold mt-0.5">{errP}</span>}
                        </div>

                        <div className="col-span-2 flex items-center justify-end gap-2">
                          <span className="text-[10px] text-slate-500 font-mono truncate">{row.unit}</span>
                          <button
                            type="button"
                            onClick={() => removeMetricRow(idx)}
                            className="text-slate-500 hover:text-rose-400 text-xs font-bold px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800"
                            title="Remove Metric"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}
            </div>

            {/* ADD CUSTOM METRIC INPUT */}
            <div className="flex items-center gap-2 pt-1">
              <input
                type="text"
                value={customMetricName}
                onChange={(e) => setCustomMetricName(e.target.value)}
                placeholder="Add additional metric (e.g. mAP@0.5:0.95, Attribution Stability, Latency)"
                className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-indigo-500 outline-none flex-1"
              />
              <button
                type="button"
                onClick={addCustomMetric}
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-indigo-300 font-bold text-xs hover:bg-slate-800 transition-all"
              >
                + Add Metric
              </button>
            </div>
          </div>

          {/* SECTION 2: REPRODUCIBILITY METADATA */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-2">
              <span>💻</span> Reproducibility Metadata & Execution Context
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Random Seed</label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Hardware / GPU Environment</label>
                <input
                  type="text"
                  value={gpuEnv}
                  onChange={(e) => setGpuEnv(e.target.value)}
                  placeholder="e.g. NVIDIA RTX 3090 / Colab T4 GPU"
                  className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block font-bold">Software / Framework Version</label>
                <input
                  type="text"
                  value={framework}
                  onChange={(e) => setFramework(e.target.value)}
                  placeholder="e.g. PyTorch 2.2 / CUDA 12.1"
                  className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 block font-bold">Recorded Experiment Limitations / Failure Notes</label>
              <textarea
                value={limitations}
                onChange={(e) => setLimitations(e.target.value)}
                placeholder="Document dataset imbalance, hardware memory constraints, or edge-case failure modes..."
                className="w-full mt-1 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs outline-none h-16"
              />
            </div>
          </div>

          {/* FOOTER ACTIONS */}
          <div className="flex items-center justify-between border-t border-slate-800 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold text-xs"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={saving}
              className="btn-primary py-2 px-6 text-xs font-bold shadow-lg shadow-indigo-500/20 disabled:opacity-50"
            >
              {saving ? 'Saving Measurements...' : '💾 Save Verified Experimental Results'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
