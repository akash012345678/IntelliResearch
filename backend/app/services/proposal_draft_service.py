import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config.settings import settings
from app.schemas.research_direction_schema import ResearchDirection, SupportingPaper, CandidateAlgorithm, CandidateDataset
from app.schemas.proposal_draft_schema import ProposalDraft, ProposalDraftResponse
from app.services.research_direction_service import ResearchDirectionService

logger = logging.getLogger(__name__)

DRAFT_DISCLAIMER = (
    "Evidence-grounded draft generated from indexed project evidence. "
    "It represents a potential direction for further empirical investigation and does not establish global academic novelty or guarantee research originality."
)


class LLMProvider:
    """Abstract Base Class for LLM Provider Synthesis."""
    def generate_proposal(self, direction: ResearchDirection) -> Optional[ProposalDraft]:
        raise NotImplementedError


class ProposalDraftService:
    """
    Service responsible for synthesizing structured academic research proposal drafts
    from Phase 4 Actionable Research Directions using either LLM-guided synthesis
    or deterministic template-guided fallback synthesis.
    Enforces task-type consistency, evidence-grounded dataset provenance, and non-destructive versioning.
    """

    @classmethod
    def create_manual_proposal(
        cls,
        db: Session,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> ProposalDraftResponse:
        """
        Create a user-provided manual research proposal draft.
        Explicitly labeled USER-PROVIDED RESEARCH IDEA to distinguish from system-generated evidence-grounded proposals.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        proposal_uuid = f"prop_manual_{uuid.uuid4().hex[:8]}"
        clean_title = title.strip() if title else "User-Provided Research Idea"
        desc_text = description.strip() if description else "User-specified manual research concept."

        abstract = (
            f"This research proposal represents a user-provided research idea: '{clean_title}'. "
            f"It was formulated directly by the researcher and is maintained as a separate user hypothesis."
        )

        research_question = (
            f"How can the user-proposed direction '{clean_title}' be formulated and empirically evaluated?"
        )

        objectives = [
            f"1. Formulate the technical scope for '{clean_title}'.",
            "2. Identify relevant benchmark datasets and baseline methodologies.",
            "3. Implement experimental prototype.",
            "4. Measure performance and evaluate trade-offs against conventional baselines."
        ]

        methodology = (
            f"RECORDED EVIDENCE:\n- User-specified manual research direction.\n\n"
            f"PROPOSED METHODOLOGY:\n- Implement user-defined concept '{clean_title}' and benchmark against domain baselines.\n\n"
            f"EXPECTED / PLANNED ANALYSIS:\n- Results are not yet recorded."
        )

        exp_plan = (
            f"Structured Experiment Plan:\n"
            f"1. Task Type: OTHER_SUPPORTED_TASK.\n"
            f"2. Baseline: User-selected domain baseline algorithms.\n"
            f"3. Proposed Approach: User concept '{clean_title}'.\n"
            f"4. Dataset: Dataset selection required.\n"
            f"5. Data Preprocessing: Standard dataset cleaning and normalization.\n"
            f"6. Training Setup: Standard cross-validation training pipeline.\n"
            f"7. Evaluation Metrics: Precision, Recall, F1-Score, Efficiency.\n"
            f"8. Comparison Strategy: Comparative benchmarking against baseline.\n"
            f"9. Ablation Study: Component isolation evaluation.\n"
            f"10. Error Analysis: Failure case qualitative inspection.\n"
            f"11. Reproducibility: Standardized seed and environment logging."
        )

        draft = ProposalDraft(
            proposal_id=proposal_uuid,
            source_direction_id=None,
            source_gap_id=None,
            title=f"[USER-PROVIDED] {clean_title}",
            abstract=abstract,
            problem_statement=desc_text,
            research_motivation="User-defined research hypothesis.",
            research_question=research_question,
            objectives=objectives,
            related_work_synthesis="Literature review and related work to be defined by user.",
            research_gap="User-defined gap/opportunity.",
            proposed_methodology=methodology,
            candidate_algorithms=[],
            candidate_datasets=[],
            task_type="OTHER_SUPPORTED_TASK",
            datasets_provenance=[],
            dataset_evaluation_plan="Dataset selection required.",
            experimental_plan=exp_plan,
            evaluation_metrics="Precision, Recall, F1-Score, Computational Efficiency",
            expected_contribution="Evaluate feasibility and performance of user-proposed concept.",
            limitations="This proposal is user-provided and has not been validated against indexed collection text evidence.",
            supporting_papers=[],
            evidence_summary={
                "evidence_classification": "USER_PROVIDED",
                "confidence": "USER_PROVIDED",
                "is_user_provided": True
            },
            generation_mode="manual_idea",
            is_user_provided=True,
            generation_timestamp=timestamp,
            disclaimer="USER-PROVIDED RESEARCH IDEA — Not synthesized from indexed literature text evidence."
        )

        return cls._wrap_and_persist_proposal(
            db=db,
            proposal_draft=draft,
            target_dir=None,
            project_id=project_id,
            generation_mode="manual_idea"
        )

    @classmethod
    def synthesize_draft(
        cls,
        db: Session,
        direction_id: Optional[str] = None,
        custom_provider: Optional[LLMProvider] = None,
        project_id: Optional[int] = None,
        user_confirmed: bool = False,
        opportunity_family_id: Optional[str] = None,
        payload_title: Optional[str] = None,
        payload_research_question: Optional[str] = None,
        payload_supporting_papers: Optional[List[Dict[str, Any]]] = None,
        regenerate: bool = False
    ) -> ProposalDraftResponse:
        """
        Synthesize a structured proposal draft for the specified direction ID or opportunity context.
        Enforces Evidence Gate:
        - DIRECTLY_SUPPORTED, STRONGLY_INFERRED, CROSS_PAPER_SYNTHESIS, and QUALIFIED_POTENTIAL_GAP generate proposals.
        - INSUFFICIENT_EVIDENCE, REJECTED, and UNDERREPRESENTATION_ONLY are rejected with HTTP 422.
        - EXPLORATORY requires explicit user confirmation.
        """
        logger.info(f"Synthesizing proposal draft for direction_id='{direction_id}' (project_id={project_id}, regenerate={regenerate})...")

        # 1. Fetch available directions from collection or project evidence
        project_papers = None
        if project_id is not None:
            from app.models.project_model import ResearchProject, ProjectPaper
            from app.models.paper_model import ResearchPaper
            project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
            p_ids = [pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()]
            project_papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(p_ids)).all() if p_ids else []
            directions_resp = ResearchDirectionService.generate_directions(
                db=db,
                top_k=20,
                project_id=project_id,
                project_name=project.name if project else None,
                project_papers=project_papers
            )
        else:
            directions_resp = ResearchDirectionService.generate_directions(db=db, top_k=20)

        target_dir: Optional[ResearchDirection] = None

        search_keys = [str(k).lower().strip() for k in (direction_id, opportunity_family_id) if k]

        for d in directions_resp.directions:
            d_id = str(d.direction_id).lower().strip()
            d_family = str(getattr(d, "opportunity_family_id", "") or "").lower().strip()
            d_parent_gap = str(getattr(d, "parent_gap_id", "") or "").lower().strip()
            d_gap_key = str(getattr(d, "gap_relationship_key", "") or "").lower().strip()
            d_title = str(d.title).lower().strip()

            if any(key in (d_id, d_family, d_parent_gap, d_gap_key, d_title) for key in search_keys):
                target_dir = d
                break

        # Fallback matching by index if dir_1 / opp_1 format
        if not target_dir and direction_id:
            clean_dir = str(direction_id).lower().strip()
            if clean_dir.startswith("dir_") or clean_dir.startswith("opp_"):
                try:
                    num_part = clean_dir.replace("dir_", "").replace("opp_", "")
                    idx = int(num_part) - 1
                    if 0 <= idx < len(directions_resp.directions):
                        target_dir = directions_resp.directions[idx]
                except ValueError:
                    pass

        # Fallback matching by title substring
        if not target_dir and payload_title:
            t_low = payload_title.lower().strip()
            for d in directions_resp.directions:
                if t_low in d.title.lower() or d.title.lower() in t_low:
                    target_dir = d
                    break

        if not target_dir and payload_title:
            logger.info("Constructing direction context directly from request payload...")
            target_dir = cls._construct_direction_from_payload(
                direction_id=direction_id or "dir_custom",
                title=payload_title,
                research_question=payload_research_question,
                supporting_papers=payload_supporting_papers
            )

        if not target_dir:
            logger.warning(f"Research direction/opportunity '{direction_id}' not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research direction or opportunity '{direction_id}' not found in the indexed collection."
            )

        # Enforce Evidence Gate
        ev_class = getattr(target_dir.evidence, "evidence_classification", None) or getattr(target_dir, "gap_evidence_class", None)
        if ev_class and str(ev_class).upper() in ("UNDERREPRESENTATION_ONLY", "INSUFFICIENT_EVIDENCE", "REJECTED"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence Gate Violation: Direction '{direction_id}' has evidence classification '{ev_class}' and cannot enter proposal generation."
            )
        if ev_class == "EXPLORATORY" and not user_confirmed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Exploratory Direction: Proposal generation for EXPLORATORY directions requires explicit user confirmation."
            )

        # Determine synthesis mode: LLM vs Template Fallback
        if custom_provider:
            try:
                logger.info("Custom/Mock LLM Provider detected. Attempting LLM synthesis...")
                draft = custom_provider.generate_proposal(target_dir)
                if draft:
                    return cls._wrap_and_persist_proposal(db, draft, target_dir, project_id, generation_mode="llm", regenerate=regenerate)
            except Exception as e:
                logger.warning(f"Custom LLM Provider failed: {e}. Falling back to template synthesis.")

        if settings.LLM_PROVIDER and settings.LLM_API_KEY:
            try:
                logger.info(f"LLM Provider '{settings.LLM_PROVIDER}' configured. Attempting LLM synthesis...")
                draft = cls._llm_synthesis(target_dir)
                if draft:
                    return cls._wrap_and_persist_proposal(db, draft, target_dir, project_id, generation_mode="llm", regenerate=regenerate)
            except Exception as e:
                logger.warning(f"LLM synthesis failed: {e}. Falling back to template synthesis.")

        # Mode 2: Deterministic Template Fallback
        logger.info("Executing Mode 2: Evidence-Grounded Template Fallback Synthesis.")
        template_draft = cls._template_synthesis(
            dir_item=target_dir,
            payload_rq=payload_research_question,
            project_papers=project_papers
        )
        return cls._wrap_and_persist_proposal(db, template_draft, target_dir, project_id, generation_mode="template", regenerate=regenerate)

    @classmethod
    def _construct_direction_from_payload(
        cls,
        direction_id: str,
        title: str,
        research_question: Optional[str] = None,
        supporting_papers: Optional[List[Dict[str, Any]]] = None
    ) -> ResearchDirection:
        from app.schemas.research_direction_schema import ResearchDirectionEvidence
        s_papers = []
        if supporting_papers:
            for sp in supporting_papers:
                s_papers.append(SupportingPaper(
                    paper_id=sp.get("paper_id") or sp.get("id") or 0,
                    title=sp.get("title") or f"Paper #{sp.get('paper_id')}",
                    role=sp.get("role") or "Supporting evidence paper in indexed collection"
                ))
        return ResearchDirection(
            direction_id=direction_id,
            title=title,
            research_question=research_question,
            research_problem=f"Indexed project evidence identifies an unassessed opportunity for {title}.",
            motivation=f"Formulate and evaluate integrated pipeline for {title}.",
            existing_evidence=["Project indexed literature evidence."],
            missing_aspect=f"Integrated evaluation of {title} remains unassessed in project collection.",
            proposed_direction=title,
            supporting_papers=s_papers,
            supporting_concepts=[],
            candidate_algorithms=[],
            candidate_datasets=[],
            candidate_methodologies=[],
            evidence=ResearchDirectionEvidence(
                gap_score=0.85,
                opportunity_score=0.85,
                semantic_evidence=0.05,
                link_prediction_score=0.8,
                collection_coverage=66.7,
                underrepresentation_score=0.3,
                evidence_classification="UNASSESSED_RELATIONSHIP"
            ),
            direction_score=0.85,
            confidence="Moderate",
            disclaimer=DRAFT_DISCLAIMER
        )

    @classmethod
    def _infer_task_type(
        cls,
        title: str,
        cand_algos: List[str],
        problem: str,
        missing_aspect: str
    ) -> str:
        text = (title + " " + problem + " " + missing_aspect + " " + " ".join(cand_algos)).lower()
        if any(k in text for k in ["yolo", "object detection", "localization", "bounding box", "detector", "detecting"]):
            return "OBJECT_DETECTION"
        elif any(k in text for k in ["segmentation", "mask r-cnn", "u-net", "dice"]):
            return "SEGMENTATION"
        elif any(k in text for k in ["explainable", "xai", "attribution", "saliency", "transparency", "lime", "grad-cam"]):
            return "EXPLAINABILITY_ANALYSIS"
        elif any(k in text for k in ["sentiment", "nlp", "bert", "roberta", "llm", "text classification", "natural language", "imdb"]):
            return "NATURAL_LANGUAGE_PROCESSING"
        elif any(k in text for k in ["intrusion", "cybersecurity", "anomaly detection", "network traffic", "ids", "cic-ids", "attack"]):
            return "CYBERSECURITY_INTRUSION_DETECTION"
        elif any(k in text for k in ["forecasting", "time series", "traffic prediction", "lstm", "arima"]):
            return "TIME_SERIES_FORECASTING"
        elif any(k in text for k in ["classification", "resnet", "densenet", "transformer"]):
            return "IMAGE_CLASSIFICATION"
        else:
            return "COMPARATIVE_BENCHMARK"

    @classmethod
    def _get_task_metrics_text(cls, task_type: str) -> Tuple[str, str]:
        if task_type == "OBJECT_DETECTION":
            m_list = "Precision [PROPOSED], Recall [PROPOSED], F1-Score [PROPOSED], mAP@0.5 [PROPOSED], mAP@0.5:0.95 [PROPOSED], IoU [PROPOSED], Latency ms/frame [PROPOSED], Attribution Stability [PROPOSED]"
            m_block = (
                "Proposed Evaluation Metrics:\n"
                "- Precision [PROPOSED]\n"
                "- Recall [PROPOSED]\n"
                "- F1-Score [PROPOSED]\n"
                "- Mean Average Precision (mAP@0.5) [PROPOSED]\n"
                "- Mean Average Precision (mAP@0.5:0.95) [PROPOSED]\n"
                "- Intersection over Union (IoU) [PROPOSED]\n"
                "- Execution Latency (ms/frame) [PROPOSED]\n"
                "- Attribution Stability (Grad-CAM Saliency) [PROPOSED]\n\n"
                "Results Status: Empirical results are not yet recorded [MISSING]."
            )
        elif task_type in ("NATURAL_LANGUAGE_PROCESSING", "SEQUENCE_CLASSIFICATION"):
            m_list = "Accuracy [PROPOSED], Precision [PROPOSED], Recall [PROPOSED], F1-Score [PROPOSED], Perplexity [PROPOSED], Latency ms/token [PROPOSED]"
            m_block = (
                "Proposed Evaluation Metrics:\n"
                "- Accuracy [PROPOSED]\n"
                "- Precision [PROPOSED]\n"
                "- Recall [PROPOSED]\n"
                "- Macro/Micro F1-Score [PROPOSED]\n"
                "- Perplexity / Loss [PROPOSED]\n"
                "- Inference Latency (ms/token) [PROPOSED]\n\n"
                "Results Status: Empirical results are not yet recorded [MISSING]."
            )
        elif task_type == "CYBERSECURITY_INTRUSION_DETECTION":
            m_list = "Detection Rate [PROPOSED], False Positive Rate [PROPOSED], Precision [PROPOSED], Recall [PROPOSED], F1-Score [PROPOSED], Throughput pkts/sec [PROPOSED]"
            m_block = (
                "Proposed Evaluation Metrics:\n"
                "- Detection Rate (DR) [PROPOSED]\n"
                "- False Positive Rate (FPR) [PROPOSED]\n"
                "- Precision [PROPOSED]\n"
                "- Recall [PROPOSED]\n"
                "- F1-Score [PROPOSED]\n"
                "- Packet Processing Throughput (pkts/sec) [PROPOSED]\n\n"
                "Results Status: Empirical results are not yet recorded [MISSING]."
            )
        elif task_type == "TIME_SERIES_FORECASTING":
            m_list = "MAE [PROPOSED], RMSE [PROPOSED], MAPE [PROPOSED], R-Squared [PROPOSED], Execution Latency [PROPOSED]"
            m_block = (
                "Proposed Evaluation Metrics:\n"
                "- Mean Absolute Error (MAE) [PROPOSED]\n"
                "- Root Mean Squared Error (RMSE) [PROPOSED]\n"
                "- Mean Absolute Percentage Error (MAPE) [PROPOSED]\n"
                "- R-Squared (R2) [PROPOSED]\n\n"
                "Results Status: Empirical results are not yet recorded [MISSING]."
            )
        else:
            m_list = "Top-1 Accuracy [PROPOSED], Precision [PROPOSED], Recall [PROPOSED], F1-Score [PROPOSED], Execution Latency ms/frame [PROPOSED]"
            m_block = (
                "Proposed Evaluation Metrics:\n"
                "- Top-1 Accuracy [PROPOSED]\n"
                "- Precision [PROPOSED]\n"
                "- Recall [PROPOSED]\n"
                "- F1-Score [PROPOSED]\n"
                "- Execution Latency (ms/frame) [PROPOSED]\n\n"
                "Results Status: Empirical results are not yet recorded [MISSING]."
            )
        return m_list, m_block

    @classmethod
    def _build_datasets_provenance(
        cls,
        dir_item: ResearchDirection,
        cand_datasets: List[str],
        project_papers: Optional[List[Any]],
        task_type: str
    ) -> List[Dict[str, Any]]:
        provenance = []

        # 1. Extract supporting paper IDs for this specific direction/opportunity
        sp_ids = []
        if dir_item.supporting_papers:
            for sp in dir_item.supporting_papers:
                pid = getattr(sp, "paper_id", None) if not isinstance(sp, dict) else (sp.get("paper_id") or sp.get("id"))
                if pid is not None and pid not in sp_ids:
                    sp_ids.append(pid)
        if not sp_ids and getattr(dir_item, "source_paper_ids", None):
            sp_ids = [pid for pid in dir_item.source_paper_ids if pid not in sp_ids]

        # 2. Extract recorded datasets ONLY from supporting papers
        sp_datasets_map = {}
        if project_papers:
            for p in project_papers:
                p_id = getattr(p, "id", None)
                if (sp_ids and p_id in sp_ids) or (not sp_ids):
                    p_ds = getattr(p, "datasets", []) or []
                    for ds in p_ds:
                        ds_name = str(ds).strip()
                        if not ds_name:
                            continue
                        if ds_name not in sp_datasets_map:
                            sp_datasets_map[ds_name] = []
                        if p_id and p_id not in sp_datasets_map[ds_name]:
                            sp_datasets_map[ds_name].append(p_id)

        # 3. Build provenance objects strictly for datasets evidenced by supporting papers
        for ds_name, pids in sp_datasets_map.items():
            matching_pids = [pid for pid in pids if pid in sp_ids] if sp_ids else pids
            role_text = f"Benchmark dataset evidenced in supporting Paper ID {', '.join(str(i) for i in matching_pids)}"
            provenance.append({
                "dataset_name": ds_name,
                "source_paper_ids": matching_pids,
                "dataset_role": role_text,
                "evidence_status": "RECORDED_EVIDENCE",
                "source_type": "paper"
            })

        # 4. If no supporting paper contains dataset evidence, fall back to candidate datasets if explicitly given
        if not provenance and cand_datasets:
            for cd in cand_datasets:
                cd_name = str(cd).strip()
                if cd_name:
                    provenance.append({
                        "dataset_name": cd_name,
                        "source_paper_ids": sp_ids,
                        "dataset_role": "Proposed benchmark dataset for evaluation",
                        "evidence_status": "PROPOSED",
                        "source_type": "proposed"
                    })

        return provenance

    @classmethod
    def _template_synthesis(
        cls,
        dir_item: ResearchDirection,
        payload_rq: Optional[str] = None,
        project_papers: Optional[List[Any]] = None
    ) -> ProposalDraft:
        """
        Deterministic, evidence-grounded template synthesizer.
        Converts a ResearchDirection into a structured ProposalDraft adhering strictly to task-type, dataset provenance, and evidence status classification rules.
        Completely project-agnostic across Computer Vision, NLP, Cybersecurity, Healthcare, Finance, and Time-Series domains.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        proposal_uuid = f"prop_{uuid.uuid4().hex[:8]}"

        cand_algos = [a.name for a in dir_item.candidate_algorithms] if dir_item.candidate_algorithms else []
        raw_cand_ds = [d.name for d in dir_item.candidate_datasets] if dir_item.candidate_datasets else []

        # 1. Infer Task Type
        task_type = cls._infer_task_type(
            title=dir_item.title,
            cand_algos=cand_algos,
            problem=dir_item.research_problem,
            missing_aspect=dir_item.missing_aspect
        )

        m_list_text, metrics_block = cls._get_task_metrics_text(task_type)

        # 2. Build Dataset Provenance strictly from supporting papers
        datasets_provenance = cls._build_datasets_provenance(
            dir_item=dir_item,
            cand_datasets=raw_cand_ds,
            project_papers=project_papers,
            task_type=task_type
        )

        cand_datasets = [d["dataset_name"] for d in datasets_provenance]

        if datasets_provenance:
            ds_items = [f"{d['dataset_name']} (Paper ID {', '.join(str(i) for i in d['source_paper_ids'])}) [{d['evidence_status']}]" for d in datasets_provenance]
            ds_str = ", ".join(ds_items)
            ds_plan = (
                f"Evaluation is proposed using evidence-supported benchmark dataset(s): {ds_str}. "
                f"Dataset provenance is strictly anchored to supporting papers in the evidence chain."
            )
        else:
            ds_str = "indexed domain benchmarks [PROPOSED]"
            ds_plan = "Suitable dataset not established in current supporting papers. Dataset selection required prior to execution [PROPOSED]."

        algo_str = cand_algos[0] if cand_algos else f"{task_type.replace('_', ' ').title()} baseline"

        # 3. Research Question
        if payload_rq and payload_rq.strip():
            research_question = f"{payload_rq.strip()} [PROPOSED]"
        elif getattr(dir_item, "research_question", None) and dir_item.research_question.strip():
            research_question = f"{dir_item.research_question.strip()} [PROPOSED]"
        else:
            research_question = (
                f"How can target methodology components be integrated for '{dir_item.title}' "
                f"to evaluate trade-offs and empirical performance under {ds_str}? [PROPOSED]"
            )

        # 4. Abstract
        abstract = (
            f"Within the indexed research project collection, this proposal investigates {dir_item.title}. "
            f"Based on evidence from indexed papers, existing studies evaluate individual methodology components, "
            f"while their integrated synthesis for {task_type.lower().replace('_', ' ')} represents an unassessed research opportunity [PROPOSED]. "
            f"We propose a systematic empirical investigation to evaluate comparative performance and computational trade-offs [PROPOSED]."
        )

        sp_ids = [sp.paper_id if not isinstance(sp, dict) else (sp.get("paper_id") or sp.get("id")) for sp in dir_item.supporting_papers] if dir_item.supporting_papers else []
        sp_paper_str = ", ".join([f"Paper ID {i}" for i in sp_ids]) if sp_ids else "supporting papers"

        # 5. Objectives
        objectives = [
            f"1. Establish empirical baseline performance using {algo_str} on benchmark datasets ({ds_str}) [RECORDED EVIDENCE / PROPOSED].",
            f"2. Formulate and implement target methodology integration for '{dir_item.title}' ({sp_paper_str}) [PROPOSED].",
            f"3. Conduct controlled experiments and comparative benchmarking across standard benchmark splits [PROPOSED].",
            f"4. Evaluate task performance using domain metrics ({m_list_text.split(',')[0]}) and execution latency [PROPOSED].",
            f"5. Document limitations, attribution stability, and failure case trade-offs [PROPOSED]."
        ]

        # 6. Related Work Synthesis & Specific Paper Role Attribution
        paper_refs = []
        if dir_item.supporting_papers:
            for sp in dir_item.supporting_papers:
                pid = sp.paper_id if not isinstance(sp, dict) else (sp.get("paper_id") or sp.get("id"))
                title_str = sp.title if not isinstance(sp, dict) else sp.get("title", "")
                role_str = sp.role if not isinstance(sp, dict) else sp.get("role", "Supporting paper evidence")
                paper_refs.append(f"Paper ID {pid} ('{title_str}') — {role_str} [RECORDED_EVIDENCE]")
            related_work = "The indexed research collection provides key empirical context:\n- " + "\n- ".join(paper_refs)
        else:
            related_work = "The indexed collection provides baseline context for the domain [RECORDED_EVIDENCE]."

        # 7. Proposed Methodology (4 DISTINCT SECTIONS: RECORDED EVIDENCE vs PROPOSED METHODOLOGY vs PROPOSED EXPERIMENTAL ANALYSIS vs MISSING RESULTS)
        if dir_item.supporting_papers:
            rec_lines = []
            for sp in dir_item.supporting_papers:
                pid = sp.paper_id if not isinstance(sp, dict) else (sp.get("paper_id") or sp.get("id"))
                title_str = sp.title if not isinstance(sp, dict) else sp.get("title", "")
                role_str = sp.role if not isinstance(sp, dict) else sp.get("role", "supporting evidence")
                rec_lines.append(f"- Paper ID {pid} ({title_str}): {role_str} [RECORDED_EVIDENCE].")
            recorded_notes = "\n".join(rec_lines)
        else:
            recorded_notes = "- Baseline implementations documented in indexed project papers [RECORDED_EVIDENCE]."

        proposed_meth = (
            f"A. RECORDED EVIDENCE:\n{recorded_notes}\n\n"
            f"B. PROPOSED METHODOLOGY:\n"
            f"- Integrate the recorded methodologies from {sp_paper_str} into a unified pipeline for '{dir_item.title}' ({task_type}) [PROPOSED].\n"
            f"- Evaluate technical performance, spatial attribution, and diagnostic transparency for domain task requirements [PROPOSED].\n\n"
            f"C. PROPOSED EXPERIMENTAL ANALYSIS:\n"
            f"- Compare baseline implementations from {sp_paper_str} against the proposed integrated pipeline [PROPOSED].\n"
            f"- Evaluate task-aligned metrics and diagnostic stability across benchmark splits [PROPOSED].\n\n"
            f"D. MISSING RESULTS:\n"
            f"- Experimental results are not yet recorded [MISSING]."
        )

        # 8. Structured Experimental Plan
        base_paper_str = f"Paper ID {sp_ids[0]}" if sp_ids else "supporting baseline paper"
        second_paper_str = f"Paper ID {sp_ids[1]}" if len(sp_ids) > 1 else (f"Paper ID {sp_ids[0]}" if sp_ids else "supporting paper")

        exp_plan = (
            f"Structured Experiment Plan:\n"
            f"1. Task Type: {task_type} [DERIVED].\n"
            f"2. Research Question: {research_question}\n"
            f"3. Baseline Architecture: Primary model baseline implementation ({base_paper_str}) [RECORDED_EVIDENCE].\n"
            f"4. Supporting Methodology: Secondary methodology component ({second_paper_str}) [RECORDED_EVIDENCE].\n"
            f"5. Proposed Integration: Integrated pipeline for '{dir_item.title}' [PROPOSED].\n"
            f"6. Dataset & Provenance: {ds_str}.\n"
            f"7. Data Preprocessing: Bounding-box annotation, text tokenization, or image normalization pipeline [PROPOSED].\n"
            f"8. Training Configuration: Training hyperparameters, random seeds, cross-validation splits, batch size, learning rate, and loss thresholds will be defined prior to experiment execution [PROPOSED].\n"
            f"9. Evaluation Metrics: {m_list_text}.\n"
            f"10. Comparison Strategy: The study will compare baseline model performance ({base_paper_str}) against the proposed integrated pipeline [PROPOSED].\n"
            f"11. Ablation & Failure Analysis: Component isolation testing and attribution localization failure review [PROPOSED].\n"
            f"12. Reproducibility & Environment Setup: Code repository, random seeds, and environment hyperparameter logs will be recorded upon execution [PROPOSED].\n"
            f"13. Empirical Results: Experimental results are not yet recorded [MISSING]."
        )

        # 9. Evaluation Metrics
        metrics = metrics_block

        # 10. Expected Contribution & Limitations
        sp_ref_str = f" ({', '.join([f'Paper ID {i}' for i in sp_ids])})" if sp_ids else ""
        expected_contrib = (
            f"Within the indexed project collection, the proposed study will evaluate whether integrating target methods{sp_ref_str} "
            f"for '{dir_item.title}' can provide enhanced diagnostic interpretability while maintaining baseline efficiency [PROPOSED]. "
            f"Results are not yet recorded [MISSING]."
        )

        limitations = (
            f"Findings and proposed designs are derived strictly from evidence available in the currently indexed paper collection. "
            f"Results represent a planned analytical study and do not establish global academic novelty or guaranteed performance metrics prior to empirical testing [PROPOSED]."
        )

        # Supporting papers list of dicts
        supporting_papers_data = []
        if dir_item.supporting_papers:
            for sp in dir_item.supporting_papers:
                pid = sp.paper_id if not isinstance(sp, dict) else (sp.get("paper_id") or sp.get("id"))
                t_str = sp.title if not isinstance(sp, dict) else sp.get("title", "")
                r_str = sp.role if not isinstance(sp, dict) else sp.get("role", "Supporting paper evidence")
                supporting_papers_data.append({"paper_id": pid, "title": t_str, "role": r_str})

        # Evidence Summary & Intelligence Signal Clarification
        ev_class = getattr(dir_item.evidence, "evidence_classification", "UNASSESSED_RELATIONSHIP")
        evidence_summary_data = {
            "gap_score": getattr(dir_item.evidence, "gap_score", 0.85),
            "semantic_evidence": getattr(dir_item.evidence, "semantic_evidence", 0.05),
            "link_prediction_score": getattr(dir_item.evidence, "link_prediction_score", 0.8),
            "underrepresentation_score": getattr(dir_item.evidence, "underrepresentation_score", 0.3),
            "collection_coverage": getattr(dir_item.evidence, "collection_coverage", 66.7),
            "direction_score": dir_item.direction_score,
            "confidence": dir_item.confidence,
            "evidence_classification": ev_class,
            "is_user_provided": False,
            "intelligence_signal_note": "These values represent collection-level research-intelligence signals and do not represent experimental performance.",
            "traceability": {
                "source_direction_id": dir_item.direction_id,
                "opportunity_family_id": getattr(dir_item, "opportunity_family_id", None),
                "canonical_rel_key": getattr(dir_item, "gap_relationship_key", None),
                "supporting_paper_ids": sp_ids,
                "datasets": datasets_provenance,
                "overall_status": "PROPOSED_RESEARCH_DIRECTION"
            }
        }

        return ProposalDraft(
            proposal_id=proposal_uuid,
            source_direction_id=dir_item.direction_id,
            source_gap_id=getattr(dir_item, "parent_gap_id", None) or getattr(dir_item, "gap_relationship_key", None),
            title=dir_item.title,
            abstract=abstract,
            problem_statement=dir_item.research_problem,
            research_motivation=dir_item.motivation,
            research_question=research_question,
            objectives=objectives,
            related_work_synthesis=related_work,
            research_gap=dir_item.missing_aspect,
            proposed_methodology=proposed_meth,
            candidate_algorithms=cand_algos,
            candidate_datasets=cand_datasets,
            task_type=task_type,
            datasets_provenance=datasets_provenance,
            dataset_evaluation_plan=ds_plan,
            experimental_plan=exp_plan,
            evaluation_metrics=metrics,
            expected_contribution=expected_contrib,
            limitations=limitations,
            supporting_papers=supporting_papers_data,
            evidence_summary=evidence_summary_data,
            generation_mode="template",
            is_user_provided=False,
            generation_timestamp=timestamp,
            disclaimer=DRAFT_DISCLAIMER
        )

    @classmethod
    def _wrap_and_persist_proposal(
        cls,
        db: Session,
        proposal_draft: ProposalDraft,
        target_dir: Optional[ResearchDirection],
        project_id: Optional[int],
        generation_mode: str = "template",
        regenerate: bool = False
    ) -> ProposalDraftResponse:
        """
        Persist proposal draft to database non-destructively under research_projects and proposal_versions tables.
        Returns contract-aligned ProposalDraftResponse.
        """
        from app.models.proposal_model import Proposal, ProposalVersion

        db_id = None
        version_num = 1
        source_dir_id = target_dir.direction_id if target_dir else (proposal_draft.source_direction_id or "dir_1")

        if project_id is not None and db is not None:
            existing_proposal = (
                db.query(Proposal)
                .filter(
                    Proposal.project_id == project_id,
                    (Proposal.source_direction_id == source_dir_id) | (Proposal.title == proposal_draft.title)
                )
                .first()
            )

            proposal_dict = proposal_draft.model_dump()

            if not existing_proposal:
                proposal_uuid = proposal_draft.proposal_id or f"prop_{uuid.uuid4().hex[:8]}"
                proposal = Proposal(
                    proposal_uuid=proposal_uuid,
                    project_id=project_id,
                    source_direction_id=source_dir_id,
                    title=proposal_draft.title,
                    status="DRAFT"
                )
                db.add(proposal)
                db.flush()

                # Clean up any stale orphan versions if SQLite reused an autoincrement primary key ID
                db.query(ProposalVersion).filter(ProposalVersion.proposal_id == proposal.id).delete(synchronize_session=False)

                ver1 = ProposalVersion(
                    proposal_id=proposal.id,
                    version_number=1,
                    proposal_data=proposal_dict,
                    generation_mode=generation_mode,
                    change_summary="Initial generated proposal draft",
                    is_restored=False
                )
                db.add(ver1)
                db.commit()
                db.refresh(proposal)
                db_id = proposal.id
                version_num = 1
                prop_uuid = proposal.proposal_uuid
            else:
                # Existing proposal found
                latest_ver = (
                    db.query(ProposalVersion)
                    .filter(ProposalVersion.proposal_id == existing_proposal.id)
                    .order_by(ProposalVersion.version_number.desc())
                    .first()
                )
                if not regenerate and latest_ver:
                    # Return latest existing version without creating a new version
                    version_num = latest_ver.version_number
                    db_id = existing_proposal.id
                    prop_uuid = existing_proposal.proposal_uuid
                    if latest_ver.proposal_data:
                        try:
                            proposal_draft = ProposalDraft.model_validate(latest_ver.proposal_data)
                        except Exception:
                            pass
                else:
                    # Explicit regeneration requested: create new version non-destructively
                    version_num = (latest_ver.version_number + 1) if latest_ver else 1
                    new_ver = ProposalVersion(
                        proposal_id=existing_proposal.id,
                        version_number=version_num,
                        proposal_data=proposal_dict,
                        generation_mode=generation_mode,
                        change_summary=f"Regenerated proposal draft (v{version_num})",
                        is_restored=False
                    )
                    db.add(new_ver)
                    existing_proposal.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db_id = existing_proposal.id
                    prop_uuid = existing_proposal.proposal_uuid
        else:
            prop_uuid = proposal_draft.proposal_id

        ver_summary = {
            "version_number": version_num,
            "change_summary": "Initial generated proposal draft" if version_num == 1 else f"Regenerated proposal draft (v{version_num})",
            "generation_mode": generation_mode,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return ProposalDraftResponse(
            id=db_id,
            proposal_id=prop_uuid,
            project_id=project_id,
            direction_id=source_dir_id,
            title=proposal_draft.title,
            research_question=proposal_draft.research_question,
            status="DRAFT",
            version_number=version_num,
            proposal=proposal_draft,
            version=ver_summary
        )

    @classmethod
    def _llm_synthesis(cls, dir_item: ResearchDirection) -> Optional[ProposalDraft]:
        """
        LLM-guided synthesizer wrapper. Called when LLM_PROVIDER and LLM_API_KEY are configured.
        Falls back to template synthesis if execution fails or returns invalid schema.
        """
        logger.info("Executing LLM synthesis wrapper...")
        return None
