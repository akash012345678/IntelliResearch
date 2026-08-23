from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class JourneyStageItem(BaseModel):
    stage_id: int  # 1 to 10
    stage_key: str  # 'PAPERS' | 'LANDSCAPE' | 'GAPS' | 'OPPORTUNITY' | 'VALIDATION' | 'PLAN' | 'EXPERIMENTS' | 'RESULTS' | 'PROPOSAL' | 'REPORT'
    title: str
    question: str
    status: str  # 'COMPLETED' | 'IN_PROGRESS' | 'AVAILABLE' | 'NOT_STARTED' | 'BLOCKED'
    summary_text: str
    target_tab: str
    action_label: str


class JourneyProgressInfo(BaseModel):
    total_stages: int = 10
    completed_stages: int
    current_stage_id: int
    current_stage_key: str
    progress_percentage: int  # 0 to 100
    is_complete: bool


class TopNextActionItem(BaseModel):
    title: str
    description: str
    why_explanation: str
    action_label: str
    target_tab: str


class MilestoneItem(BaseModel):
    key: str
    title: str
    completed: bool
    completed_at: Optional[str] = None


class RecentActivityItem(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    timestamp: str


class JourneyTraceNode(BaseModel):
    id: str
    label: str
    status: str
    count: int
    target_tab: str


class ResearchJourneyResponse(BaseModel):
    project_id: int
    project_name: str
    project_status: str
    paper_count: int
    progress: JourneyProgressInfo
    next_action: TopNextActionItem
    stages: List[JourneyStageItem] = []
    milestones: List[MilestoneItem] = []
    recent_activity: List[RecentActivityItem] = []
    trace_nodes: List[JourneyTraceNode] = []
