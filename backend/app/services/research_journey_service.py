import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection, ResearchExperiment, ExperimentRun, ExperimentResult
from app.models.proposal_model import Proposal
from app.schemas.research_journey_schema import (
    JourneyStageItem,
    JourneyProgressInfo,
    TopNextActionItem,
    MilestoneItem,
    RecentActivityItem,
    JourneyTraceNode,
    ResearchJourneyResponse
)

logger = logging.getLogger(__name__)


class ResearchJourneyService:
    """
    Read-only service for aggregating project journey state across all 10 stages,
    computing student progress percentage, top next-action recommendations, milestones, and audit history.
    """

    @classmethod
    def get_research_journey(cls, db: Session, project_id: int) -> ResearchJourneyResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        papers = [assoc.paper for assoc in project.project_papers if assoc.paper]
        paper_count = len(papers)
        saved_dirs = project.saved_directions or []
        exps = project.experiments or []
        props = project.proposals or []

        has_saved_plan = False
        saved_plan_title = None
        for d in saved_dirs:
            if d.direction_data and isinstance(d.direction_data, dict) and "methodology_plan" in d.direction_data:
                has_saved_plan = True
                saved_plan_title = d.title
                break

        completed_exps = [e for e in exps if e.status == "COMPLETED"]
        recorded_results_count = sum(1 for e in exps if any(len(r.results) > 0 for r in e.runs))

        # ----------------------------------------------------
        # STAGE EVALUATIONS (1 to 10)
        # ----------------------------------------------------
        # Stage 1: Papers
        st1_done = paper_count >= 1
        st1_status = "COMPLETED" if st1_done else "IN_PROGRESS"
        st1_summary = f"{paper_count} research papers assigned to project." if st1_done else "No research papers added yet."

        # Stage 2: Landscape
        st2_done = paper_count >= 1
        st2_status = "COMPLETED" if st2_done else "NOT_STARTED"
        st2_summary = f"Landscape calculated over {paper_count} papers." if st2_done else "Add papers to calculate landscape."

        # Stage 3: Gaps
        st3_done = paper_count >= 1
        st3_status = "COMPLETED" if st3_done else "NOT_STARTED"
        st3_summary = "Research gap analysis available." if st3_done else "Add papers to detect gaps."

        # Stage 4: Opportunity
        st4_done = len(saved_dirs) >= 1
        st4_status = "COMPLETED" if st4_done else ("AVAILABLE" if st1_done else "NOT_STARTED")
        st4_summary = f"{len(saved_dirs)} saved research direction(s)." if st4_done else "Explore candidate research opportunities."

        # Stage 5: Validation
        st5_done = any(
            d.direction_data and isinstance(d.direction_data, dict) and "validation" in d.direction_data
            for d in saved_dirs
        )
        st5_status = "COMPLETED" if st5_done else ("AVAILABLE" if st4_done else "NOT_STARTED")
        st5_summary = "Literature validation evaluated." if st5_done else "Validate saved idea against broader literature."

        # Stage 6: Research Plan
        st6_done = has_saved_plan
        st6_status = "COMPLETED" if st6_done else ("AVAILABLE" if st4_done else "NOT_STARTED")
        st6_summary = f"Saved plan: '{saved_plan_title}'" if st6_done else "Build methodology execution plan."

        # Stage 7: Experiments
        st7_done = len(completed_exps) >= 1
        st7_status = "COMPLETED" if st7_done else ("IN_PROGRESS" if len(exps) > 0 else ("AVAILABLE" if st6_done else "NOT_STARTED"))
        st7_summary = f"{len(completed_exps)} of {len(exps)} experiments completed." if len(exps) > 0 else "Create or import planned experiments."

        # Stage 8: Results
        st8_done = recorded_results_count >= 1
        st8_status = "COMPLETED" if st8_done else ("AVAILABLE" if len(exps) > 0 else "NOT_STARTED")
        st8_summary = f"Results recorded for {recorded_results_count} experiment(s)." if st8_done else "Results not yet recorded."

        # Stage 9: Proposals
        st9_done = len(props) >= 1
        st9_status = "COMPLETED" if st9_done else ("AVAILABLE" if st6_done else "NOT_STARTED")
        st9_summary = f"{len(props)} proposal(s) created." if st9_done else "Draft structured research proposal."

        # Stage 10: Research Report
        st10_done = paper_count >= 1
        st10_status = "COMPLETED" if st10_done else "NOT_STARTED"
        st10_summary = "Full research report export available." if st10_done else "Add papers to enable report."

        # Stage Objects
        stages: List[JourneyStageItem] = [
            JourneyStageItem(
                stage_id=1, stage_key="PAPERS", title="1. Research Papers",
                question="What research do I already have?", status=st1_status,
                summary_text=st1_summary, target_tab="papers", action_label="View / Add Papers"
            ),
            JourneyStageItem(
                stage_id=2, stage_key="LANDSCAPE", title="2. Research Landscape",
                question="What are these papers doing?", status=st2_status,
                summary_text=st2_summary, target_tab="map", action_label="Explore Research Map"
            ),
            JourneyStageItem(
                stage_id=3, stage_key="GAPS", title="3. Research Gaps",
                question="What appears to be missing?", status=st3_status,
                summary_text=st3_summary, target_tab="gaps", action_label="Explore Research Gaps"
            ),
            JourneyStageItem(
                stage_id=4, stage_key="OPPORTUNITY", title="4. Research Opportunity",
                question="What could I investigate?", status=st4_status,
                summary_text=st4_summary, target_tab="directions", action_label="Explore Opportunities"
            ),
            JourneyStageItem(
                stage_id=5, stage_key="VALIDATION", title="5. Idea Validation",
                question="Is this idea worth investigating further?", status=st5_status,
                summary_text=st5_summary, target_tab="directions", action_label="Validate Research Idea"
            ),
            JourneyStageItem(
                stage_id=6, stage_key="PLAN", title="6. Research Plan",
                question="How should I conduct this research?", status=st6_status,
                summary_text=st6_summary, target_tab="plan", action_label="Build Research Plan"
            ),
            JourneyStageItem(
                stage_id=7, stage_key="EXPERIMENTS", title="7. Experiments",
                question="Have I actually tested the idea?", status=st7_status,
                summary_text=st7_summary, target_tab="experiments", action_label="Open Experiments"
            ),
            JourneyStageItem(
                stage_id=8, stage_key="RESULTS", title="8. Results Analysis",
                question="What did my experiments actually show?", status=st8_status,
                summary_text=st8_summary, target_tab="results-analysis", action_label="Analyze Results"
            ),
            JourneyStageItem(
                stage_id=9, stage_key="PROPOSAL", title="9. Research Proposal",
                question="Can I turn this into a structured proposal?", status=st9_status,
                summary_text=st9_summary, target_tab="proposals", action_label="Open / Draft Proposal"
            ),
            JourneyStageItem(
                stage_id=10, stage_key="REPORT", title="10. Research Report",
                question="Can I document the complete research journey?", status=st10_status,
                summary_text=st10_summary, target_tab="report", action_label="Generate Research Report"
            ),
        ]

        # Calculate progress
        completed_stage_ids = [s.stage_id for s in stages if s.status == "COMPLETED"]
        completed_count = len(completed_stage_ids)
        progress_pct = int((completed_count / 10.0) * 100)
        is_complete = completed_count == 10

        # Determine current stage ID
        current_st = next((s for s in stages if s.status != "COMPLETED"), stages[-1])

        # Top Next Action Recommendation
        if not st1_done:
          next_act = TopNextActionItem(
              title="Add Research Papers to Project",
              description="Your project has no papers assigned yet.",
              why_explanation="Research gap discovery, paper-to-paper connections, and methodology planning require assigned research papers.",
              action_label="➕ Add Research Papers",
              target_tab="papers"
          )
        elif not st4_done:
          next_act = TopNextActionItem(
              title="Save a Research Direction",
              description="Explore your project research map and save a candidate research direction.",
              why_explanation="Saving a candidate research opportunity enables literature validation and methodology planning.",
              action_label="💡 Explore Opportunities",
              target_tab="directions"
          )
        elif not st6_done:
          next_act = TopNextActionItem(
              title="Build Research Methodology Plan",
              description="Convert your saved research direction into a structured methodology plan.",
              why_explanation="A research plan defines your objectives, hypotheses, baseline algorithms, datasets, and experiment matrix.",
              action_label="🧪 Build Research Plan",
              target_tab="plan"
          )
        elif not st7_done:
          next_act = TopNextActionItem(
              title="Start Experiments & Record Results",
              description="Import planned experiments into your Experiment Workspace and record empirical measurements.",
              why_explanation="Recording real baseline and proposed metrics enables evidence-based results analysis without data fabrication.",
              action_label="🧪 Open Experiments",
              target_tab="experiments"
          )
        elif not st8_done:
          next_act = TopNextActionItem(
              title="Analyze Empirical Results",
              description="Analyze recorded baseline vs proposed metrics and evaluate trade-offs.",
              why_explanation="Results analysis synthesizes plain-language conclusions before drafting your research proposal.",
              action_label="📊 Analyze Results",
              target_tab="results-analysis"
          )
        elif not st9_done:
          next_act = TopNextActionItem(
              title="Draft Research Proposal",
              description="Draft a structured proposal incorporating your validated methodology and experimental evidence.",
              why_explanation="A proposal synthesizes your problem statement, literature gap, proposed method, and experimental proof.",
              action_label="📝 Draft Proposal",
              target_tab="proposals"
          )
        else:
          next_act = TopNextActionItem(
              title="Generate Research Report",
              description="Export your complete end-to-end research project report.",
              why_explanation="Your IntelliResearch workflow is fully complete. Export a comprehensive project research report for submission.",
              action_label="📑 Generate Report",
              target_tab="report"
          )

        # Milestones
        milestones: List[MilestoneItem] = [
            MilestoneItem(key="first_paper", title="First Paper Added", completed=st1_done),
            MilestoneItem(key="first_gap", title="First Gap Identified", completed=st3_done),
            MilestoneItem(key="first_opportunity", title="First Opportunity Saved", completed=st4_done),
            MilestoneItem(key="first_validation", title="First Idea Validated", completed=st5_done),
            MilestoneItem(key="first_plan", title="First Research Plan Saved", completed=st6_done),
            MilestoneItem(key="first_experiment", title="First Experiment Completed", completed=st7_done),
            MilestoneItem(key="first_result", title="First Empirical Result Recorded", completed=st8_done),
            MilestoneItem(key="first_proposal", title="First Proposal Created", completed=st9_done),
            MilestoneItem(key="final_report", title="Final Research Report Available", completed=st10_done),
        ]

        # Recent Activity Feed
        recent_activity: List[RecentActivityItem] = []
        for assoc in project.project_papers:
            if assoc.paper:
                recent_activity.append(RecentActivityItem(
                    id=f"paper_{assoc.paper_id}",
                    event_type="PAPER_ADDED",
                    title="Research Paper Added",
                    description=f"Assigned paper '{assoc.paper.title[:45]}...'",
                    timestamp=assoc.added_at.isoformat() if assoc.added_at else project.created_at.isoformat()
                ))

        for d in saved_dirs:
            recent_activity.append(RecentActivityItem(
                id=f"direction_{d.id}",
                event_type="DIRECTION_SAVED",
                title="Research Opportunity Saved",
                description=f"Saved candidate direction '{d.title[:45]}...'",
                timestamp=d.created_at.isoformat() if d.created_at else project.created_at.isoformat()
            ))

        for e in exps:
            recent_activity.append(RecentActivityItem(
                id=f"exp_{e.id}",
                event_type="EXPERIMENT_CREATED",
                title="Experiment Created",
                description=f"Configured experiment '{e.name[:45]}...'",
                timestamp=e.created_at.isoformat() if e.created_at else project.created_at.isoformat()
            ))

        for p in props:
            recent_activity.append(RecentActivityItem(
                id=f"prop_{p.id}",
                event_type="PROPOSAL_CREATED",
                title="Proposal Created",
                description=f"Drafted proposal '{p.title[:45]}...'",
                timestamp=p.created_at.isoformat() if p.created_at else project.created_at.isoformat()
            ))

        # Sort activity by timestamp desc, limit to 8 items
        recent_activity.sort(key=lambda x: x.timestamp, reverse=True)
        recent_activity = recent_activity[:8]

        # End-to-End Trace Nodes
        trace_nodes: List[JourneyTraceNode] = [
            JourneyTraceNode(id="n_papers", label="Papers", status="COMPLETED" if st1_done else "NOT_STARTED", count=paper_count, target_tab="papers"),
            JourneyTraceNode(id="n_landscape", label="Landscape", status="COMPLETED" if st2_done else "NOT_STARTED", count=paper_count, target_tab="map"),
            JourneyTraceNode(id="n_gaps", label="Gaps", status="COMPLETED" if st3_done else "NOT_STARTED", count=1 if st3_done else 0, target_tab="gaps"),
            JourneyTraceNode(id="n_opp", label="Opportunities", status="COMPLETED" if st4_done else "NOT_STARTED", count=len(saved_dirs), target_tab="directions"),
            JourneyTraceNode(id="n_val", label="Validation", status="COMPLETED" if st5_done else "NOT_STARTED", count=1 if st5_done else 0, target_tab="directions"),
            JourneyTraceNode(id="n_plan", label="Plan", status="COMPLETED" if st6_done else "NOT_STARTED", count=1 if st6_done else 0, target_tab="plan"),
            JourneyTraceNode(id="n_exp", label="Experiments", status="COMPLETED" if st7_done else "NOT_STARTED", count=len(exps), target_tab="experiments"),
            JourneyTraceNode(id="n_res", label="Results", status="COMPLETED" if st8_done else "NOT_STARTED", count=recorded_results_count, target_tab="results-analysis"),
            JourneyTraceNode(id="n_prop", label="Proposal", status="COMPLETED" if st9_done else "NOT_STARTED", count=len(props), target_tab="proposals"),
            JourneyTraceNode(id="n_rep", label="Report", status="COMPLETED" if st10_done else "NOT_STARTED", count=1 if st10_done else 0, target_tab="report"),
        ]

        return ResearchJourneyResponse(
            project_id=project.id,
            project_name=project.name,
            project_status=project.status,
            paper_count=paper_count,
            progress=JourneyProgressInfo(
                total_stages=10,
                completed_stages=completed_count,
                current_stage_id=current_st.stage_id,
                current_stage_key=current_st.stage_key,
                progress_percentage=progress_pct,
                is_complete=is_complete
            ),
            next_action=next_act,
            stages=stages,
            milestones=milestones,
            recent_activity=recent_activity,
            trace_nodes=trace_nodes
        )
