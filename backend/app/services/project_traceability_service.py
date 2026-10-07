import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection, ResearchExperiment
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.schemas.project_traceability_schema import (
    PaperTraceItem,
    ConceptTraceItem,
    GapTraceItem,
    OpportunityTraceItem,
    QuestionsObjectivesTraceItem,
    PlanTraceItem,
    ExperimentTraceItem,
    ResultsTraceItem,
    VersionTraceItem,
    ProposalTraceItem,
    ReportTraceItem,
    TraceabilityChainItem,
    TraceabilitySummary,
    ProjectTraceabilityResponse
)

logger = logging.getLogger(__name__)


class ProjectTraceabilityService:
    """
    Service responsible for building dynamic, end-to-end evidence & provenance traceability
    chains across the entire IntelliResearch research lifecycle for ANY research project.
    Enforces canonical relationship resolution:
    PROJECT -> PAPERS -> GAP -> OPPORTUNITY -> METHODOLOGY PLAN -> PLANNED EXPERIMENTS -> RUNS -> RESULTS -> PROPOSAL -> VERSIONS -> REPORT
    """

    @classmethod
    def get_project_traceability(cls, project_id: int, db: Session) -> ProjectTraceabilityResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research project with ID {project_id} not found."
            )

        # 1. Fetch Project Intelligence & Assigned Papers
        intel = ProjectIntelligenceService.analyze_project(project_id, db)
        
        paper_ids = [pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()]
        db_papers = []
        if paper_ids:
            db_papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(paper_ids)).all()
        paper_map = {p.id: p for p in db_papers}

        # 2. Fetch Saved Plans, Experiments, Proposals
        saved_plans = db.query(SavedResearchDirection).filter(SavedResearchDirection.project_id == project_id).order_by(SavedResearchDirection.created_at.desc()).all()
        experiments = db.query(ResearchExperiment).filter(ResearchExperiment.project_id == project_id).all()
        proposals = db.query(Proposal).filter(Proposal.project_id == project_id).all()

        # Build plan lookup matching direction_id
        def find_saved_plan_for_dir(target_dir_id: str) -> Optional[SavedResearchDirection]:
            for sp in saved_plans:
                if sp.source_direction_id == target_dir_id:
                    return sp
                if isinstance(sp.direction_data, dict):
                    d_dict = sp.direction_data
                    if d_dict.get("direction_id") == target_dir_id or d_dict.get("id") == target_dir_id:
                        return sp
                    plan_inner = d_dict.get("methodology_plan", {})
                    if isinstance(plan_inner, dict) and plan_inner.get("direction_id") == target_dir_id:
                        return sp
            return None

        # Group experiments by direction_id
        exps_by_dir: Dict[str, List[ResearchExperiment]] = {}
        for exp in experiments:
            d_id = exp.direction_id
            if d_id:
                exps_by_dir.setdefault(d_id, []).append(exp)

        # Group proposals by source_direction_id
        props_by_dir: Dict[str, Proposal] = {}
        for prop in proposals:
            d_id = prop.source_direction_id
            if d_id and d_id not in props_by_dir:
                props_by_dir[d_id] = prop

        candidate_dirs = intel.candidate_research_directions if hasattr(intel, "candidate_research_directions") else []
        gaps_list = intel.research_gaps if hasattr(intel, "research_gaps") else []

        # Collect all unique direction IDs across candidate opportunities, saved plans, experiments, and proposals
        dir_order: List[str] = []
        candidate_map: Dict[str, Any] = {}

        for idx, opp in enumerate(candidate_dirs, start=1):
            d_id = getattr(opp, "direction_id", None) or getattr(opp, "id", f"dir_{idx}")
            if d_id not in dir_order:
                dir_order.append(d_id)
            candidate_map[d_id] = opp

        for sp in saved_plans:
            d_id = sp.source_direction_id
            if not d_id and isinstance(sp.direction_data, dict):
                d_id = sp.direction_data.get("direction_id") or sp.direction_data.get("id")
            if d_id and d_id not in dir_order:
                dir_order.append(d_id)

        for exp in experiments:
            d_id = exp.direction_id
            if d_id and d_id not in dir_order:
                dir_order.append(d_id)

        for prop in proposals:
            d_id = prop.source_direction_id
            if d_id and d_id not in dir_order:
                dir_order.append(d_id)

        chains: List[TraceabilityChainItem] = []
        processed_prop_ids = set()

        # 3. Build chains for every direction in the project
        for idx, dir_id in enumerate(dir_order, start=1):
            opp = candidate_map.get(dir_id)
            saved_plan = find_saved_plan_for_dir(dir_id)
            linked_prop = props_by_dir.get(dir_id)

            if opp:
                title = getattr(opp, "title", f"Research Direction #{idx}")
                conf = str(getattr(opp, "confidence", "High")).capitalize()
                classif = getattr(opp, "gap_evidence_class", None) or "EVIDENCE_GROUNDED_OPPORTUNITY"
                score = float(getattr(opp, "gap_evidence_score", 0.85) or 0.85)
                rq = getattr(opp, "research_question", None)
                desc = getattr(opp, "description", None) or getattr(opp, "proposed_direction", None) or "Evidence-grounded direction."
            elif saved_plan:
                title = saved_plan.title
                conf = str(saved_plan.confidence or "High").capitalize()
                classif = "SAVED_METHODOLOGY_DIRECTION"
                score = 0.9
                p_data = saved_plan.direction_data or {}
                m_plan = p_data.get("methodology_plan", p_data) if isinstance(p_data, dict) else {}
                rq = m_plan.get("research_questions", [None])[0] if isinstance(m_plan, dict) and isinstance(m_plan.get("research_questions"), list) and len(m_plan.get("research_questions")) > 0 else None
                desc = saved_plan.description or "Saved research methodology direction."
            elif linked_prop:
                title = linked_prop.title
                conf = "High"
                classif = "PROPOSAL_DIRECTION"
                score = 0.9
                rq = None
                desc = "Direction associated with research proposal."
            else:
                title = f"Research Direction {dir_id}"
                conf = "High"
                classif = "PROJECT_DIRECTION"
                score = 0.85
                rq = None
                desc = "Project research direction."

            opp_item = OpportunityTraceItem(
                direction_id=dir_id,
                title=title,
                confidence=conf,
                classification=classif,
                direction_score=round(score, 4),
                research_question=rq,
                description=desc
            )

            # Match Parent Gap
            parent_gap_id = getattr(opp, "parent_gap_id", None) if opp else None
            matched_gap = None
            if parent_gap_id:
                for g in gaps_list:
                    g_id = getattr(g, "gap_id", None)
                    if g_id == parent_gap_id:
                        matched_gap = g
                        break
            if not matched_gap and gaps_list:
                matched_gap = gaps_list[(idx - 1) % len(gaps_list)]

            if matched_gap:
                gap_item = GapTraceItem(
                    gap_id=getattr(matched_gap, "gap_id", f"gap_{idx}"),
                    title=getattr(matched_gap, "title", "Unassessed Research Gap"),
                    description=getattr(matched_gap, "description", "Collection-scoped evidence gap."),
                    gap_score=float(getattr(matched_gap, "gap_score", 0.8) or 0.8),
                    confidence=str(getattr(matched_gap, "confidence", "Moderate")).capitalize(),
                    relationship_evidence=getattr(matched_gap, "relationship_type", "Collection-scoped evidence"),
                    limitation_statement=getattr(matched_gap, "explanation", None),
                    status="IDENTIFIED"
                )
            else:
                gap_item = GapTraceItem(
                    gap_id=f"gap_{idx}",
                    title="Collection-scoped Evidence Gap",
                    description="Evidence gap derived from indexed paper collection.",
                    gap_score=0.8,
                    confidence="Moderate",
                    relationship_evidence="Collection-scoped evidence",
                    status="IDENTIFIED"
                )

            # Supporting Papers for this opportunity
            supp_papers_raw = getattr(opp, "supporting_papers", [])
            paper_items: List[PaperTraceItem] = []
            for sp in supp_papers_raw:
                p_id = sp.get("paper_id") if isinstance(sp, dict) else getattr(sp, "paper_id", None)
                p_obj = paper_map.get(p_id) if p_id else None
                if p_obj:
                    paper_items.append(PaperTraceItem(
                        paper_id=p_obj.id,
                        title=p_obj.title,
                        authors=getattr(p_obj, "authors", None),
                        year=getattr(p_obj, "year", None),
                        evidence_role="[RECORDED_EVIDENCE]",
                        supported_concept=sp.get("title", p_obj.title) if isinstance(sp, dict) else p_obj.title
                    ))
                elif p_id:
                    paper_items.append(PaperTraceItem(
                        paper_id=p_id,
                        title=sp.get("title", f"Paper #{p_id}") if isinstance(sp, dict) else f"Paper #{p_id}",
                        evidence_role="[RECORDED_EVIDENCE]"
                    ))

            if not paper_items and db_papers:
                for p in db_papers[:2]:
                    paper_items.append(PaperTraceItem(
                        paper_id=p.id,
                        title=p.title,
                        authors=getattr(p, "authors", None),
                        year=getattr(p, "year", None),
                        evidence_role="[RECORDED_EVIDENCE]",
                        supported_concept="Assigned Project Paper"
                    ))

            # Supporting Concepts
            supp_concepts_raw = getattr(opp, "supporting_concepts", []) or []
            candidate_algos = getattr(opp, "candidate_algorithms", []) or []
            candidate_datasets = getattr(opp, "candidate_datasets", []) or []

            concept_items: List[ConceptTraceItem] = []
            for c_name in supp_concepts_raw:
                if isinstance(c_name, str):
                    concept_items.append(ConceptTraceItem(name=c_name, type="concept", evidence_tag="[RECORDED_EVIDENCE]"))
            for algo in candidate_algos:
                a_name = algo.get("name") if isinstance(algo, dict) else getattr(algo, "name", str(algo))
                if a_name and not any(ci.name == a_name for ci in concept_items):
                    concept_items.append(ConceptTraceItem(name=a_name, type="algorithm", evidence_tag="[RECORDED_EVIDENCE]"))
            for ds in candidate_datasets:
                d_name = ds.get("name") if isinstance(ds, dict) else getattr(ds, "name", str(ds))
                if d_name and not any(ci.name == d_name for ci in concept_items):
                    concept_items.append(ConceptTraceItem(name=d_name, type="dataset", evidence_tag="[RECORDED_EVIDENCE]"))

            # Plan Resolution (strictly check SavedResearchDirection table)
            saved_plan = find_saved_plan_for_dir(dir_id)
            linked_exps = exps_by_dir.get(dir_id, [])

            if saved_plan:
                p_data = saved_plan.direction_data or {}
                m_plan = p_data.get("methodology_plan", p_data) if isinstance(p_data, dict) else {}
                baselines = m_plan.get("baseline_methods", []) if isinstance(m_plan, dict) else []
                proposed_arch = m_plan.get("proposed_architecture") or m_plan.get("architecture") if isinstance(m_plan, dict) else "Proposed System"
                plan_datasets = m_plan.get("candidate_datasets", []) if isinstance(m_plan, dict) else []
                ds_names = [d.get("name", str(d)) if isinstance(d, dict) else str(d) for d in plan_datasets]
                
                plan_item = PlanTraceItem(
                    plan_id=saved_plan.id,
                    status="SAVED",
                    methodology_title=saved_plan.title,
                    baseline_methods=[b.get("name", str(b)) if isinstance(b, dict) else str(b) for b in baselines],
                    proposed_architecture=proposed_arch,
                    datasets=ds_names,
                    experiment_count=len(linked_exps) or (len(m_plan.get("experiments", [])) if isinstance(m_plan, dict) else 0)
                )

                # RQs and Objectives from saved plan
                rq_list = m_plan.get("research_questions", [rq] if rq else []) if isinstance(m_plan, dict) else [rq]
                obj_list = m_plan.get("objectives", []) if isinstance(m_plan, dict) else []
                hyp_list = m_plan.get("hypotheses", []) if isinstance(m_plan, dict) else []
                qo_item = QuestionsObjectivesTraceItem(
                    research_questions=[str(r) for r in rq_list if r],
                    objectives=[str(o) for o in obj_list if o],
                    hypotheses=[str(h) for h in hyp_list if h],
                    evidence_tag="[PROPOSED]"
                )
            else:
                plan_item = PlanTraceItem(
                    status="NOT_CREATED",
                    methodology_title="Plan Not Generated Yet",
                    experiment_count=len(linked_exps)
                )
                qo_item = QuestionsObjectivesTraceItem(
                    research_questions=[rq] if rq else ["What is the empirical trade-off of the proposed methodology?"],
                    objectives=["Evaluate proposed methodology against baseline suite."],
                    hypotheses=["Proposed architecture achieves statistically significant performance improvement."],
                    evidence_tag="[PROPOSED]"
                )

            # Linked Experiments Resolution (strictly scoped to dir_id)
            exp_items: List[ExperimentTraceItem] = []
            total_chain_result_runs = 0
            total_chain_metric_rows = 0
            completed_exps_count = 0
            exps_with_results_count = 0

            for exp in linked_exps:
                exp_runs = exp.runs or []
                exp_runs_with_results = [r for r in exp_runs if len(r.results or []) > 0]
                exp_metric_rows = sum(len(r.results or []) for r in exp_runs)
                
                total_chain_result_runs += len(exp_runs_with_results)
                total_chain_metric_rows += exp_metric_rows

                if exp.status == "COMPLETED":
                    completed_exps_count += 1

                if len(exp_runs_with_results) > 0:
                    exps_with_results_count += 1
                    indiv_result_status = "RESULTS_RECORDED"
                elif exp.status == "COMPLETED":
                    indiv_result_status = "COMPLETED_NO_RESULTS"
                else:
                    indiv_result_status = "MISSING"

                exp_items.append(ExperimentTraceItem(
                    experiment_id=exp.id,
                    title=exp.name,
                    type=exp.experiment_type,
                    execution_status=exp.status,
                    baseline=exp.baseline_config.get("algorithm", "Baseline") if isinstance(exp.baseline_config, dict) else "Baseline",
                    proposed_method=exp.proposed_config.get("architecture", "Proposed") if isinstance(exp.proposed_config, dict) else "Proposed",
                    configured_metrics=exp.execution_config.get("metrics", ["Accuracy", "F1-Score"]) if isinstance(exp.execution_config, dict) else ["Accuracy", "F1-Score"],
                    result_runs_count=len(exp_runs_with_results),
                    result_rows_count=exp_metric_rows,
                    result_status=indiv_result_status
                ))

            # Chain Results Aggregation & Status Rules
            total_chain_exps = len(linked_exps)

            if total_chain_exps == 0 or exps_with_results_count == 0:
                chain_completion_status = "RESULTS_NOT_RECORDED"
                notice_text = "Experimental measurements have not yet been recorded. The experiments remain pending execution. [MISSING]"
            elif exps_with_results_count < total_chain_exps:
                chain_completion_status = "PARTIAL_RESULTS"
                notice_text = f"{total_chain_result_runs} run(s) recorded ({exps_with_results_count} of {total_chain_exps} experiments have recorded results). [PARTIAL_RESULTS]"
            else:
                chain_completion_status = "ALL_RESULTS_RECORDED"
                notice_text = f"{total_chain_result_runs} run(s) recorded across all {total_chain_exps} experiments. [ALL_RESULTS_RECORDED]"

            results_item = ResultsTraceItem(
                results_recorded=(exps_with_results_count > 0),
                run_count=total_chain_result_runs,
                result_row_count=total_chain_metric_rows,
                experiments_count=total_chain_exps,
                completed_experiments_count=completed_exps_count,
                experiments_with_results_count=exps_with_results_count,
                completion_status=chain_completion_status,
                notice=notice_text
            )

            # Proposal & Versions (strictly scoped to dir_id)
            linked_prop = props_by_dir.get(dir_id)
            version_items: List[VersionTraceItem] = []

            if linked_prop:
                processed_prop_ids.add(linked_prop.id)
                latest_ver_num = linked_prop.versions[-1].version_number if linked_prop.versions else 1
                
                prop_item = ProposalTraceItem(
                    proposal_id=linked_prop.id,
                    proposal_uuid=linked_prop.proposal_uuid,
                    title=linked_prop.title,
                    status=linked_prop.status,
                    current_version_number=latest_ver_num,
                    is_created=True
                )

                for v in linked_prop.versions:
                    version_items.append(VersionTraceItem(
                        version_id=v.id,
                        version_number=v.version_number,
                        created_at=v.created_at.isoformat() if v.created_at else None,
                        source_type=v.generation_mode.upper() if v.generation_mode else "TEMPLATE",
                        is_current=(v.version_number == latest_ver_num)
                    ))
            else:
                prop_item = ProposalTraceItem(
                    title="Proposal Not Created Yet",
                    status="NOT_CREATED",
                    is_created=False
                )

            # Report Item
            report_item = ReportTraceItem(
                status="READY_FOR_EXPORT" if (linked_prop or db_papers) else "NOT_GENERATED",
                report_title=f"{project.name} Research Report"
            )

            chains.append(TraceabilityChainItem(
                chain_id=f"chain_{dir_id}",
                opportunity=opp_item,
                gap=gap_item,
                papers=paper_items,
                concepts=concept_items,
                questions_objectives=qo_item,
                plan=plan_item,
                experiments=exp_items,
                results=results_item,
                proposal=prop_item,
                versions=version_items,
                report=report_item
            ))

        # 4. Process any manual proposals not attached to candidate directions
        for prop in proposals:
            if prop.id in processed_prop_ids:
                continue

            latest_ver_num = prop.versions[-1].version_number if prop.versions else 1
            prop_item = ProposalTraceItem(
                proposal_id=prop.id,
                proposal_uuid=prop.proposal_uuid,
                title=prop.title,
                status=prop.status,
                current_version_number=latest_ver_num,
                is_created=True
            )

            version_items = [
                VersionTraceItem(
                    version_id=v.id,
                    version_number=v.version_number,
                    created_at=v.created_at.isoformat() if v.created_at else None,
                    source_type=v.generation_mode.upper() if v.generation_mode else "MANUAL",
                    is_current=(v.version_number == latest_ver_num)
                )
                for v in prop.versions
            ]

            chains.append(TraceabilityChainItem(
                chain_id=f"chain_prop_{prop.id}",
                opportunity=OpportunityTraceItem(
                    direction_id=prop.source_direction_id or f"dir_prop_{prop.id}",
                    title=prop.title,
                    confidence="High",
                    classification="MANUAL_RESEARCH_PROPOSAL",
                    direction_score=0.9
                ),
                gap=GapTraceItem(
                    gap_id=f"gap_prop_{prop.id}",
                    title="User-Identified Research Problem",
                    description="Research direction created directly by research investigator.",
                    gap_score=0.9,
                    confidence="High"
                ),
                papers=[PaperTraceItem(paper_id=p.id, title=p.title, authors=getattr(p, "authors", None), year=getattr(p, "year", None)) for p in db_papers[:3]],
                concepts=[ConceptTraceItem(name="User Proposed Method", type="algorithm")],
                questions_objectives=QuestionsObjectivesTraceItem(
                    research_questions=["How does the user-proposed methodology perform on benchmark metrics?"],
                    objectives=["Develop and evaluate proposed architecture."],
                    hypotheses=["Proposed approach achieves improved performance."]
                ),
                plan=PlanTraceItem(status="NOT_CREATED", methodology_title="Plan Not Generated Yet"),
                experiments=[],
                results=ResultsTraceItem(results_recorded=False, completion_status="RESULTS_NOT_RECORDED"),
                proposal=prop_item,
                versions=version_items,
                report=ReportTraceItem(status="READY_FOR_EXPORT", report_title=f"{project.name} Research Report")
            ))

        # 5. Overall Summary Counters across Project
        proj_completed_exps = sum(1 for exp in experiments if exp.status == "COMPLETED")
        proj_result_runs = sum(len([r for r in (exp.runs or []) if len(r.results or []) > 0]) for exp in experiments)
        proj_result_rows = sum(sum(len(r.results or []) for r in (exp.runs or [])) for exp in experiments)

        if len(experiments) > 0 and proj_result_runs == len(experiments):
            global_results_status = "ALL_RESULTS_RECORDED"
        elif proj_result_runs > 0:
            global_results_status = "PARTIAL_RESULTS"
        else:
            global_results_status = "RESULTS_NOT_RECORDED"

        summary = TraceabilitySummary(
            total_papers=len(db_papers),
            total_gaps=len(gaps_list),
            total_opportunities=len(candidate_dirs),
            saved_plans=len(saved_plans),
            planned_experiments=len(experiments),
            completed_experiments=proj_completed_exps,
            recorded_result_runs=proj_result_runs,
            recorded_result_rows=proj_result_rows,
            created_proposals=len(proposals),
            final_report_status="READY_FOR_EXPORT" if (proposals or db_papers) else "NOT_GENERATED",
            stage_statuses={
                "papers": "AVAILABLE" if db_papers else "NOT_AVAILABLE",
                "gaps": "AVAILABLE" if gaps_list else "NOT_AVAILABLE",
                "opportunities": "AVAILABLE" if candidate_dirs else "NOT_AVAILABLE",
                "plans": "SAVED" if saved_plans else "NOT_CREATED",
                "experiments": "PLANNED" if experiments else "NOT_EXECUTED",
                "results": global_results_status,
                "proposals": "DRAFT" if proposals else "NOT_CREATED",
                "report": "READY_FOR_EXPORT" if (proposals or db_papers) else "NOT_GENERATED"
            }
        )

        return ProjectTraceabilityResponse(
            project_id=project.id,
            project_name=project.name,
            summary=summary,
            chains=chains
        )
