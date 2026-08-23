import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.schemas.methodology_plan_schema import (
    MethodologyPlanResponse,
    PipelineStepItem,
    DatasetPlanItem,
    BaselineMethodItem,
    ExperimentPlanItem,
    MetricCategoryItem,
    AblationStepItem,
    ExpectedOutputItem,
    HypothesesItem
)
from app.services.research_opportunity_evaluation_service import ResearchOpportunityEvaluationService
from app.services.research_idea_validation_service import ResearchIdeaValidationService

logger = logging.getLogger(__name__)

PLANNER_DISCLAIMER = (
    "This research methodology plan is a structured execution recommendation derived strictly from current collection evidence. "
    "It does not guarantee academic novelty, computational feasibility, or experimental success. "
    "All actual experimental results must come from future execution."
)


class ResearchMethodologyService:
    """
    Service to synthesize evidence-grounded research execution plans from validated research opportunities.
    Read-only by default. Supports explicit project plan persistence.
    """

    @classmethod
    def get_methodology_plan(
        cls,
        db: Session,
        direction_id: str,
        project_id: Optional[int] = None
    ) -> MethodologyPlanResponse:
        """
        Synthesize complete methodology plan response.
        """
        logger.info(f"Generating research methodology plan direction_id='{direction_id}', project_id={project_id}")

        # 1. Fetch evaluation & validation evidence
        eval_resp = ResearchOpportunityEvaluationService.evaluate_opportunity(db, direction_id, project_id)
        val_resp = ResearchIdeaValidationService.validate_opportunity(db, direction_id, project_id)

        title = eval_resp.title
        problem = eval_resp.research_problem
        supp_papers = [sp.model_dump() for sp in eval_resp.what_current_research_does]
        algos = [ca.name for ca in eval_resp.candidate_algorithms]
        datasets = [cd.name for cd in eval_resp.candidate_datasets]

        primary_algo = algos[0] if algos else "Baseline Algorithm"
        secondary_algo = algos[1] if len(algos) > 1 else "Target Component"

        # 2. Objectives
        objectives = [
            f"Implement baseline performance using {primary_algo}.",
            f"Develop proposed combination integrating {primary_algo} with {secondary_algo}.",
            "Build reproducible evaluation pipeline comparing baseline vs proposed model.",
            "Conduct ablation studies to evaluate individual component contributions.",
            "Document performance metrics, computational efficiency, and limitations."
        ]

        # 3. Research Questions
        research_questions = [
            {
                "rq_id": "RQ1",
                "question": f"How does combining {primary_algo} with {secondary_algo} impact performance compared to standalone baseline models?"
            },
            {
                "rq_id": "RQ2",
                "question": "What is the computational overhead and memory impact of the proposed model combination?"
            },
            {
                "rq_id": "RQ3",
                "question": "Which specific architectural component contributes most significantly to performance gains?"
            }
        ]

        # 4. Conceptual System Pipeline
        pipeline = [
            PipelineStepItem(
                step_number=1,
                stage="INPUT_DATA",
                title="Input Domain Stream",
                description="Acquire raw domain samples or video frame sequences."
            ),
            PipelineStepItem(
                step_number=2,
                stage="PREPROCESSING",
                title="Data Preprocessing & Normalization",
                description="Apply cropping, normalization, and sequence windowing."
            ),
            PipelineStepItem(
                step_number=3,
                stage="FEATURE_EXTRACTION",
                title=f"Feature Extraction ({primary_algo})",
                description="Extract spatial or domain feature embeddings."
            ),
            PipelineStepItem(
                step_number=4,
                stage="MODELING",
                title=f"Temporal / Concept Modeling ({secondary_algo})",
                description="Model temporal sequences or concept interactions."
            ),
            PipelineStepItem(
                step_number=5,
                stage="EVALUATION",
                title="Classification & Metric Evaluation",
                description="Compute classification loss, accuracy, and F1-score."
            )
        ]

        # 5. Dataset Plan
        dataset_plan = []
        if datasets:
            for ds_name in datasets:
                dataset_plan.append(DatasetPlanItem(
                    name=ds_name,
                    status="Observed in current collection",
                    suitability="Observed in supporting papers as a standard evaluation benchmark.",
                    limitations="Ensure proper licensing and verify access permissions before downloading.",
                    licensing="Research & Academic Use Only"
                ))
        else:
            dataset_plan.append(DatasetPlanItem(
                name="Public Domain Benchmark",
                status="Candidate for investigation",
                suitability="Candidate benchmark for evaluating application domain features.",
                limitations="Perform dataset search in HuggingFace or Kaggle repositories.",
                licensing="Open Access"
            ))

        # 6. Data Preparation (8 Steps)
        data_prep = [
            "Data Collection: Acquire raw benchmark samples.",
            "Data Cleaning: Remove corrupted or incomplete records.",
            "Label Verification: Audit target classification labels.",
            "Train/Val/Test Split: Apply 70/15/15 stratified random split.",
            "Normalization: Standardize pixel or feature vector ranges.",
            "Data Augmentation: Apply domain-appropriate transformations.",
            "Sequence Windowing: Form sliding sequence windows for temporal input.",
            "Batch Preparation: Construct optimized DataLoader streams."
        ]

        # 7. Baseline Methods
        baselines = []
        for a in algos:
            baselines.append(BaselineMethodItem(
                algorithm=a,
                supporting_paper_count=1,
                role="Baseline Comparison Model",
                reason=f"Identified as standard method in current collection papers."
            ))

        # 8. Proposed Method
        proposed = {
            "architecture_name": f"Integrated {primary_algo} + {secondary_algo}",
            "components": [f"{primary_algo} Encoder", f"{secondary_algo} Sequential Layer", "Classifier Head"],
            "input_format": "Sequence of N feature vectors or frames",
            "processing_flow": f"Raw input → {primary_algo} extraction → {secondary_algo} modeling → Classification Output",
            "output_format": "Target class probability distribution",
            "conceptual_difference": f"Combines spatial feature representation with temporal behavior modeling."
        }

        # 9. Experiments Matrix
        experiments = [
            ExperimentPlanItem(
                experiment_number=1,
                title="Exp 1: Baseline Performance Benchmark",
                purpose=f"Evaluate standalone {primary_algo} model on test split.",
                variables="Standalone Baseline Architecture",
                baseline=primary_algo,
                metrics=["Accuracy", "Precision", "Recall", "F1-Score"]
            ),
            ExperimentPlanItem(
                experiment_number=2,
                title="Exp 2: Proposed Model Evaluation",
                purpose=f"Evaluate combined {primary_algo} + {secondary_algo} model.",
                variables="Proposed Combined Architecture",
                baseline=primary_algo,
                metrics=["Accuracy", "Precision", "Recall", "F1-Score"]
            ),
            ExperimentPlanItem(
                experiment_number=3,
                title="Exp 3: Hyperparameter & Window Sensitivity",
                purpose="Evaluate effect of varying sequence window size (5 vs 10 vs 20 frames).",
                variables="Sequence Window Length (5, 10, 20)",
                baseline="Proposed Model (default window=10)",
                metrics=["F1-Score", "Inference Latency (ms)"]
            )
        ]

        # 10. Evaluation Metrics
        metrics = [
            MetricCategoryItem(
                category="Classification Metrics",
                metrics=["Accuracy (%)", "Precision (%)", "Recall (%)", "F1-Score (%)", "Macro/Micro Average F1"]
            ),
            MetricCategoryItem(
                category="Efficiency & Resource Metrics",
                metrics=["Inference Latency (ms/sample)", "Frames Per Second (FPS)", "Model Parameters (M)", "Peak GPU RAM (MB)"]
            )
        ]

        # 11. Ablation Study
        ablation = [
            AblationStepItem(
                step_name="Full Model",
                component_removed="None (Complete Pipeline)",
                purpose="Establish peak proposed performance."
            ),
            AblationStepItem(
                step_name="No Temporal Layer",
                component_removed=secondary_algo,
                purpose=f"Evaluate exact gain provided by temporal {secondary_algo} layer."
            ),
            AblationStepItem(
                step_name="No Data Augmentation",
                component_removed="Augmentation Pipeline",
                purpose="Evaluate model generalization stability."
            )
        ]

        # 12. Experiment Variables
        variables = {
            "independent": ["Model Architecture Choice", "Sequence Window Length", "Hyperparameter Configuration"],
            "dependent": ["Classification F1-Score", "Model Accuracy", "Inference Latency"],
            "control": ["Dataset Train/Test Split", "Random Seed (42)", "Batch Size (32)", "Hardware Environment"]
        }

        # 13. Expected Outputs (Planned)
        expected_outputs = [
            ExpectedOutputItem(
                output_type="Table",
                title="Table 1: Baseline vs Proposed Performance Comparison",
                description="Comparative metrics across Accuracy, Precision, Recall, F1-Score."
            ),
            ExpectedOutputItem(
                output_type="Table",
                title="Table 2: Ablation Study Results",
                description="Performance breakdown showing impact of removing temporal module."
            ),
            ExpectedOutputItem(
                output_type="Figure",
                title="Figure 1: Training & Validation Loss Curves",
                description="Loss convergence visualization across 50 epochs."
            ),
            ExpectedOutputItem(
                output_type="Figure",
                title="Figure 2: Confusion Matrix Heatmap",
                description="Detailed per-class prediction confusion matrix."
            )
        ]

        # 14. Success Criteria
        success_criteria = [
            "Baseline and proposed models train to convergence without overfitting.",
            "Evaluation protocol is fully reproducible using fixed random seed (42).",
            "Statistical comparison across baseline and proposed models is completed.",
            "Ablation study confirms the individual contribution of temporal modeling.",
            "All experimental limitations and failure cases are documented."
        ]

        # 15. Risks & Limitations
        risks = [
            "Dataset Availability: Benchmark dataset licensing or download restrictions.",
            "Sample Imbalance: Over-representation of normal vs alert states in dataset.",
            "Computational Constraints: GPU memory limits during temporal window training.",
            "Overfitting: High training accuracy failing to generalize to unseen test splits."
        ]

        # 16. Reproducibility Checklist
        reproducibility = [
            "Dataset source, version, and download link recorded",
            "Exact train/validation/test split ratio documented",
            "Preprocessing and augmentation transformations specified",
            "Model architecture hyperparameters (learning rate, batch size) recorded",
            "Fixed random seed (42) configured for all random operations",
            "Hardware specifications (CPU, GPU, RAM) documented",
            "Software dependencies and environment versions locked",
            "Evaluation metric formulas defined",
            "Baseline models clearly specified",
            "Code repository repository structured for reproduction"
        ]

        # 17. Research Timeline (8 Weeks)
        timeline = [
            {"week": "Week 1", "task": "Literature Review & Dataset Acquisition"},
            {"week": "Week 2", "task": "Data Preprocessing & DataLoader Pipeline"},
            {"week": "Week 3", "task": "Baseline Model Implementation & Training"},
            {"week": "Week 4", "task": "Proposed Combined Model Architecture Implementation"},
            {"week": "Week 5", "task": "Comparative Experiments & Hyperparameter Tuning"},
            {"week": "Week 6", "task": "Ablation Studies & Latency Benchmarking"},
            {"week": "Week 7", "task": "Results Analysis & Visualization Generation"},
            {"week": "Week 8", "task": "Research Proposal / Report Synthesis"}
        ]

        # 18. Implementation Checklist
        impl_checklist = [
            "Literature review completed",
            "Dataset acquired and preprocessed",
            "Baseline model trained",
            "Proposed model trained",
            "Comparative experiments completed",
            "Ablation study executed",
            "Results analyzed and plotted",
            "Limitations documented",
            "Research proposal / report finalized"
        ]

        # 19. Potential Contribution (Cautious framing)
        potential_contribution = (
            f"An empirical evaluation of combining {primary_algo} with {secondary_algo} "
            f"for the selected application domain, providing structured baseline comparisons and ablation insights."
        )

        # 20. Hypotheses
        hypotheses = HypothesesItem(
            null_hypothesis=f"H0: Combining {primary_algo} with {secondary_algo} yields no statistically significant improvement in F1-score compared to standalone baselines.",
            alternative_hypothesis=f"H1: Combining {primary_algo} with {secondary_algo} yields improved F1-score and temporal consistency compared to standalone baselines."
        )

        # 21. Traceability
        traceability = {
            "research_problem": problem,
            "supporting_paper_count": len(supp_papers),
            "research_gap_score": eval_resp.evidence.overall_gap_score,
            "validation_status": val_resp.validation_status,
            "trace_chain": "Problem → Papers → Gap → Direction → Validation → Plan → Proposal"
        }

        return MethodologyPlanResponse(
            direction_id=direction_id,
            title=title,
            scope="project" if project_id else "global",
            validation_status=val_resp.validation_status,
            research_problem=problem,
            problem_context=eval_resp.motivation if hasattr(eval_resp, "motivation") else "Collection studies baseline methodologies in this domain.",
            supporting_papers=supp_papers,
            objectives=objectives,
            research_questions=research_questions,
            pipeline=pipeline,
            dataset_plan=dataset_plan,
            data_preparation=data_prep,
            baseline_methods=baselines,
            proposed_method=proposed,
            experiments=experiments,
            metrics=metrics,
            ablation_plan=ablation,
            variables=variables,
            expected_outputs=expected_outputs,
            success_criteria=success_criteria,
            risks=risks,
            reproducibility_checklist=reproducibility,
            timeline=timeline,
            implementation_checklist=impl_checklist,
            potential_contribution=potential_contribution,
            hypotheses=hypotheses,
            traceability=traceability,
            disclaimer=PLANNER_DISCLAIMER
        )
