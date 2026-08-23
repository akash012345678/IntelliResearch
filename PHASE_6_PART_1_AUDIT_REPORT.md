# PHASE 6 — PART 1 PRE-IMPLEMENTATION AUDIT REPORT
## RESEARCH PROJECT & PROPOSAL PERSISTENCE ARCHITECTURE AUDIT

**Project:** IntelliResearch — AI-Based Research Gap Discovery and Research Recommendation System  
**Audit Scope:** Codebase, Database, API, Schema, and Persistence Audit prior to Phase 6 Part 1 Implementation  
**Audit Mode:** STRICT READ-ONLY  
**Date:** 2026-08-23  

---

## 1. CURRENT SYSTEM CONTEXT

IntelliResearch currently consists of:

* **PDF Ingestion & Metadata Extraction:** PyMuPDF extraction, structured JSON metadata.
* **Database Layer:** Supabase PostgreSQL (`research_papers` table with 16 indexed research papers).
* **Semantic Index Layer:** Sentence-BERT (`all-MiniLM-L6-v2`) + FAISS L2 vector store.
* **Knowledge Graph:** NetworkX `DiGraph` (84 nodes, 126 edges built from indexed paper metadata).
* **Analysis & Gap Engines:** `LinkPredictionService` (357 candidate graph edges), `ResearchGapService`, `GlobalResearchIntelligenceService`.
* **Proposal Synthesizer:** `ProposalDraftService` supporting Mode 1 (LLM-guided) & Mode 2 (deterministic template fallback).
* **Export Engine:** `ProposalExportService` rendering Markdown (`.md`), JSON (`.json`), and PDF (`.pdf`) downloads.
* **Frontend UI:** React + Tailwind CSS web application containing Home, Dashboard, Semantic Search, Knowledge Graph, Global Research Analysis (`/research-analysis`), and Research Proposal Workspace Modal.

### Verified Baseline Test & Build Status:
* **Backend Pytest Test Suite:** **179 Passed, 1 Skipped, 0 Failures** (36.99s).
* **Frontend Production Build (`npm run build`):** **0 Errors, 0 Warnings** (`✓ built in 526ms`).

---

## 2. DATABASE MODEL AUDIT

An inspection of `backend/app/models/` and the entire backend codebase confirms that **only one SQLAlchemy database model currently exists**:

* **Model File:** **[`backend/app/models/paper_model.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/models/paper_model.py)**
* **SQLAlchemy Class:** `ResearchPaper(Base)`
* **Database Table:** `research_papers`
* **Table Columns:**
  - `id`: Column(Integer, primary_key=True, index=True)
  - `title`: Column(String(500), nullable=False, index=True)
  - `abstract`: Column(Text, nullable=True)
  - `full_text`: Column(Text, nullable=False)
  - `filename`: Column(String(255), nullable=False)
  - `uploaded_at`: Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  - `keywords`: Column(JSON, nullable=False, default=list)
  - `algorithms`: Column(JSON, nullable=False, default=list)
  - `datasets`: Column(JSON, nullable=False, default=list)
  - `methodologies`: Column(JSON, nullable=False, default=list)
  - `application_domains`: Column(JSON, nullable=False, default=list)

### Search Findings for Project / Proposal Models:
Searches for `ResearchProject`, `Project`, `Proposal`, `ProposalDraft`, `Workspace`, `Version`, `Saved`, and `Bookmark` returned **zero database models**. No SQLAlchemy tables exist for projects, saved directions, proposals, or proposal versions.

---

## 3. PROPOSAL PERSISTENCE AUDIT

Inspected **[`proposal_draft_schema.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/schemas/proposal_draft_schema.py)**, **[`proposal_draft_service.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/services/proposal_draft_service.py)**, and **[`research_direction_api.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/api/research_direction_api.py)**:

