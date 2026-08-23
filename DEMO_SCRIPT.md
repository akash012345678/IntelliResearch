# IntelliResearch — Demonstration Script & Guide

**Total Duration**: ~12–15 Minutes  
**Target Audience**: Academic Evaluators, Professors, Project Reviewers & Students

---

## Demonstration Timeline & Step-by-Step Script

### 🕒 0:00–1:00 | Introduction & Core Problem
- **Presenter**: *"Welcome to IntelliResearch! For undergraduate and graduate students, transforming a collection of research papers into a novel, evidence-grounded research project is daunting. Students struggle with identifying real research gaps, designing controlled methodology, tracking experiment runs, and synthesizing structured academic manuscripts. IntelliResearch solves this by guiding students step-by-step through a 14-stage evidence-grounded research workflow."*
- **Screen**: Navigate to Home Dashboard (`/`). Show Hero Banner and Global Literature Collection count.

---

### 🕒 1:00–2:30 | Project Creation & Research Journey
- **Action**: Click **My Projects** (`/research-projects`). Select **"Smart Medical Image Segmentation"** or create a new project.
- **Presenter**: *"Inside our project workspace, the Student Research Journey immediately answers three questions: Where am I? What should I do next? And why does it matter? Look at our Next Step Recommendation Card—it highlights our active stage, prerequisites, and expected outcome."*
- **Screen**: Show `ResearchJourney.jsx`, `NextResearchStepCard.jsx`, and transparent health meters in `ResearchProjectHealth.jsx`.

---

### 🕒 2:30–4:30 | Discovery: Research Map & Paper Concepts
- **Action**: Switch to **DISCOVER** phase tab $\rightarrow$ **Map** (`tab=map`).
- **Presenter**: *"In the DISCOVER phase, the Student-Friendly Research Map visualizes how our assigned literature papers connect. We see shared algorithms, datasets, and underrepresented topics highlighted in green and purple. We can also view pairwise paper relationships and shared concepts without deciphering complex graph terminology."*
- **Screen**: Show graph nodes, cluster overlays, concept tags, and underrepresented concept lists.

---

### 🕒 4:30–6:00 | Understand: Research Gaps & Opportunity Explorer
- **Action**: Switch to **UNDERSTAND** phase tab $\rightarrow$ **Gaps** (`tab=gaps`) and **Opportunities** (`tab=directions`). Open **Opportunity Explorer Modal**.
- **Presenter**: *"In the UNDERSTAND phase, IntelliResearch identifies gaps in our paper collection. Notice how it translates these gaps into actionable research directions—suggesting target algorithms, baseline models, and evaluation datasets. We can validate our candidate idea against external literature to confirm that the gap exists before building our plan."*
- **Screen**: Open `OpportunityExplorerModal.jsx` and `ResearchIdeaValidationModal.jsx`.

---

### 🕒 6:00–8:00 | Build: Methodology Planner & Experiment Workspace
- **Action**: Switch to **BUILD** phase tab $\rightarrow$ **Research Plan** (`tab=plan`) and **Experiments** (`tab=experiments`).
- **Presenter**: *"Now we move to the BUILD phase. Our 24-section Methodology Blueprint outlines our research questions, hypotheses, baseline architectures, and metric targets. Next, in the Experiment Workspace, we log controlled execution runs. Notice that all metrics—Accuracy, F1-score, Latency—reflect real recorded student runs. If a metric is unrecorded, IntelliResearch displays 'Results not yet recorded' rather than fabricating fake numbers."*
- **Screen**: Show 24-section methodology blueprint, experiment run tables, multi-run mean/std dev calculations, and `ResearchResultsAnalysis.jsx`.

---

### 🕒 8:00–10:30 | Write: Academic Manuscript & Citation Intelligence
- **Action**: Switch to **WRITE** phase tab $\rightarrow$ **Academic Paper** (`tab=manuscript`).
- **Presenter**: *"In the WRITE phase, IntelliResearch synthesizes a structured 29-section academic manuscript grounded in our recorded project evidence. Each section features evidence classification badges: Green for Recorded Evidence, Yellow for Derived Analysis, and Blue for Proposed Methodology. Click on the Claim Evidence panel to see paragraph-level traceability back to source literature papers. In the Reference Manager, citations are formatted in IEEE, APA, or Harvard style with incomplete metadata explicitly flagged."*
- **Screen**: Show `AcademicManuscriptWorkspace.jsx`, `ClaimEvidencePanel.jsx`, and `ReferenceManager.jsx`.

---

### 🕒 10:30–12:30 | Finalize: Quality Audit, Formatting & Live Preview
- **Action**: Switch to **Quality Audit**, **Formatting**, and **Preview** tabs.
- **Presenter**: *"Before submission, our Academic Quality Audit scans for result metric mismatches, unsupported absolute claims, and dangerous novelty assertions. Next, in Document Formatting, we select our target profile—College Project Report—and interact with a live page-by-page preview featuring an automated Table of Contents and List of Figures."*
- **Screen**: Show `AcademicQualityPanel.jsx`, `AcademicDocumentSettings.jsx`, and `AcademicDocumentPreview.jsx`.

---

### 🕒 12:30–14:00 | Submission Package & Wrap-Up
- **Action**: Open **Submission Package** tab (`tab=submission`) and click **Download Submission Package (.ZIP)**.
- **Presenter**: *"Finally, with a single click, IntelliResearch packages our complete project deliverables into a ready-to-submit ZIP archive containing `/paper/`, `/evidence/`, `/references/`, and `/report/` folders. IntelliResearch seamlessly transforms uploaded papers into an evidence-grounded, submission-ready research project!"*
- **Screen**: Show `AcademicSubmissionPackage.jsx`, downloaded ZIP contents, and final completion screen.
