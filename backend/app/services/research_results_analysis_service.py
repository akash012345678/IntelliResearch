import logging
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ResearchExperiment, ExperimentRun, ExperimentResult
from app.schemas.results_analysis_schema import (
    MetricAnalysisItem,
    TradeoffAnalysisItem,
    MultiRunStatsItem,
    AblationAnalysisItem,
    HypothesisAssessmentItem,
    EvidenceStrengthItem,
    ReproducibilitySummaryItem,
    SingleExperimentAnalysisResponse,
    ProjectResultsAnalysisSummaryResponse
)

logger = logging.getLogger(__name__)

LOWER_IS_BETTER_METRICS = {"mae", "mse", "rmse", "latency", "inference time", "memory usage", "loss", "error rate"}


class ResearchResultsAnalysisService:
    """
    Read-only service for analyzing student-recorded experiment results,
    detecting performance trade-offs, evaluating hypotheses, and synthesizing safe conclusions.
    """

    @classmethod
    def _analyze_single_experiment(cls, exp: ResearchExperiment) -> SingleExperimentAnalysisResponse:
        runs = exp.runs or []
        latest_run = runs[-1] if len(runs) > 0 else None
        results = latest_run.results if latest_run else []

        # Group results by metric
        baseline_by_metric = {}
        proposed_by_metric = {}
        for r in results:
            if r.method_type == "baseline":
                baseline_by_metric[r.metric_name] = r
            elif r.method_type == "proposed":
                proposed_by_metric[r.metric_name] = r

        all_metric_names = sorted(list(set(list(baseline_by_metric.keys()) + list(proposed_by_metric.keys()))))
        metrics_analysis: List[MetricAnalysisItem] = []
        improved_metrics = []
        degraded_metrics = []

        for m_name in all_metric_names:
            b_res = baseline_by_metric.get(m_name)
            p_res = proposed_by_metric.get(m_name)

            b_val_str = b_res.metric_value if b_res else None
            p_val_str = p_res.metric_value if p_res else None
            unit = (b_res or p_res).unit if (b_res or p_res) else None

            is_lower = m_name.lower() in LOWER_IS_BETTER_METRICS
            direction = "lower_is_better" if is_lower else "higher_is_better"

            abs_diff = None
            rel_diff_pct = None
            is_improved = None
            interp = "Not enough data recorded to perform comparison."

            if b_val_str is not None and p_val_str is not None:
                try:
                    b_num = float(b_val_str)
                    p_num = float(p_val_str)
                    diff = p_num - b_num
                    abs_diff = round(diff, 4)

                    if b_num != 0:
                        rel_diff_pct = f"{round(((diff) / abs(b_num)) * 100, 2)}%"
                    else:
                        rel_diff_pct = "N/A"

                    if is_lower:
                        is_improved = diff < 0
                    else:
                        is_improved = diff > 0

                    if is_improved:
                        improved_metrics.append(m_name)
                        interp = f"On the recorded {m_name}, the proposed configuration was {abs(abs_diff)} {'lower (better)' if is_lower else 'higher'} than the selected baseline."
                    elif diff == 0:
                        interp = f"On the recorded {m_name}, both baseline and proposed configurations achieved identical values ({b_num})."
                    else:
                        degraded_metrics.append(m_name)
                        interp = f"On the recorded {m_name}, the proposed configuration recorded a {'higher (worse)' if is_lower else 'lower'} value than the baseline (difference: {abs_diff})."

                except ValueError:
                    interp = f"Recorded non-numeric string values ({b_val_str} vs {p_val_str}). Qualitative comparison recorded."

            elif b_val_str is not None:
                interp = f"Only baseline recorded ({b_val_str}). Comparison unavailable until proposed model result is entered."
            elif p_val_str is not None:
                interp = f"Only proposed model recorded ({p_val_str}). Comparison unavailable until baseline result is entered."

            metrics_analysis.append(MetricAnalysisItem(
                metric_name=m_name,
                baseline_value=b_val_str,
                proposed_value=p_val_str,
                unit=unit,
                abs_difference=abs_diff,
                rel_difference_pct=rel_diff_pct,
                direction=direction,
                is_improved=is_improved,
                interpretation=interp
            ))

        # Trade-off Detection
        tradeoffs: List[TradeoffAnalysisItem] = []
        if len(improved_metrics) > 0 and len(degraded_metrics) > 0:
            tradeoffs.append(TradeoffAnalysisItem(
                tradeoff_type=f"Performance Trade-off ({', '.join(improved_metrics)} vs {', '.join(degraded_metrics)})",
                description=f"The proposed configuration showed improvement in {', '.join(improved_metrics)} but recorded higher trade-offs or lower scores in {', '.join(degraded_metrics)}.",
                impact_assessment="Performance trade-off observed. Selection of proposed method depends on application priorities."
            ))

        # Multi-Run Statistics
        multi_run_stats: List[MultiRunStatsItem] = []
        if len(runs) >= 2:
            # Group proposed metric values across runs
            run_vals_by_metric: Dict[str, List[float]] = {}
            for r in runs:
                for res in r.results:
                    if res.method_type == "proposed":
                        try:
                            v = float(res.metric_value)
                            run_vals_by_metric.setdefault(res.metric_name, []).append(v)
                        except ValueError:
                            pass

            for m_n, val_list in run_vals_by_metric.items():
                if len(val_list) >= 2:
                    mean_val = round(sum(val_list) / len(val_list), 4)
                    var_val = sum((x - mean_val) ** 2 for x in val_list) / (len(val_list) - 1)
                    std_dev = round(math.sqrt(var_val), 4)
                    min_v = round(min(val_list), 4)
                    max_v = round(max(val_list), 4)
                    rng_v = round(max_v - min_v, 4)

                    consistency = "LOW_VARIATION" if std_dev <= 0.02 else "MODERATE_VARIATION" if std_dev <= 0.05 else "HIGH_VARIATION"
                    notes_str = f"Evaluated across {len(val_list)} runs. Dispersion std_dev={std_dev}."

                    multi_run_stats.append(MultiRunStatsItem(
                        metric_name=m_n,
                        run_count=len(val_list),
                        mean=mean_val,
                        std_dev=std_dev,
                        min_val=min_v,
                        max_val=max_v,
                        range_val=rng_v,
                        consistency_rating=consistency,
                        notes=notes_str
                    ))

        # Hypothesis Assessment
        status_h = "INSUFFICIENT_DATA"
        obs_summary = "Results not yet recorded or insufficient measurements available."
        acad_expl = "Hypothesis evaluation requires recorded empirical baseline and proposed measurements."

        if len(improved_metrics) > 0 and len(degraded_metrics) == 0:
            status_h = "CONSISTENT_WITH_H1"
            obs_summary = f"Recorded results showed consistent improvements across {', '.join(improved_metrics)}."
            acad_expl = f"Within the parameters of this recorded experiment, the empirical evidence is consistent with alternative hypothesis H1."
        elif len(degraded_metrics) > 0 and len(improved_metrics) == 0:
            status_h = "CONSISTENT_WITH_H0"
            obs_summary = f"Recorded results showed lower performance or no gain over baseline across {', '.join(degraded_metrics)}."
            acad_expl = f"Within this recorded experiment, the empirical evidence does not show performance gains over the baseline."
        elif len(improved_metrics) > 0 and len(degraded_metrics) > 0:
            status_h = "INCONCLUSIVE"
            obs_summary = f"Recorded results showed mixed trends: improvement in {', '.join(improved_metrics)} alongside trade-offs in {', '.join(degraded_metrics)}."
            acad_expl = f"The empirical evidence presents trade-offs, rendering global hypothesis conclusions inconclusive without domain weighting."

        hyp_assess = HypothesisAssessmentItem(
            research_question=exp.research_question,
            hypothesis_h0=exp.hypothesis_h0,
            hypothesis_h1=exp.hypothesis_h1,
            observed_result_summary=obs_summary,
            assessment_status=status_h,
            academic_explanation=acad_expl
        )

        # Evidence Strength Rating
        factors = []
        score = 0
        if len(results) > 0:
            score += 25
            factors.append("Actual results recorded")
        if len(baseline_by_metric) > 0 and len(proposed_by_metric) > 0:
            score += 25
            factors.append("Both baseline and proposed methods recorded")
        if len(runs) >= 2:
            score += 20
            factors.append(f"Multiple runs executed ({len(runs)} runs)")
        checklist_done = len(exp.reproducibility_checklist or [])
        if checklist_done >= 5:
            score += 20
            factors.append(f"Reproducibility checklist partially complete ({checklist_done}/10)")
        if exp.limitations:
            score += 10
            factors.append("Experiment limitations documented")

        rating_str = "STRONGER" if score >= 80 else "MODERATE" if score >= 50 else "LIMITED" if score >= 25 else "INSUFFICIENT"
        ev_strength = EvidenceStrengthItem(
            rating=rating_str,
            score=score,
            factors=factors,
            explanation=f"Evidence strength rated as {rating_str} ({score}/100) based on documentation completeness."
        )

        # Reproducibility Summary
        repro_summary = ReproducibilitySummaryItem(
            checklist_score=checklist_done,
            completed_items=exp.reproducibility_checklist or [],
            missing_items=[],
            reproducibility_level="HIGH" if checklist_done >= 8 else "MODERATE" if checklist_done >= 5 else "LOW"
        )

        # Safe Conclusion & Recommended Next Steps
        ds_name = exp.dataset_config.get("dataset_name", "the dataset") if exp.dataset_config else "the dataset"
        base_name = exp.baseline_config.get("algorithm", "the baseline") if exp.baseline_config else "the baseline"
        prop_name = exp.proposed_config.get("architecture", "the proposed model") if exp.proposed_config else "the proposed model"

        if len(results) == 0:
            safe_conc = f"Experiment '{exp.name}' is planned. Experimental results have not yet been recorded."
            next_steps = [
                "Execute the experiment externally in your preferred ML environment.",
                "Record baseline and proposed metric measurements in the Experiment Workspace.",
                "Log random seed and hardware environment for reproducibility."
            ]
        else:
            safe_conc = f"This experiment evaluated {prop_name} against {base_name} on {ds_name}. "
            if len(improved_metrics) > 0:
                safe_conc += f"On the recorded data, {prop_name} achieved higher scores in {', '.join(improved_metrics)}. "
            if len(degraded_metrics) > 0:
                safe_conc += f"However, trade-offs were observed in {', '.join(degraded_metrics)}. "
            safe_conc += "These observations apply strictly to the recorded experiment run(s); broader validation across secondary datasets is recommended."

            next_steps = []
            if len(runs) < 2:
                next_steps.append("Execute additional runs with varied random seeds to evaluate variance.")
            if not exp.limitations:
                next_steps.append("Document dataset and hardware limitations.")
            if checklist_done < 8:
                next_steps.append("Complete missing reproducibility checklist fields.")
            if len(next_steps) == 0:
                next_steps.append("Proceed to integrate recorded findings into your draft research proposal.")

        return SingleExperimentAnalysisResponse(
            experiment_id=exp.id,
            experiment_name=exp.name,
            experiment_type=exp.experiment_type,
            status=exp.status,
            dataset_name=ds_name,
            baseline_alg=base_name,
            proposed_arch=prop_name,
            run_count=len(runs),
            metrics_count=len(all_metric_names),
            metrics_analysis=metrics_analysis,
            tradeoffs=tradeoffs,
            multi_run_stats=multi_run_stats,
            ablation_analysis=[],
            hypothesis_assessment=hyp_assess,
            evidence_strength=ev_strength,
            reproducibility=repro_summary,
            recorded_limitations=exp.limitations,
            safe_conclusion=safe_conc,
            recommended_next_steps=next_steps
        )

    @classmethod
    def get_project_results_analysis(cls, db: Session, project_id: int) -> ProjectResultsAnalysisSummaryResponse:
        """
        Aggregate results analysis across all experiments in a research project.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        exps = project.experiments or []
        exp_analyses: List[SingleExperimentAnalysisResponse] = [cls._analyze_single_experiment(e) for e in exps]

        completed_count = sum(1 for e in exps if e.status == "COMPLETED")
        results_rec_count = sum(1 for e in exps if any(len(r.results) > 0 for r in e.runs))
        baseline_comp_count = sum(1 for e in exps if e.experiment_type == "BASELINE_COMPARISON")
        ablation_count = sum(1 for e in exps if e.experiment_type == "ABLATION")
        multi_run_count = sum(1 for e in exps if len(e.runs) >= 2)
        hyp_count = sum(1 for ea in exp_analyses if ea.hypothesis_assessment.assessment_status != "INSUFFICIENT_DATA")
        lims_count = sum(1 for e in exps if e.limitations and len(e.limitations.trim() if isinstance(e.limitations, str) else "") > 0)

        has_results = results_rec_count > 0
        notice = "Analysis is based only on experimental results recorded in this project." if has_results else "Your experiments are planned, but no experimental results have been recorded yet."

        if not has_results:
            proj_conclusion = "No experimental results have been recorded for this project yet. Complete experiment runs externally and enter verified measurements to generate evidence-based conclusions."
            guidance = [
                "Open the Research Experiment Workspace.",
                "Configure your dataset and model hyperparameters.",
                "Execute your experiments externally (Colab / PyTorch / TensorFlow).",
                "Record real baseline vs proposed measurements."
            ]
        else:
            proj_conclusion = f"Across {results_rec_count} experiment(s) with recorded results in this project, empirical measurements have been systematically evaluated. "
            if hyp_count > 0:
                proj_conclusion += f"Evidence was consistent with alternative hypotheses in {hyp_count} experiment(s). "
            proj_conclusion += "Conclusions remain strictly grounded in student-entered empirical data."
            guidance = [
                "Review baseline vs proposed comparison matrices.",
                "Assess consistency across multi-run statistics.",
                "Export results analysis report or integrate findings into your Research Proposal."
            ]

        return ProjectResultsAnalysisSummaryResponse(
            total_experiments=len(exps),
            completed_experiments=completed_count,
            results_recorded_count=results_rec_count,
            baseline_comparisons_count=baseline_comp_count,
            ablation_experiments_count=ablation_count,
            multi_run_experiments_count=multi_run_count,
            hypotheses_evaluated_count=hyp_count,
            limitations_recorded_count=lims_count,
            has_recorded_results=has_results,
            notice=notice,
            experiments_analysis=exp_analyses,
            project_overall_conclusion=proj_conclusion,
            decision_guidance=guidance
        )