* **Generation Mechanism:** Proposal drafts are generated **dynamically in-memory** upon receiving a `POST /api/research-directions/draft` HTTP request.
* **Database Persistence:** **NO.** Proposal drafts are not saved to Supabase PostgreSQL.
* **File Persistence:** **NO.** Files are rendered on-the-fly as temporary binary/text HTTP attachments during export downloads (`.md`, `.json`, `.pdf`), but no proposal draft files are saved to server disk.
* **Frontend State Persistence:** Proposal drafts are stored **ONLY in transient React component state** (`activeProposalDraft` in `ResearchAnalysis.jsx`).
* **Browser Storage:** **NO.** Browser `localStorage`, `sessionStorage`, or `IndexedDB` are not used.
* **Identifier:** `proposal_id` is generated as an in-memory random UUID string (`f"prop_{uuid.uuid4().hex[:8]}"`).
* **Direction Association:** Linked via `source_direction_id` (e.g. `"dir_1"`).
* **Paper Association:** Linked via `supporting_papers` JSON array containing paper ID, title, and role.
* **Versioning & Editing:** **NO.** No proposal editing or versioning capabilities currently exist.
* **Page Refresh Survival:** **NO.** Refreshing the page clears React state and discards the generated draft.

---

## 4. RESEARCH DIRECTION AUDIT

Inspected **[`research_direction_service.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/services/research_direction_service.py)**, **[`research_direction_api.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/api/research_direction_api.py)**, and **[`ResearchAnalysis.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/ResearchAnalysis.jsx)**:

* **Origin:** Directions are computed dynamically on-demand by aggregating data from PostgreSQL papers, the NetworkX Knowledge Graph, SBERT FAISS semantic embeddings, `LinkPredictionService`, and `ResearchGapService`.
* **Identifiers:** `direction_id` strings (e.g. `"dir_1"`, `"dir_2"`) are assigned dynamically based on sorted list index order.
* **Database Storage:** **NO.** Directions are not stored in any database table.
* **Determinism:** Results are deterministic for a fixed paper collection due to fixed sorting by multi-signal `direction_score`.
* **Saving & Assignment:** Cannot currently be saved, bookmarked, or assigned to a project.

---

## 5. PAPER-PROJECT RELATIONSHIP AUDIT

Searching for `project_id`, `paper_project`, `project_papers`, association tables, collections, or folders returned zero occurrences across the backend and frontend.

> **"Project-to-paper persistence does not currently exist."**

---

## 6. API AUDIT

Below is the complete list of all 11 active backend API endpoints:

| Method | Path | Purpose | DB Read/Write | Current Persistence |
|:---|:---|:---|:---|:---|
| **POST** | `/api/upload` | Upload PDF, extract metadata, SBERT embed, FAISS index | DB Write (`research_papers`) | PostgreSQL + FAISS |
| **GET** | `/api/papers` | Fetch all indexed research papers | DB Read (`research_papers`) | PostgreSQL |
| **GET** | `/api/paper/{id}` | Fetch details for single paper | DB Read (`research_papers`) | PostgreSQL |
| **DELETE** | `/api/paper/{id}` | Delete paper and update FAISS vector store | DB Write (`research_papers`) | PostgreSQL + FAISS |
| **POST** | `/api/semantic/search` | Natural language semantic similarity search | Read | FAISS + PostgreSQL |
| **GET** | `/api/semantic/papers/{id}/related` | Get semantically related papers | Read | FAISS + PostgreSQL |
| **GET** | `/api/knowledge-graph` | Fetch NetworkX graph nodes, edges & stats | Read | NetworkX + PostgreSQL |
| **GET** | `/api/knowledge-graph/statistics` | Fetch Knowledge Graph summary statistics | Read | NetworkX |
| **GET** | `/api/knowledge-graph/top-entities` | Fetch top connected graph entities | Read | NetworkX |
| **GET** | `/api/link-prediction` | Fetch candidate link predictions | Read | NetworkX |
| **GET** | `/api/research-gaps` | Fetch evaluated research gap candidates | Read | NetworkX + FAISS |
| **GET** | `/api/research-intelligence` | Fetch Global Research Intelligence analysis | Read | PostgreSQL + NetworkX + FAISS |
| **GET** | `/api/research-directions` | Fetch Actionable Research Directions | Read | In-Memory Synthesis |
| **GET** | `/api/research-directions/export` | Export directions in Markdown, JSON, PDF | Read | Download Attachment Stream |
| **POST** | `/api/research-directions/draft` | Synthesize structured proposal draft | Read | In-Memory Response |

**Finding:** Zero project management, proposal persistence, or proposal versioning API endpoints currently exist.

---

## 7. FRONTEND PERSISTENCE AUDIT

Inspected `frontend/src/`:

* **Browser Storage Usage:** **ZERO.** No `localStorage`, `sessionStorage`, or `IndexedDB` calls exist.
* **State Management:** Uses standard React component state (`useState`, `useMemo`, `useRef`).
* **Persistence Behavior:** All user state (search filters, selected papers, active proposals, exported statuses) resides strictly in memory and resets on page refresh.

---

## 8. SUPABASE DATABASE & MIGRATION STRATEGY AUDIT

Inspected **[`backend/app/database/session.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/database/session.py)**:

