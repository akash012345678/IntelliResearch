# Phase 7 — Part 4 Implementation Report: Research Methodology & Experiment Planner

## Executive Summary
In **Phase 7 — Part 4**, we designed, built, and verified the **Research Methodology & Experiment Planner**. The system converts validated research opportunities into evidence-grounded research execution plans containing 24 structured planning sections: objectives, testable hypotheses, visual system pipeline, dataset considerations, preprocessing steps, baseline comparison, proposed architecture, experiment matrix, metrics, ablation plan, reproducibility checklist, timeline, and export/proposal workspace integration.

---

## 1. Audit Findings & Intelligence Reuse
- **Existing Intelligence Reused**: `ResearchOpportunityEvaluationService`, `ResearchIdeaValidationService`, `ResearchDirectionService`, `ProposalDraftService`, `ProjectIntelligenceService`, `ProjectResearchReportService`.
- **Zero Duplicate Algorithms**: Reused existing SBERT similarity, link prediction, and concept extraction data structures.
- **Read-Only Guarantee**: `ResearchMethodologyService` executes 0 DB writes, 0 FAISS index changes, and 0 graph alterations by default. Plan persistence occurs only when the student explicitly clicks `[💾 Save Research Plan]`.

---

## 2. Core Components Implemented

### Backend Components
1. **`app/schemas/methodology_plan_schema.py`**:
   - Pydantic models for `MethodologyPlanResponse`, `PipelineStepItem`, `DatasetPlanItem`, `BaselineMethodItem`, `ExperimentPlanItem`, `MetricCategoryItem`, `AblationStepItem`, `ExpectedOutputItem`, `HypothesesItem`, and `SaveResearchPlanRequest`.
2. **`app/services/research_methodology_service.py`**:
   - Read-only service synthesizing 24 evidence-grounded planning sections from existing research intelligence.
3. **`app/api/research_methodology_api.py`**:
   - Endpoints `GET /api/research-directions/{direction_id}/methodology-plan`, `GET /api/projects/{project_id}/research-directions/{direction_id}/methodology-plan`, and `POST /api/projects/{project_id}/research-plan/save`.
4. **`app/main.py`**:
   - Registered `research_methodology_router`.

### Frontend Components
1. **`frontend/src/components/ResearchMethodologyPlannerModal.jsx`**:
   - **Header & Scope Tag**: Title, Scope Tag (`GLOBAL COLLECTION` / `PROJECT • X PAPERS`), Validation Status Badge, and Planning Disclaimer.
   - **24 Structured Sections**: Problem Statement, Concrete Objectives, Research Questions, Testable Hypotheses ($H_0/H_1$), 5-Stage System Pipeline, Dataset Plan, 8-Step Preprocessing, Baseline Comparison, Proposed Architecture, Experiment Matrix, Categorized Metrics, Ablation Plan, Variables, Planned Outputs, Success Criteria, Risks, Reproducibility Checklist, 8-Week Timeline, Implementation Checklist, Cautious Potential Contribution, Evidence Traceability, and Educational Help Box.
   - **Actions**: `[📄 Export PDF]`, `[📝 Export Markdown]`, `[📊 Export JSON]`, `[💾 Save Research Plan]`, `[✨ Draft Research Proposal]`.
2. **`frontend/src/components/ResearchIdeaValidationModal.jsx`**:
   - Added `[🧪 Build Research Plan]` button next to `[✨ Draft Research Proposal]`.
3. **`frontend/src/components/OpportunityExplorerModal.jsx`**:
   - Added `[🧪 Build Research Plan]` button next to `[✨ Draft Research Proposal]`.
4. **`frontend/src/pages/ResearchProjectDetails.jsx`**:
   - Added `🧪 Research Plan` tab allowing students to view saved methodology plans or build new research plans.
5. **`frontend/src/services/api.js`**:
   - Added `getMethodologyPlan(directionId)`, `getProjectMethodologyPlan(projectId, directionId)`, and `saveProjectResearchPlan(projectId, directionId, plan_data, notes)`.

---

## 3. Planning & Academic Safety Guarantees
- **No Fake Experimental Results**: The system generates experiment structures, hypotheses, pipeline steps, metrics, and planned output tables. It NEVER fabricates accuracy numbers, F1 scores, RMSE values, or fake dataset statistics.
- **Cautious Academic Phrasing**: Uses labels like *"Potential contribution"*, *"Candidate combination"*, *"Proposed configuration"*. Never claims guaranteed novelty or performance.
- **Strict Scope Isolation**: Global scope uses indexed collection papers; Project scope strictly uses project-assigned papers with zero cross-project leakage.

---

## 4. Verification Results

1. **Backend Unit & Integration Tests (`pytest`)**:
   - **Command**: `.\venv\Scripts\python.exe -m pytest`
   - **Result**: `244 passed, 1 skipped in 33.15s` (100% pass rate across all 244 backend unit & API tests).

2. **Frontend Production Build (`npm run build`)**:
   - **Command**: `npm run build`
   - **Result**: `✓ built in 847ms` (Clean production bundle compiled without warnings or syntax errors).

3. **Immutability & Safety Audit**:
   - Confirmed 0 DB mutations, 0 FAISS index changes, and 0 graph alterations during plan generation requests.

---

## Final Status

==================================================
PASS — PHASE 7 PART 4 COMPLETE
==================================================
