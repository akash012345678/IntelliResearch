# Phase 8 — Part 5 Pre-Implementation System Audit

## 1. System Overview & Scope
**IntelliResearch** is an AI-based research gap discovery, recommendation, experiment management, and academic manuscript generation system. The architecture connects 15+ sub-modules into an evidence-grounded research pipeline.

---

## 2. Frontend Component Audit

| Component | Category | Purpose | Status |
| font |---|---|---|
| `Header.jsx` | Navigation | Top-level navigation bar (Home, Research Library, My Projects, Research Intelligence) | Verified |
| `Dashboard.jsx` | Home View | Student-centric home dashboard with Active Project, Next Step Card, Recent Projects, and Global Library | Verified |
| `ResearchProjects.jsx` | Project Management | Project list, creation modal, and archive toggle | Verified |
| `ResearchProjectDetails.jsx` | Project Workspace | 5-phase grouped workspace (Discover, Understand, Build, Write, Finalize) | Verified |
| `ResearchJourney.jsx` | Guidance Engine | 10-stage research journey visualization and progress tracking | Verified |
| `ResearchMap.jsx` | Visualization | Student-friendly research map concept graph and paper landscape | Verified |
| `OpportunityExplorerModal.jsx` | Discovery | Detailed exploration of candidate research directions and algorithms | Verified |
| `ResearchIdeaValidationModal.jsx` | Validation | Broader literature validation of research opportunities | Verified |
| `ResearchMethodologyPlannerModal.jsx` | Planning | 24-section methodology blueprint builder | Verified |
| `ResearchExperimentWorkspace.jsx` | Experiments | Experiment run tracking, dataset config, baseline/proposed algorithms, and run metrics | Verified |
| `ResearchResultsAnalysis.jsx` | Analysis | Statistical analysis of recorded results and ablation study evaluation | Verified |
| `ProposalWorkspaceModal.jsx` | Synthesis | Template-guided and LLM-guided research proposal editor with versioning | Verified |
| `AcademicManuscriptWorkspace.jsx` | Writing | 29-section academic manuscript workspace with evidence classification badges | Verified |
| `ClaimEvidencePanel.jsx` | Traceability | Paragraph-level claim evidence trace panel (*"Where did this come from?"*) | Verified |
| `ReferenceManager.jsx` | References | Verified reference manager supporting IEEE, APA, and Harvard styles without metadata fabrication | Verified |
| `AcademicQualityPanel.jsx` | Quality Audit | Result metric mismatch detection, unsupported claim detector, and novelty warnings | Verified |
| `ManuscriptReviewChecklist.jsx` | Pre-Submission | 13-point pre-submission student review checklist | Verified |
| `AcademicDocumentSettings.jsx` | Formatting | Customization controls for 3 formatting profiles (College Project Report, Research Paper, Thesis) | Verified |
| `AcademicDocumentValidator.jsx` | Validation | Placeholder scanner (`TODO`, `TBD`, `[Student Name]`), structure & broken citation link auditor | Verified |
| `AcademicDocumentPreview.jsx` | Preview | Interactive page-by-page document previewer with TOC and Lists of Figures/Tables | Verified |
| `AcademicSubmissionPackage.jsx` | Delivery | Generator for downloadable ZIP submission package containing `/paper/`, `/evidence/`, `/references/`, and `/report/` | Verified |
| `NextResearchStepCard.jsx` | Guidance | Smart next-step card displaying recommended action, rationale, prerequisites, and outcome | Verified |
| `ResearchProjectHealth.jsx` | Health Meter | Deterministic project health meters with transparent calculations | Verified |
| `SubmissionReadinessCard.jsx` | Readiness | Final submission readiness indicator with itemized checks | Verified |
| `StudentHelpTooltip.jsx` | Usability | Jargon-free explanations for complex concepts (*"What does this mean?"*) | Verified |

---

## 3. Backend API Router & Service Audit