* **Table Initialization:** Tables are created automatically on FastAPI startup via `Base.metadata.create_all(bind=engine)` inside `init_db()`.
* **Migration Strategy:** Inline column migrations exist in `init_db()`. It inspects table columns and issues `ALTER TABLE ... ADD COLUMN ...` statements if new schema columns are missing.
* **Alembic Usage:** Alembic is not configured.
* **PostgreSQL Schema:** Contains 1 table (`research_papers`) with 11 columns.

---

## 9. DATA OWNERSHIP AUDIT

Based on the existing codebase architecture, the safest and cleanest relational structure for Phase 6 is:

```text
ResearchProject
    │
    ├── ProjectPapers (Association table: project_id, paper_id)
    │
    ├── Saved Research Directions (stored direction snapshot linked to project_id)
    │
    └── Proposals (proposal_id, project_id, direction_id, title, status)
            │
            └── ProposalVersions (version_id, proposal_id, version_number, full Pydantic JSON proposal draft data)
```

### Justification:
1. **`ResearchProject` as Top-Level Container:** A researcher creates a project (e.g. "Autonomous Driving Research").
2. **`ProjectPaper` Association:** Papers can belong to one or more projects without duplicating `ResearchPaper` rows.
3. **`Proposal` & `ProposalVersion` Hierarchy:** Allows saving a proposal draft under a project and updating/saving subsequent edits as discrete version history entries.

---

## 10. DUPLICATE FUNCTIONALITY CHECK

A full repository scan confirmed **zero duplicate or conflicting implementations**:
* Project management: **NOT FOUND**
* Saved proposals table: **NOT FOUND**
* Proposal version history: **NOT FOUND**
* Research workspace persistence: **NOT FOUND**
* Paper collections / folders: **NOT FOUND**

---

## 11. DATA MIGRATION SAFETY

Adding Phase 6 models will require:
1. Creating new SQLAlchemy models in `backend/app/models/` (`project_model.py`, `proposal_model.py`).
2. Registering new models in `Base.metadata`.
3. Running `Base.metadata.create_all(bind=engine)` inside `init_db()`.
4. **Safety Verification:** Creating new tables will **NOT alter or drop existing `research_papers` rows**, ensuring 100% backward compatibility and zero data loss.

---

## 12. TEST AUDIT BASELINE

Executed actual baseline tests on the live repository:

* **Backend Pytest:**
  - **Passed:** **179**
  - **Skipped:** **1**
  - **Failed:** **0**
  - **Total Items:** **180**
* **Frontend Build:**
  - **Command:** `npm run build`
  - **Status:** **0 Errors, 0 Warnings** (`✓ built in 526ms`)

---

## 13. REAL DATABASE READ-ONLY VERIFICATION

Ran `scratch/audit_db_readonly.py` against live Supabase PostgreSQL:

* **Database Engine:** PostgreSQL (Dialect: `postgresql`)
* **Existing Tables Count:** **1** (`['research_papers']`)
* **Indexed Research Papers Count:** **16**
* **Existing Project Tables:** `False`
* **Existing Proposal Tables:** `False`

---

## 14. ARCHITECTURE GAP REPORT

