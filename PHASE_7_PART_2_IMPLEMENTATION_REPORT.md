# Phase 7 — Part 2 Implementation Report: Research Opportunity Explorer & Feasibility Evaluation

## Executive Summary
In **Phase 7 — Part 2**, we successfully designed, built, and verified the **Research Opportunity Explorer & Feasibility Evaluation** system. Students can now evaluate candidate research opportunities through a 15-section detail view, compare up to 3 opportunities side-by-side, inspect conceptual implementation pipelines, review candidate datasets and risks, and draft evidence-grounded proposals.

---

## 1. Read-Only Audit & Data Reuse
- **Existing Backend Intelligence Reused**: `GlobalResearchIntelligenceService`, `ProjectIntelligenceService`, `ResearchGapService`, `ResearchDirectionService`, `ProposalDraftService`.
- **Zero Duplicate Algorithms**: Reused existing SBERT cosine similarity, Knowledge Graph link prediction, concept coverage, underrepresentation scores, and proposal synthesis pipelines.
- **Read-Only Guarantee**: `ResearchOpportunityEvaluationService` executes 0 database writes, 0 FAISS index alterations, and 0 graph mutations.

---

## 2. Core Components Implemented

### Backend Components
1. **`app/schemas/opportunity_evaluation_schema.py`**:
   - Pydantic schema for `OpportunityEvaluationResponse` with metrics, pipeline steps, experiment plans, dataset considerations, risks, scorecards, why consider lists, and student checklists.
2. **`app/services/research_opportunity_evaluation_service.py`**:
   - Read-only evaluation service to generate deterministic, collection-grounded evaluation responses for global or project-scoped directions.
3. **`app/api/opportunity_evaluation_api.py`**:
   - Endpoints `GET /api/research-directions/{direction_id}/evaluate` and `GET /api/projects/{project_id}/research-directions/{direction_id}/evaluate`.
4. **`app/main.py`**:
   - Registered `opportunity_evaluation_router`.

### Frontend Components
1. **`frontend/src/components/OpportunityExplorerModal.jsx`**:
   - **Header & Scope Tag**: Title, Confidence Badge, and Scope Tag (*"Collection-based evidence only"* / *"Based on N paper(s) in this project"*).
   - **Section A**: Research Problem (simple academic language).
   - **Section B**: What Current Research Does (visual cards of supporting papers & methods).
   - **Section C**: What Appears To Be Missing (strictly collection-scoped: *"Not observed in current indexed collection"*).
   - **Section D**: Why This Idea Is Relevant & Evidence Metrics (tooltips for Relationship Strength, Semantic Relevance, Collection Support, Underrepresentation, Gap Score).
   - **Section 🛠**: What Would I Actually Build? (Conceptual 5-step pipeline: Input → Feature Extraction → Modeling → Classification → Output).
   - **Section ⚙**: Candidate Technologies (Supported by Collection vs Candidate for Further Investigation).
   - **Section 📦**: Dataset Considerations (Collection usage, suitability, limitations).
   - **Section 🧪**: Possible Experiment Plan (Candidate evaluation plan steps comparing Accuracy, Precision, Recall, F1-score).
   - **Section 🎯**: Possible Contribution (Cautiously framed potential contribution).
   - **Section ⚠**: Research Risks & Considerations (Literature review warning).
   - **Section 📊**: Research Opportunity Scorecard (*"🟡 PROMISING — INVESTIGATE FURTHER"*).
   - **Section 🎓**: Why Consider This? (3–5 bullet reasons).
   - **Section 🔍**: Before You Start (Interactive student checklist).
   - **Primary Action**: `[✨ Draft Research Proposal]` button calling `POST /api/research-directions/draft` and opening `ProposalWorkspaceModal.jsx`.
2. **`frontend/src/components/OpportunityComparisonModal.jsx`**:
   - Comparative feasibility table comparing up to 3 selected research opportunities side-by-side across gap score, semantic relevance, collection support, candidate tech, and evidence-grounded verdict (*"Most strongly supported by current collection"*).
3. **`frontend/src/components/ResearchMap.jsx`**:
   - Added `[View Opportunity]` button to research opportunity cards.
   - Added `[ ] Compare` checkbox selection on cards and top action bar `[⚖ Compare Selected Opportunities (N)]`.
4. **`frontend/src/services/api.js`**:
   - Added `evaluateOpportunity(directionId)` and `evaluateProjectOpportunity(projectId, directionId)`.

---

## 3. Student Vocabulary & Framing Standards
- **No Raw Graph Jargon in Primary UI**: Converted technical terms to *"Relationship Strength"*, *"Shared Research Evidence"*, *"Concept Coverage"*, *"Semantic Relevance"*, and *"Collection Support"*.
- **Collection Scoping**: Always uses *"Promising within current collection"*, *"Evidence-supported opportunity"*, and *"Not observed in current indexed collection"*. Never claims global academic novelty.

---

## 4. Verification Results

1. **Backend Unit & Integration Tests (`pytest`)**:
   - **Command**: `.\venv\Scripts\python.exe -m pytest`
   - **Result**: `240 passed, 1 skipped in 31.42s` (100% pass rate across all 240 backend unit & API tests).

2. **Frontend Production Build (`npm run build`)**:
   - **Command**: `npm run build`
   - **Result**: `✓ built in 914ms` (Clean production bundle compiled without warnings or syntax errors).

3. **Immutability & Safety Audit**:
   - Confirmed 0 DB mutations, 0 FAISS index changes, and 0 graph alterations during evaluation requests.

---

## Final Status

==================================================
PASS — PHASE 7 PART 2 COMPLETE
==================================================
