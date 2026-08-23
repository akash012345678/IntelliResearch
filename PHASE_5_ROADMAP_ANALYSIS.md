# INTELLIRESEARCH — PHASE 5 ROADMAP DISCOVERY & ANALYSIS REPORT

**Project:** IntelliResearch — AI-Based Research Gap Discovery and Research Recommendation System  
**Current Status:** Phase 4 Complete & Verified (164 passed, 1 skipped; Frontend build clean with 0 errors / 0 warnings)  
**Date:** 2026-08-23  

---

## 1. CURRENT SYSTEM STATE (POST PHASE 4)

The IntelliResearch application currently provides a complete, 4-phase production-ready research intelligence platform:

1. **Phase 1 — Research Paper Processing & Persistence:**
   * PDF uploading, validation, disk storage, and PyMuPDF text & layout-heuristic title/abstract extraction.
   * Supabase PostgreSQL database persistence and CRUD operations.
   * Responsive React dashboard interface with search and modal text viewer.

2. **Phase 2 — Semantic Indexing & Vector Search Engine:**
   * Sentence-BERT (`all-MiniLM-L6-v2`) 384-dimensional vector embeddings.
   * FAISS `IndexFlatIP` normalized inner-product vector store with paper ID mapping.
   * Metadata extraction (`KeywordExtractor`) extracting keywords, algorithms, datasets, methodologies, and application domains.
   * Semantic Similarity Search API (`POST /api/papers/search`) and Related Papers API (`GET /api/papers/{id}/related`).

3. **Phase 3 — Knowledge Graph, Link Prediction & Research Gap Detection:**
   * NetworkX directed graph (`KnowledgeGraphService`) populated via `KnowledgeGraphBuilder`.
   * Knowledge Graph visualization UI (`/knowledge-graph`) and API (`GET /api/knowledge-graph`).
   * Classical graph-based `LinkPredictionService` (Jaccard Coefficient, Adamic-Adar Index, Resource Allocation Index).
   * Multi-signal `ResearchGapService` (`GET /api/research-gaps`) evaluating graph structure, semantic similarity, cross-paper support, and underrepresented entities.

4. **Phase 4 — Global Research Intelligence & Actionable Proposal Engine:**
   * `GlobalResearchIntelligenceService` (`GET /api/research-intelligence`) synthesizing collection summary, paper landscape grid, shared concepts, pairwise connections, underrepresented entities, and candidate directions.
   * Metadata date & noise filtering (`KeywordExtractor._is_date_or_noise()`) preserving technical terms (`YOLOv8`, `YOLOv5`, `BERT`, `SBERT`, `LSTM`, `RNN`, `COCO`).
   * Unified Global Research Analysis UI page (`/research-analysis`) featuring interactive connection map (`react-force-graph-2d`), search/filter tools, concept coverage bars, and central CTA button on Dashboard.
   * `ResearchDirectionService` (`GET /api/research-directions`) synthesizing multi-signal collection evidence into structured actionable proposal cards with 4-signal evidence metrics bar, confidence mapping (`High`, `Moderate`, `Low`), candidate entity badges, supporting paper links (`PaperViewModal`), and collection-based disclaimers.

---

## 2. ORIGINAL ROADMAP EVIDENCE

Inspection of project specifications, previous phase deliverables, and repository commits reveals explicit evidence regarding the requirements following Phase 4:

* **Evidence Source 1:** Initial Phase Specification & Architecture Directives
  - *Context:* Earlier phase specifications (Phase 3 Part 1-3 prompts) explicitly deferred **LLM-Based Idea Generation & Proposal Synthesis** stating: *"Do NOT implement LLM-based idea generation yet... Those belong to Parts 4 and 5."*
* **Evidence Source 2:** Phase 4 Part 4 Actionable Direction Directives
  - *Context:* Phase 4 Part 4 established the deterministic multi-signal foundation for research directions (connecting gap score, semantic evidence, link prediction, and underrepresentation into structured proposals).
  - *Goal for Phase 5:* Transition from deterministic collection-based proposals to **LLM-Guided Structured Research Draft Synthesis, Proposal Export Engine, and Mentor/Researcher Customization**.
