# IntelliResearch — Final Project Report Outline (Thesis / Project Documentation)

**Document Title**: IntelliResearch: An Evidence-Grounded AI Platform for Student Research Gap Discovery, Experiment Management, and Academic Manuscript Synthesis  
**Target Structure**: 26 Chapters / Sections

---

## 📖 Chapter & Section Structure

### 1. Abstract
- Summary of problem, proposed system, key algorithms, verification results, and academic safety safeguards.

### 2. Introduction
- Background on academic research challenges faced by undergraduate and graduate students.
- Importance of evidence grounding, literature traceability, and reproducibility.

### 3. Problem Statement & Motivation
- Difficulty of finding non-trivial research gaps in paper collections.
- Risk of ungrounded AI essay generators producing fake citations and fake empirical claims.

### 4. Objectives
- Primary & secondary technical objectives of the IntelliResearch platform.

### 5. Existing System vs. Proposed IntelliResearch Platform
- Comparative analysis of manual research workflows, traditional reference managers, LLM writing assistants, and IntelliResearch.

### 6. System Architecture & High-Level Design
- Full architectural diagram (React, FastAPI, Sentence-BERT, FAISS, NetworkX, SQLite/PostgreSQL).

### 7. Core Research Workflow
- 14-stage pipeline from paper ingestion to submission ZIP archive streaming.

### 8. Research Paper Ingestion & Entity Mining
- PDF parsing, SBERT embedding generation, FAISS vector indexing, and algorithm/dataset/methodology keyword extraction.

### 9. Knowledge Graph & Student-Friendly Research Map
- NetworkX concept graph construction, paper-to-paper relationship calculation, and underrepresented concept mining.

### 10. Collection-Scoped Research Gap Discovery Engine
- Algorithmic gap detection based on underrepresented concept co-occurrences.

### 11. Research Opportunity Explorer & Feasibility Evaluation
- Candidate direction generation, difficulty evaluation, and dataset matching.

### 12. Broader Literature Idea Validation
- External collection validation and novelty risk assessment without absolute global claims.

### 13. 24-Section Methodology Blueprint Planner
- Design of structured research methodology plans covering RQs, hypotheses, baselines, and target metrics.

### 14. Research Experiment Workspace & Execution Logging
- Configurable datasets, baseline vs proposed models, hyperparameter logging, and run metrics.

### 15. Statistical Results Analysis & Evidence Engine
- Multi-run statistical evaluation (mean, std dev, min/max range) and ablation study contributions.

### 16. Research Proposal Synthesis & Versioning
- Template-guided proposal generation, proposal workspace editing, version history, and diff comparison.

### 17. 29-Section Evidence-Grounded Academic Manuscript Generator
- Synthesizing 29-section academic papers with 4-level evidence classification badges.

### 18. Claim Evidence Traceability Engine
- Paragraph-level claim trace panel linking manuscript statements to source literature.

### 19. Verified Citation Manager & Reference Engine
- Formatting references in IEEE, APA, and Harvard styles without metadata fabrication.

### 20. Academic Quality Audit & Novelty Safety Checker
- Scans for metric mismatches, unsupported absolute claims, and dangerous novelty assertions.

### 21. Academic Document Formatting & Live Page Layout Engine
- Customization controls for 3 formatting profiles with live TOC and List of Figures rendering.

### 22. Submission Package Generator
- In-memory ZIP archive streaming `/paper/`, `/evidence/`, `/references/`, and `/report/` deliverables.

### 23. Database Architecture & Schema Design
- Detailed ORM schema documentation for all 12 database tables.

### 24. System Verification & QA Testing
- Backend unit/API test results (`pytest`), frontend build verification (`npm run build`), and project isolation checks.

### 25. System Limitations & Future Work
- Discussion of current limitations (e.g. OCR quality of scanned PDFs) and future enhancements (e.g. multi-user live co-authoring).

### 26. Conclusion & References
- Final summary and academic references.
