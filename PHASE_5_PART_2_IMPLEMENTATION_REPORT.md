# PHASE 5 PART 2 IMPLEMENTATION REPORT: LLM / TEMPLATE-GUIDED RESEARCH PROPOSAL DRAFT SYNTHESIZER

**Project:** IntelliResearch — AI-Based Research Gap Discovery and Research Recommendation System  
**Phase:** Phase 5 — Part 2: LLM / Template-Guided Research Proposal Draft Synthesizer  
**Status:** PASS — PHASE 5 PART 2 COMPLETE  
**Date:** 2026-08-23  

---

## 1. OBJECTIVE

The objective of **Phase 5 Part 2** was to design, implement, test, and integrate a dual-mode research proposal draft synthesizer. The system transforms Phase 4 Actionable Research Directions into structured academic proposal drafts (`ProposalDraft`) grounded strictly in indexed collection evidence. It supports Mode 1 (LLM-guided synthesis when configured) and Mode 2 (deterministic template-guided fallback synthesis when unconfigured or on error/timeout), guaranteeing 100% application functionality without requiring an LLM API key.

---

## 2. ARCHITECTURE

```text
POST /api/research-directions/draft  (Request: {"direction_id": "dir_1"})
               │
               ▼
   FastAPI Router (research_direction_api.py)
               │
               ▼
   ProposalDraftService (proposal_draft_service.py)
               │
   ┌───────────┴───────────────────────────┐
   ▼                                       ▼
[Mode 1: LLM Provider Configured?]      [Mode 2: Default / Fallback]
   │                                       │
   ├── YES: Call LLMProvider               └── NO or Error/Timeout:
   │        Validate Pydantic Schema           Execute Template Synthesizer
   │        (On Fail ──► Fallback)             (_template_synthesis)
   ▼                                       ▼
ProposalDraft (generation_mode: "llm")   ProposalDraft (generation_mode: "template")
               │                           │
               └───────────┬───────────────┘
                           ▼
              ProposalDraftResponse (HTTP 200)
```

---

## 3. PROPOSAL SCHEMA

Implemented in **[`backend/app/schemas/proposal_draft_schema.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/schemas/proposal_draft_schema.py)**:

* `proposal_id`: Unique proposal identifier string (`prop_<hex8>`).
* `source_direction_id`: ID of the underlying research direction (`dir_1`, etc.).
* `title`: Proposal Title.
* `abstract`: Executive abstract summarizing problem, baseline methods, and proposed exploration.
* `problem_statement`: Evidence-backed research problem.
* `research_motivation`: Justification for investigating underrepresented target aspects.
* `related_work_synthesis`: Synthesis of supporting papers with explicit title & role citations.
* `research_gap`: Evidence-backed missing aspect.
* `proposed_methodology`: Proposed direction for exploration.
* `candidate_algorithms`: List of baseline algorithm names.
* `candidate_datasets`: List of candidate dataset names (or empty list if unmentioned).
* `dataset_evaluation_plan`: Dataset plan or notice requiring further domain evaluation.
* `experimental_plan`: Baseline comparison design and cross-validation plan.
* `evaluation_metrics`: Metrics plan or notice requiring domain-specific selection.
* `expected_contribution`: Proposed analytical contribution statement.
* `limitations`: Collection coverage bounds and study constraints.
* `supporting_papers`: Array of supporting paper metadata objects.
* `evidence_summary`: Multi-signal evidence scores dictionary (`gap_score`, `direction_score`, etc.).
* `generation_mode`: `"llm"` or `"template"`.
* `generation_timestamp`: ISO 8601 UTC timestamp.
* `disclaimer`: Mandatory collection-based academic disclaimer.

---

## 4. PROPOSAL DRAFT SERVICE

Implemented in **[`backend/app/services/proposal_draft_service.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/services/proposal_draft_service.py)**:

* Provides `ProposalDraftService.synthesize_draft(db, direction_id, custom_provider)`.
* Lookups `ResearchDirection` via `ResearchDirectionService`.
* Checks `settings.LLM_PROVIDER` and `settings.LLM_API_KEY`.
* Implements `LLMProvider` abstraction interface for future provider extensions.
* Executes deterministic `_template_synthesis(dir_item)` when LLM is unconfigured or fails.

---

## 5. LLM PROVIDER ABSTRACTION

* Abstract base class `LLMProvider` defines `generate_proposal(direction: ResearchDirection) -> Optional[ProposalDraft]`.
* Optional configuration fields added to **[`settings.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/config/settings.py)**: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`.
* Zero-config guarantee: Absence of LLM configuration seamlessly routes requests to Mode 2 (Template Mode) without throwing errors.

---

## 6. TEMPLATE FALLBACK

* Mode 2 template synthesis generates structured, academically cautious proposals using only supplied Phase 4 evidence.
* If candidate datasets or metrics are unmentioned in evidence, the template explicitly states that further domain evaluation is required rather than fabricating data.

---

## 7. EVIDENCE GROUNDING & ANTI-HALLUCINATION

* Enforces strict collection-based terminology:
  - ✅ *"The indexed collection shows limited representation of this aspect."*
  - ❌ *"No previous research has addressed this problem."*
  - ✅ *"This represents a potential direction for further investigation."*
  - ❌ *"This is a novel research topic."*
* Prohibits hallucinating fake papers, citations, datasets, or empirical accuracy figures.

---

## 8. API ENDPOINT

Implemented in **[`backend/app/api/research_direction_api.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/api/research_direction_api.py)**:

* `POST /api/research-directions/draft`
* Request payload: `{"direction_id": "dir_1"}`
* Response payload: `{"proposal": { ... }}` (HTTP 200 OK)
* Returns 404 Not Found if `direction_id` does not exist in the collection.

---

## 9. ERROR HANDLING

* Non-existent `direction_id` returns HTTP 404.
* LLM provider exceptions, timeouts, or schema mismatches trigger automatic template fallback.
* Unexpected service exceptions return HTTP 500.

---

## 10. TESTING RESULTS

* Executed full backend pytest test suite:
  - **179 Passed, 1 Skipped** out of 180 total tests (34.05s execution time).
  - 100% pass rate in `test_proposal_draft_service.py` (5/5 passed) and `test_research_direction_api.py` (8/8 passed).

---

## 11. IMMUTABILITY VERIFICATION

* **Supabase PostgreSQL Database:** Unchanged (paper count verified before = 12, after = 12).
* **FAISS Vector Store:** Unchanged (read-only).
* **NetworkX Knowledge Graph:** Unchanged (read-only).

---

## 12. PERFORMANCE

* **Template Synthesis Latency:** ~25 ms total response time.
* **Database & Index Overhead:** 0 additional database writes, 0 embedding recalculations, 0 graph rebuilds.

---

## 13. KNOWN LIMITATIONS

* LLM mode is enabled only when valid provider credentials are provided via environment variables.

---

## 14. FINAL STATUS

```text
======================================================================
              PASS — PHASE 5 PART 2 COMPLETE
======================================================================
```