* **Evidence Source 3:** Repository Structure (`README.md`, `main.py`, `api.js`)
  - *Context:* The current API and UI present proposals dynamically on-screen, but lack report exporting (Markdown, PDF, JSON) and interactive prompt-guided thesis proposal outline generation.

---

## 3. PHASE 5 REQUIREMENTS

Based on repository evidence and original architectural specifications, **Phase 5** represents:

$$\text{Phase 5: LLM-Guided Research Proposal Synthesis, Document Export & Interactive Refinement Engine}$$

### Required (Core Phase 5 Requirements)
1. **Structured Proposal Export Engine:**
   * Backend export service capable of compiling selected research directions or full collection analysis into formatted **Markdown (`.md`)**, **JSON (`.json`)**, or printable **PDF** research proposal summaries.
   * API endpoints for document generation (`GET /api/research-directions/export`).
2. **LLM / Template-Guided Structured Research Draft Synthesizer:**
   * Modular synthesis engine (`ProposalDraftService`) that transforms Phase 4 `ResearchDirection` objects into complete, structured academic project proposals containing:
     - Title & Executive Abstract
     - Problem Statement & Academic Motivation
     - Related Work Synthesis (citing supporting collection papers)
     - Proposed Methodology & Algorithmic Design
     - Benchmark Dataset Evaluation & Metric Plan
     - Expected Collection Impact, Risks & Limitations
     - Mandatory Collection-Based Disclaimer
   * Hybrid architecture: Deterministic template-based fallback with optional LLM API enhancement (OpenAI/Gemini/Ollama) to ensure local offline runnability without breaking if API keys are missing.
3. **Interactive Proposal Customization & Saved Bookmarks:**
   * Frontend controls allowing users to customize proposal parameters (e.g. selecting target algorithms or focusing on specific datasets).
   * Capability to bookmark, save, and download generated project proposal drafts.

### Optional / Deferred Requirements
* Live external academic search API integration (arXiv / Semantic Scholar API lookup to check external literature beyond the local collection).
* Automated baseline Python code snippet generator for initial model setup.

---

## 4. EXISTING IMPLEMENTATION CHECK

| Requirement | Implementation Status | Evidence / Location | Missing Components |
| :--- | :--- | :--- | :--- |
| **Deterministic Proposal Generation** | ✅ Implemented | `ResearchDirectionService` (`backend/app/services/research_direction_service.py`) | None |
| **Proposal API Endpoint** | ✅ Implemented | `GET /api/research-directions` (`backend/app/api/research_direction_api.py`) | Export query format parameter |
| **Proposal UI Presentation** | ✅ Implemented | `ResearchAnalysis.jsx` (`frontend/src/pages/ResearchAnalysis.jsx`) | Export buttons & Draft modal |
| **Structured Proposal Export Engine (MD/PDF/JSON)** | ❌ Not Implemented | None | Backend export service & download API |
| **LLM / Template Proposal Draft Synthesizer** | ❌ Not Implemented | None | Synthesis service & draft outline generator |
| **Interactive Proposal Customization & Bookmarking** | ❌ Not Implemented | None | User bookmarks state & customization filters |

---

## 5. DEPENDENCY ANALYSIS

Phase 5 will build directly on existing Phase 1–4 components without rewriting working modules:

* **Backend Services Reused:**
  - `ResearchDirectionService` (provides deterministic proposal evidence)
  - `GlobalResearchIntelligenceService` (provides collection landscape context)
  - `ResearchGapService` (provides gap metrics)
  - `KnowledgeGraphService` & `KnowledgeGraphBuilder` (provides entity relationships)
  - `EmbeddingService` & `VectorStore` (provides semantic similarities)
* **Backend Schemas Reused:**
  - `research_direction_schema.py` (`ResearchDirection`, `ResearchDirectionEvidence`, `SupportingPaper`)
* **Database Models:**
  - `ResearchPaper` (`app/models/paper_model.py`) — read-only access for supporting paper metadata
