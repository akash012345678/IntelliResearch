# Phase 6 Part 6 — Pre-Implementation Audit Report

## Executive Summary
This pre-implementation audit analyzes the complete IntelliResearch codebase (frontend components, routing, services, and backend endpoints) to prepare for Phase 6 Part 6: **Project Workspace End-to-End Integration & Final UX**.

---

## 1. Audit of Frontend Components & Navigation

### 1.1 `App.jsx` & `Header.jsx`
- **Current State**: `App.jsx` defines HashRouter with routes: `/`, `/dashboard`, `/knowledge-graph`, `/research-intelligence`, `/research-analysis`, `/research-projects`, `/research-projects/:projectId`.
- **Finding**: Navigation between pages is functional, but there is no direct visual workflow indicator guiding researchers from paper upload -> project creation -> workspace analysis -> proposal draft -> report export.
- **Header z-index**: `Header.jsx` has `sticky top-0 z-40`.

### 1.2 `ResearchProjectDetails.jsx`
- **Current State**: Serves as the detail view for `/research-projects/:projectId`.
- **Finding 1 (Tab State Persistence)**: The active workspace tab is currently stored only in React state (`useState('overview')`). On browser refresh or deep-linking, the selected tab resets to `overview`.
- **Finding 2 (Missing Proposals Tab)**: There is no dedicated `Proposals` workspace tab listing all proposals persisted under the project with actions for Edit, Compare, Version History, Restore, and Delete. Currently, proposals can only be opened from the `Proposal Traceability` tab or `ResearchAnalysis.jsx`.
- **Finding 3 (Missing Research Report Tab)**: Research Report is currently triggered solely via a top action button opening `ProjectResearchReportModal`. Incorporating a dedicated `Research Report` tab provides direct inline access to project report view and export.
- **Finding 4 (Scope Indicator)**: The page shows metric cards, but lacks an explicit `PROJECT SCOPE (X papers)` indicator to clearly differentiate project-scoped intelligence from global intelligence.

### 1.3 `ResearchProjects.jsx`
- **Current State**: Lists all research projects, allows creating new projects, shows project cards with paper counts.
- **Finding**: Clicking a project card correctly navigates to `/research-projects/:projectId`. However, creating a project does not automatically prompt adding initial research papers.

### 1.4 `ResearchIntelligence.jsx` & `ResearchAnalysis.jsx`
- **Current State**: Provide global collection intelligence across all indexed papers in FAISS/SQL database.
- **Finding**: Terminology in UI headers switches between "Global Research Analysis", "Global Research Intelligence", and "Research Intelligence". Adding a clear `GLOBAL SCOPE (N papers)` tag prevents confusion with `PROJECT SCOPE (X papers)`.

### 1.5 Modals Audit
- **`PaperViewModal.jsx`**: Portaled to `document.body` with `z-[100]`, fixed header (`shrink-0`), scrollable content (`min-h-0 flex-1 overflow-y-auto`), stationary footer (`shrink-0`), and `document.body.style.overflow = 'hidden'` scroll locking. Excellent architecture.
- **`ProposalWorkspaceModal.jsx`**: Portaled to root, handles drafting, section editing, version history, proposal comparison, version restoration, and PDF/MD export.
- **`ProjectResearchReportModal.jsx`**: Displays complete project research report with section navigation and PDF/MD/JSON export.
- **`ProjectPaperSelector.jsx`**: Allows multi-selection of available papers and bulk adding them to a project.

---

## 2. Audit of 10 Critical System Areas

1. **Duplicate UI Functionality**:
   - `ResearchAnalysis.jsx` and `ResearchIntelligence.jsx` both expose direction drafting and proposal synthesis. Proposal drafting from directions should seamlessly redirect or link into the project workspace proposal tab/modal.

2. **Broken Navigation / State in URLs**:
   - Tab switching in `ResearchProjectDetails.jsx` does not update the URL query string (`?tab=papers`, `?tab=gaps`, `?tab=proposals`). Deep-linking and page refresh fail to retain tab context.

3. **Inconsistent Terminology**:
   - Mixed usage of "Documents" vs. "Research Papers", "Workspace" vs. "Research Project", "Missing Item" vs. "Research Gap". Standardized terms must be enforced across all views.

4. **Missing Navigation Paths**:
   - After saving a research direction or saving a proposal from `ResearchAnalysis.jsx`, there was no direct link to navigate straight to the destination project workspace.

5. **Stale State After Mutations**:
   - Adding or removing papers in `ResearchProjectDetails.jsx` calls `fetchProjectData()`, which refreshes intelligence, but removing a paper did not re-fetch the proposals or direction list.

