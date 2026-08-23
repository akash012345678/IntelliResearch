# IntelliResearch — Academic Presentation & Defense Slide Deck Outline

**Title**: IntelliResearch — AI-Based Research Gap Discovery, Experiment Management & Evidence-Grounded Academic Manuscript Generation Platform  
**Target Duration**: 15–20 Minutes (21 Slides)

---

## 📽️ Slide Deck Structure

### Slide 1: Title Slide
- **Title**: IntelliResearch: AI-Based Research Gap Discovery & Recommendation System
- **Subtitle**: An Evidence-Grounded Platform for Student Research Journey Management
- **Presenter Info**: Student Name, Department, Institution, Date

### Slide 2: Problem Statement & Motivation
- **Context**: Undergraduate and graduate students struggle with navigating academic literature.
- **Challenges**: Identifying true research gaps, formulating structured methodologies, tracking experiment runs, and writing rigorous academic manuscripts.
- **Consequence**: High student burnout, repetitive literature reviews, and unsupported research claims.

### Slide 3: Existing Limitations & Gaps in Current Tools
- **Generic AI Writers**: Produce ungrounded essays with fabricated citations and hallucinated experiment numbers.
- **Reference Managers**: Store PDFs without concept graph analysis or research gap discovery.
- **Fragmented Workflows**: Separate tools for papers, spreadsheets for experiments, and docs for writing.

### Slide 4: Proposed Solution — IntelliResearch
- **Core Concept**: One unified platform connecting literature papers to gap discovery, methodology planning, experiment tracking, statistical analysis, and manuscript generation.
- **Key Principle**: **100% Evidence Grounding** — zero fabricated metrics, fake citations, or fake novelty claims.

### Slide 5: System Architecture & Data Flow
- **Architecture Diagram**: React Frontend $\leftrightarrow$ FastAPI Backend $\leftrightarrow$ Sentence-BERT + FAISS + NetworkX + SQLite/PostgreSQL.
- **Core Pipeline**: Papers $\rightarrow$ Research Map $\rightarrow$ Gaps $\rightarrow$ Opportunities $\rightarrow$ Validation $\rightarrow$ Plan $\rightarrow$ Experiments $\rightarrow$ Results $\rightarrow$ Proposal $\rightarrow$ Academic Paper $\rightarrow$ Submission Package.

### Slide 6: Research Paper Collection & Ingestion
- **PDF Extraction**: Automated full-text and metadata parsing.
- **Keyword & Entity Extraction**: Automated identification of algorithms, datasets, methodologies, and application domains.
- **Semantic Indexing**: SBERT dense embeddings stored in FAISS for fast similarity search.

### Slide 7: Student-Friendly Research Map & Concept Graphs
- **Visual Graph**: Concept graph rendering paper relationships and shared topics.
- **Overlaps & Underrepresented Topics**: Highlights topics appearing in only a few papers to reveal potential research gaps.

### Slide 8: Collection-Scoped Research Gap Discovery
- **Gap Mining**: Algorithmic detection of underrepresented algorithm-dataset combinations.
- **Student Language**: Translates graph metrics into plain explanations (*"Appears in only 2 papers in your collection"*).

### Slide 9: Evidence-Grounded Research Opportunity Explorer
- **Opportunity Recommendations**: Candidate research directions grounded in paper concepts.
- **Feasibility Evaluation**: Assesses technical difficulty, required dataset size, and baseline availability.

### Slide 10: Broader Literature Validation
- **Literature Checking**: Evaluates candidate gaps against broader literature indexes.
- **Academic Safety**: Warns student if the gap is already addressed in external literature without claiming absolute global novelty.

### Slide 11: 24-Section Methodology Blueprint
- **Structured Planning**: Defines RQs, hypotheses, baseline algorithms, proposed architectures, hardware requirements, and target metrics.

### Slide 12: Controlled Experiment Workspace & Metric Logging
- **Run Tracking**: Configures baseline vs proposed models, hyperparameter configurations, and execution times.
- **Data Grounding**: Unrecorded entries display `"Results not yet recorded"` — zero fake numbers.

### Slide 13: Statistical Results Analysis & Ablation Studies
- **Statistical Evaluation**: Computes mean, standard deviation, min/max ranges, and ANOVA across multiple seed runs.
- **Ablation Evaluation**: Measures module-by-module performance contributions.

### Slide 14: Structured Research Proposal Workspace
- **Proposal Synthesis**: Assembles literature review, methodology blueprint, and expected outcomes into exportable proposal drafts.
- **Versioning**: Full version history supporting version switching and diff comparison.

### Slide 15: 29-Section Evidence-Grounded Academic Manuscript
- **Section Generation**: Synthesizes 29 academic manuscript sections (Abstract, Intro, Lit Review, Methodology, Experiments, Results, Discussion, Conclusion, Appendices).
- **Classification Badges**: 🟢 RECORDED, 🟡 DERIVED, 🔵 PROPOSED, 🔴 MISSING.

### Slide 16: Claim Evidence Traceability & Verified Reference Manager
- **Claim Traceability**: Paragraph-level trace links back to source literature.
- **Reference Formatter**: Formats references in IEEE, APA, and Harvard styles; flags incomplete metadata.

### Slide 17: Academic Quality Audit & Novelty Safety Checker
- **Metric Mismatch Detection**: Scans draft manuscript text against database experiment records to highlight discrepancies.
- **Absolute Claim Warning**: Flags dangerous terms (*"superior"*, *"guarantees"*, *"first ever"*) and suggests cautious alternatives.

### Slide 18: Document Formatting & Interactive Live Preview
- **Formatting Profiles**: College Project Report, Research Paper, and Thesis profiles.
- **Live Preview Engine**: Renders live page layout with automated Table of Contents and List of Figures.

### Slide 19: ZIP Submission Package Generator
- **Deliverables**: Single `.zip` archive streaming `/paper/`, `/evidence/`, `/references/`, and `/report/` subdirectories.

### Slide 20: System Verification & Testing Results
- **Backend Test Suite**: 100% pass rate across 256+ `pytest` unit & API tests.
- **Frontend Build**: Production build compiled in 545ms with 0 errors.

### Slide 21: Conclusion & Q&A
- **Summary**: IntelliResearch empowers students to conduct rigorous, evidence-grounded research from literature review to final submission.
- **Q&A**: Open for evaluator questions.