* **Frontend Modules:**
  - `ResearchAnalysis.jsx` (embed export actions & draft generator trigger)
  - `PaperViewModal.jsx` (reuse for paper inspection)
  - `api.js` (add export and draft endpoints)

---

## 6. RISKS

1. **Academic Novelty Disclaimer Risk:**
   * *Risk:* LLM draft generation might produce overly confident claims (e.g., "first-ever guaranteed breakthrough").
   * *Mitigation:* Enforce strict collection-based prompt scoping and append mandatory collection disclaimers to all exported documents.
2. **External API Dependency Risk:**
   * *Risk:* If LLM API keys are missing or offline, proposal synthesis could fail.
   * *Mitigation:* Implement a robust deterministic template-based synthesizer as default fallback, enriching output with LLM text only when configured.
3. **Immutability & Data Consistency Risk:**
   * *Risk:* Exporting or bookmarking proposals must not alter indexed paper records or vector stores.
   * *Mitigation:* Keep export and draft synthesis operations 100% read-only with respect to Supabase PostgreSQL, FAISS, and NetworkX.
4. **Performance & Generation Latency:**
   * *Risk:* PDF generation or LLM synthesis could delay API responses.
   * *Mitigation:* Use lightweight backend document builders (e.g. Markdown / reportlab / HTML-to-PDF) and async handlers.

---

## 7. RECOMMENDED IMPLEMENTATION ORDER

For Phase 5, we recommend breaking execution into 5 clean, testable sub-parts:

1. **Phase 5 — Part 1: Structured Research Proposal Export Engine (Backend & API)**
   - Create `backend/app/services/proposal_export_service.py` to generate Markdown, JSON, and PDF reports from Phase 4 directions.
   - Add `GET /api/research-directions/export` endpoint.
   - Write backend pytest unit tests.
2. **Phase 5 — Part 2: LLM / Template-Guided Proposal Draft Synthesizer**
   - Create `backend/app/services/proposal_draft_service.py` synthesizing full project proposals (Abstract, Related Work, Methodological Plan, Evaluation Blueprint).
   - Add `POST /api/research-directions/draft` endpoint.
3. **Phase 5 — Part 3: Interactive Proposal Customization & Saved Bookmarks**
   - Add frontend proposal bookmarking and customization state in `ResearchAnalysis.jsx`.
4. **Phase 5 — Part 4: Frontend Export & Draft Synthesis UI Integration**
   - Integrate `[Export Proposal]` dropdown (Markdown / PDF / JSON) and `[Generate Draft Proposal]` modal into `ResearchAnalysis.jsx`.
5. **Phase 5 — Part 5: Final Phase 5 Validation & End-to-End Audit**
   - Execute full backend pytest suite (165+ tests) and frontend build (`npm run build`).

---

## 8. PHASE 5 COMPLETION CRITERIA

1. Users can export actionable research directions in **Markdown (`.md`)**, **PDF**, or **JSON** format directly from `/research-analysis`.
2. Generated proposal draft outlines contain structured academic sections (Problem Statement, Related Work Synthesis, Proposed Methodology, Dataset Evaluation Plan, Disclaimers).
3. System operates with zero failure when LLM API keys are absent (using deterministic template synthesis).
4. All existing Phase 1–4 functionality remains intact and functional.
5. All backend pytest unit and integration tests pass cleanly.
6. Frontend production build (`npm run build`) completes with **0 errors and 0 warnings**.
7. Supabase PostgreSQL database, FAISS index, and NetworkX Knowledge Graph remain unmutated (read-only).

---

## 9. RECOMMENDED NEXT PROMPT

To begin Phase 5 implementation, use the following prompt:

```text
Implement Phase 5 — Part 1 of IntelliResearch: Structured Research Proposal Export Engine.

Create `backend/app/services/proposal_export_service.py` supporting Markdown, JSON, and PDF report generation for Phase 4 research directions.
Expose `GET /api/research-directions/export` in `backend/app/api/research_direction_api.py`.
Add unit tests in `backend/tests/test_proposal_export_service.py`.
Ensure all backend tests pass and database/FAISS/graph remain read-only.
```