| Router / API Module | Endpoints Count | Key Services Involved | Status |
|---|---|---|---|
| `upload_api.py` | 1 | `PDFService`, `KeywordExtractor` | Verified |
| `paper_api.py` | 4 | `PaperService`, `VectorStore` | Verified |
| `search_api.py` | 2 | `SemanticIndexService`, `VectorStore` | Verified |
| `knowledge_graph_api.py` | 3 | `KnowledgeGraphService`, `KnowledgeGraphBuilder` | Verified |
| `research_gap_api.py` | 2 | `ResearchGapService` | Verified |
| `intelligence_api.py` | 2 | `GlobalResearchIntelligenceService` | Verified |
| `research_direction_api.py` | 3 | `ResearchDirectionService` | Verified |
| `research_project_api.py` | 8 | `ResearchProjectService` | Verified |
| `proposal_api.py` | 7 | `ProposalPersistenceService`, `ProposalDraftService`, `ProposalExportService` | Verified |
| `project_intelligence_api.py` | 2 | `ProjectIntelligenceService` | Verified |
| `project_research_report_api.py` | 3 | `ProjectResearchReportService` | Verified |
| `opportunity_evaluation_api.py` | 2 | `OpportunityEvaluationService` | Verified |
| `opportunity_validation_api.py` | 2 | `OpportunityValidationService` | Verified |
| `research_methodology_api.py` | 3 | `ResearchMethodologyService` | Verified |
| `research_experiment_api.py` | 5 | `ResearchExperimentService` | Verified |
| `research_results_analysis_api.py` | 2 | `ResearchResultsAnalysisService` | Verified |
| `research_journey_api.py` | 1 | `ResearchJourneyService` | Verified |
| `academic_manuscript_api.py` | 5 | `AcademicManuscriptService` | Verified |
| `academic_citation_api.py` | 3 | `AcademicCitationService`, `AcademicQualityService` | Verified |
| `academic_document_api.py` | 3 | `AcademicDocumentValidator`, `AcademicDocumentService`, `SubmissionPackageService` | Verified |
| `research_dashboard_api.py` | 1 | `ResearchDashboardService` | Verified |

---

## 4. Database Schema Audit

All database tables are managed via SQLAlchemy ORM models in `backend/app/models/`:
1. `research_papers`: `id`, `title`, `abstract`, `full_text`, `filename`, `uploaded_at`, `keywords`, `algorithms`, `datasets`, `methodologies`, `application_domains`.
2. `research_projects`: `id`, `name`, `description`, `status`, `created_at`, `updated_at`.
3. `project_papers`: `id`, `project_id` (FK), `paper_id` (FK), `added_at`.
4. `saved_research_directions`: `id`, `project_id` (FK), `direction_id`, `title`, `description`, `rationale`, `saved_at`.
5. `research_methodology_plans`: `id`, `project_id` (FK), `direction_id`, `title`, `sections_json`, `created_at`, `updated_at`.
6. `research_experiments`: `id`, `project_id` (FK), `direction_id`, `name`, `purpose`, `experiment_type`, `status`, `dataset_config`, `baseline_config`, `proposed_config`, `environment_config`, `execution_config`, `notes`, `limitations`, `reproducibility_checklist`.
7. `experiment_runs`: `id`, `experiment_id` (FK), `run_number`, `status`, `hyperparameters`, `metrics_summary`, `execution_time_seconds`, `completed_at`.
8. `experiment_results`: `id`, `experiment_id` (FK), `run_id` (FK), `metric_name`, `metric_value`, `split`, `recorded_at`.
9. `research_proposals`: `id`, `project_id` (FK), `current_version_id` (FK), `created_at`, `updated_at`.
10. `proposal_versions`: `id`, `proposal_id` (FK), `version_number`, `title`, `abstract`, `problem_statement`, `proposed_methodology`, `expected_outcomes`, `timeline`, `budget`, `references`, `created_at`.
11. `research_manuscripts`: `id`, `project_id` (FK), `title`, `current_version_number`, `status`, `completeness_score`, `created_at`, `updated_at`.
12. `research_manuscript_versions`: `id`, `manuscript_id` (FK), `version_number`, `title`, `content_json`, `change_summary`, `created_at`.

---

## 5. Audit Conclusion
The codebase is clean, modular, and fully grounded in recorded project evidence. Proceeding with system QA testing and final documentation updates.