6. **Inconsistent Loading States**:
   - Buttons during paper assignment, direction saving, or proposal version restoration did not always show inline spinners or disabled states.

7. **Inconsistent Error Handling**:
   - Some error states printed raw `err.message` in alerts instead of structured user-friendly error banners with `[ Retry ]` options.

8. **Inconsistent Empty States**:
   - Zero-paper projects displayed metric cards with 0s and empty tables without a prominent CTA guiding the researcher to "Add Research Papers".

9. **Modal Stacking Problems**:
   - Verified that `PaperViewModal` and `ProposalWorkspaceModal` use `z-[100]` and `createPortal(..., document.body)`. `ProjectResearchReportModal` and `ProjectPaperSelector` must also be double-checked for z-index layering above `Header.jsx`.

10. **Unnecessary API Data Reloading**:
    - Switching tabs inside `ResearchProjectDetails.jsx` previously triggered full project re-fetch instead of reusing the already-loaded `intelligence` object.

---

## 3. Backend API Audit Findings

- **Project APIs (`/api/projects`)**:
  - `POST /api/projects` - Create project
  - `GET /api/projects` - List projects
  - `GET /api/projects/{id}` - Get project details
  - `PATCH /api/projects/{id}` - Update project (name, status, description)
  - `DELETE /api/projects/{id}` - Delete project
  - `POST /api/projects/{id}/papers/{paper_id}` - Add paper
  - `POST /api/projects/{id}/papers/bulk` - Bulk add papers
  - `DELETE /api/projects/{id}/papers/{paper_id}` - Remove paper
  - `GET /api/projects/{id}/papers` - List project papers
  - `GET /api/projects/{id}/available-papers` - Search unassigned papers

- **Direction APIs (`/api/projects/{id}/directions`)**:
  - `POST /api/projects/{id}/directions` - Save direction
  - `GET /api/projects/{id}/directions` - List directions
  - `DELETE /api/projects/{id}/directions/{direction_id}` - Delete direction

- **Proposal APIs (`/api/proposals`)**:
  - `POST /api/proposals` - Save proposal
  - `GET /api/proposals/{id}` - Get proposal
  - `GET /api/projects/{id}/proposals` - List project proposals
  - `DELETE /api/proposals/{id}` - Delete proposal (Backend endpoint exists, frontend `api.js` wrapper missing)
  - `PATCH /api/proposals/{id}` - Edit proposal
  - `GET /api/proposals/{id}/versions` - List version history
  - `GET /api/proposals/{id}/compare` - Compare versions
  - `POST /api/proposals/{id}/restore/{version}` - Restore version

- **Project Intelligence & Report APIs**:
  - `GET /api/projects/{id}/research-intelligence` - Compute project-scoped intelligence
  - `GET /api/projects/{id}/research-report` - Generate report JSON
  - `GET /api/projects/{id}/research-report/export` - Export PDF/Markdown/JSON report

- **Backend Gap**: Frontend `api.js` was missing `deleteProposal(proposalId)`.

---

## 4. Integration & Refactoring Plan

1. **Add `deleteProposal` to `frontend/src/services/api.js`**.
2. **Refactor `ResearchProjectDetails.jsx`**:
   - Synchronize `activeTab` with URL query param (`useSearchParams`: `?tab=overview`, `?tab=papers`, `?tab=connections`, `?tab=concepts`, `?tab=gaps`, `?tab=directions`, `?tab=proposals`, `?tab=traceability`, `?tab=report`).
   - Add explicit **`PROJECT SCOPE (X papers)`** badge in header.
   - Implement **Proposals Tab** displaying all saved project proposals with status, version number, draft mode, last updated date, and actions for `[ Open ]`, `[ Edit ]`, `[ Compare ]`, `[ Version History ]`, `[ Export ]`, and `[ Delete ]`.
   - Implement **Research Report Tab** rendering an in-workspace report viewer with inline export buttons for PDF, Markdown, and JSON.
   - Enhance empty state for projects with 0 papers to show prominent "This research project has no papers yet" guidance.
   - Ensure removing a paper refreshes project intelligence, direction lists, and proposal lists without re-rendering unrelated global views.
3. **Audit & Standardize Terminology**:
   - Consistently use "Research Paper", "Research Project", "Research Direction", "Research Gap", "Research Proposal", "Proposal Version", "Project Research Intelligence", "Global Research Intelligence", "Evidence Traceability".
4. **Modal Layering Audit**:
   - Ensure all workspace modals use root portals (`createPortal`) and `z-[100]`.
5. **Testing & Verification**:
   - Run `pytest` for backend verification.
   - Run `npm run build` to ensure 0 errors and 0 warnings.
   - Perform full E2E workflow testing in browser.
