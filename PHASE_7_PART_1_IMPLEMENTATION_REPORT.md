# Phase 7 — Part 1 Implementation Report: Student-Friendly Research Map & New Idea Discovery

## Executive Summary
In **Phase 7 — Part 1**, we successfully transformed the technical Knowledge Graph experience into a **Student-Friendly Research Discovery Map** (`ResearchMap.jsx`). The new interface renders card-based research publication maps, human-readable paper-to-paper connections, categorized shared concepts (Common vs Underrepresented), 5-step research gap explanations, and evidence-grounded research opportunities with direct `[✨ Draft Research Proposal]` integration.

---

## Technical Audit & Enhancements

### 1. New Component Architecture
- **Component File**: `frontend/src/components/ResearchMap.jsx`
- **Scope Support**: Dual-mode rendering for **Global Scope** (`/research-analysis`) and **Project Scope** (`/research-projects/:projectId`).
- **Core Visual Flow**:
  $$\text{YOUR PAPERS} \longrightarrow \text{COMMON CONCEPTS} \longrightarrow \text{UNDERREPRESENTED} \longrightarrow \text{POTENTIAL GAPS} \longrightarrow \text{💡 RESEARCH OPPORTUNITY} \longrightarrow \text{📝 DRAFT PROPOSAL}$$

### 2. Student-Friendly Visualization Layer
1. **Interactive Legend & Help Panel**: "How to Read This Map" collapsible panel explaining Paper, Connection, Common Concept, Underrepresented Concept, Potential Gap, and Opportunity.
2. **Research Opportunities Layer**:
   - Card layout with Confidence Filter (All, High, Moderate) and Sorting.
   - Includes Title, Current Collection Context, Potential Contribution, Supporting Papers (clickable to `PaperViewModal`), Candidate Algorithms & Datasets, Gap Score %, Semantic Relevance %, and Confidence level.
   - Direct `[✨ Draft Research Proposal]` button triggering proposal synthesis via `apiService.generateProposalDraft(directionId)`.
3. **"What Is Missing?" (Potential Research Gaps)**:
   - Gap cards with source paper title, missing concept & type, gap score %, confidence badge.
   - Expandable 5-step human-readable evidence explanation ("Why was this identified?").
4. **Paper Landscape & Connections**:
   - Rectangular paper cards showing ID, title, 2–4 key concepts (algorithms, datasets, methodologies, domain).
   - Pairwise connection cards (`Paper A ── 82% Similar ──> Paper B`) with modal explaining shared concepts.
5. **Shared Concept View**:
   - Grouped into Common (used in ≥ 50% or > 1 paper) and Underrepresented concepts.
   - Includes student helper text explaining the meaning of underrepresented concepts.

### 3. Backend Schema Extensions
- Extended `ProjectResearchDirection` in `backend/app/schemas/project_intelligence_schema.py` with optional rich evidence attributes (`research_problem`, `motivation`, `missing_aspect`, `proposed_direction`, `candidate_algorithms`, `candidate_datasets`).
- Enriched candidate directions in `GlobalResearchIntelligenceService` and `ProjectIntelligenceService`.

---

## Verification & Quality Assurance

1. **Backend Unit Test Suite (`pytest`)**:
   - **Command**: `.\venv\Scripts\python.exe -m pytest`
   - **Result**: `224 passed in 47.96s` (100% pass rate across all 224 backend tests).

2. **Frontend Production Build (`npm run build`)**:
   - **Command**: `npm run build`
   - **Result**: `✓ built in 1.15s` (Clean production build without warnings or syntax errors).

3. **Data Integrity & Non-Destructive Guarantee**:
   - All underlying intelligence algorithms, paper management, research gap services, proposal synthesis, and project persistence remain 100% intact.