| Capability | Existing? | Location | Persistent? | Missing Work |
|:---|:---|:---|:---|:---|
| **Research Papers** | Yes | `paper_model.py`, `paper_api.py` | Yes (PostgreSQL) | Fully complete |
| **Research Directions** | Yes | `research_direction_service.py` | No (In-Memory) | Needs project association & DB saving |
| **Proposal Draft Synthesis** | Yes | `proposal_draft_service.py` | No (In-Memory) | Needs DB persistence layer |
| **Proposal Draft Workspace UI**| Yes | `ProposalWorkspaceModal.jsx` | No (React State)| Needs project context & save/load UI |
| **Proposal Export (MD, JSON, PDF)**| Yes | `proposal_export_service.py` | No (On-the-fly) | Fully complete |
| **Research Projects** | **NO** | None | **NO** | Need `ResearchProject` DB model & API |
| **Project-Paper Relationship** | **NO** | None | **NO** | Need `project_papers` association table |
| **Project-Direction Link** | **NO** | None | **NO** | Need saved direction schema/table |
| **Proposal Database Storage** | **NO** | None | **NO** | Need `proposals` DB table & CRUD API |
| **Proposal Versioning** | **NO** | None | **NO** | Need `proposal_versions` table & version history API |
| **Proposal Editing** | **NO** | None | **NO** | Need draft section editor UI & update API |
| **Proposal History & Retrieval** | **NO** | None | **NO** | Need list proposals API & project proposal browser |
| **Proposal Deletion** | **NO** | None | **NO** | Need `DELETE /api/proposals/{id}` endpoint |

---

## 15. RECOMMENDED PHASE 6 PART 1 ARCHITECTURE

### Recommended Database Models:
1. **`ResearchProject` (`research_projects`):**
   - `id`: Integer, primary key
   - `title`: String(255), nullable=False
   - `description`: Text, nullable=True
   - `created_at`: DateTime(timezone=True), default=func.now()
   - `updated_at`: DateTime(timezone=True), default=func.now(), onupdate=func.now()

2. **`ProjectPaper` (`project_papers`):**
   - `project_id`: Foreign key to `research_projects.id` (primary key)
   - `paper_id`: Foreign key to `research_papers.id` (primary key)
   - `added_at`: DateTime(timezone=True), default=func.now()

3. **`SavedProposal` (`proposals`):**
   - `id`: Integer, primary key
   - `proposal_uuid`: String(100), unique, index=True
   - `project_id`: Foreign key to `research_projects.id`, nullable=True
   - `source_direction_id`: String(100), nullable=True
   - `title`: String(500), nullable=False
   - `current_version_number`: Integer, default=1
   - `created_at`: DateTime(timezone=True), default=func.now()
   - `updated_at`: DateTime(timezone=True), default=func.now()

4. **`ProposalVersion` (`proposal_versions`):**
   - `id`: Integer, primary key
   - `proposal_id`: Foreign key to `proposals.id`, nullable=False
   - `version_number`: Integer, nullable=False
   - `proposal_data`: JSON, nullable=False (stores full Pydantic `ProposalDraft` object)
   - `created_at`: DateTime(timezone=True), default=func.now()

### Recommended API Endpoints:
* `POST /api/projects`: Create a new Research Project
* `GET /api/projects`: List all Research Projects
* `GET /api/projects/{id}`: Get project details, assigned papers, and proposals
* `POST /api/projects/{id}/papers`: Assign paper(s) to project
* `DELETE /api/projects/{id}/papers/{paper_id}`: Remove paper from project
* `POST /api/proposals/save`: Persist a generated proposal draft into DB under a project
* `GET /api/proposals`: List saved proposals (with optional `project_id` query filter)
* `GET /api/proposals/{id}`: Get saved proposal details and version history
* `PUT /api/proposals/{id}`: Update proposal sections and save new version
* `DELETE /api/proposals/{id}`: Delete saved proposal

---

## 16. SAFETY AUDIT VERIFICATION

* Database tables altered or created during audit: **0**
* Records inserted, updated, or deleted: **0**
* Existing Phase 1-5 services modified: **0**
* FAISS vector index modified: **0**
* NetworkX Knowledge Graph modified: **0**

---

AUDIT COMPLETE — READY FOR PHASE 6 PART 1 IMPLEMENTATION
