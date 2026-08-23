# IntelliResearch — AI-Based Research Gap Discovery & Recommendation Platform

IntelliResearch is an end-to-end AI-powered academic platform designed to guide undergraduate and graduate students through the entire research journey—from research paper collection to paper landscape exploration, research gap discovery, opportunity validation, 24-section methodology planning, empirical experiment tracking, results analysis, proposal drafting, academic manuscript synthesis, citation quality auditing, document formatting, and ZIP submission packaging.

---

## 🌟 Key Features & Capabilities

### 1. Research Discovery & Landscape Exploration
- **Student-Friendly Research Map**: Visually explains paper-to-paper relationships, shared concepts, underrepresented concept overlaps, and research gaps.
- **Global & Project Intelligence**: Dual-scoped research intelligence engine separating global repository literature from project-assigned paper collections.
- **Semantic Search**: Vector similarity search over indexed paper abstracts and full text powered by Sentence-BERT embeddings.

### 2. Opportunity Discovery & Literature Validation
- **Evidence-Grounded Opportunities**: Recommends candidate algorithms, datasets, and methodologies grounded in paper concept graphs.
- **Broader Literature Validation**: Validates research opportunities against indexed collections to verify external support without claiming global academic novelty.

### 3. Methodology & Experiment Workspace
- **24-Section Methodology Blueprint**: Structured research plan builder covering RQs, hypotheses, baseline algorithms, proposed architectures, hardware setup, and evaluation metrics.
- **Controlled Experiment Tracking**: Configures datasets, baseline methods, proposed models, execution parameters, and multi-run metric logging.
- **Statistical Results Analysis**: Analyzes recorded empirical results, computes mean/std dev/ranges, evaluates ablation studies, and generates cautious academic conclusions.

### 4. Writing, Quality Audit & Submission Package
- **29-Section Academic Manuscript Generator**: Synthesizes structured academic paper drafts with 4-level evidence classification badges (🟢 RECORDED, 🟡 DERIVED, 🔵 PROPOSED, 🔴 MISSING).
- **Citation Intelligence & Reference Manager**: Verified IEEE, APA, and Harvard reference formatting without metadata fabrication.
- **Academic Quality Audit**: Automatically detects result metric mismatches against database records, unsupported absolute claims (*"superior"*, *"guarantees"*), and dangerous novelty warnings (*"first"*, *"unprecedented"*).
- **Document Formatting & Preview**: Supports College Project Report, Research Paper, and Thesis formatting profiles with live page-by-page rendering (TOC, List of Figures, List of Tables, Appendices A/B/C).
- **ZIP Submission Package Generator**: Exports a single `.zip` containing `/paper/`, `/evidence/`, `/references/`, and `/report/` deliverables.

---

## 🚀 Complete Research Workflow

$$\text{PAPERS} \rightarrow \text{MAP} \rightarrow \text{GAP} \rightarrow \text{OPPORTUNITY} \rightarrow \text{VALIDATE} \rightarrow \text{PLAN} \rightarrow \text{🧪 EXPERIMENTS} \rightarrow \text{📊 RESULTS} \rightarrow \text{PROPOSAL} \rightarrow \text{📄 ACADEMIC PAPER} \rightarrow \text{📐 FORMATTING} \rightarrow \text{📦 SUBMISSION PACKAGE (.ZIP)}$$

---

## 🛠️ Technology Stack

- **Frontend**: React (Vite), TailwindCSS, Lucide-React, React-Router-DOM, Axios
- **Backend**: Python 3.11/3.13, FastAPI, SQLAlchemy ORM, Pydantic V2, Pytest
- **AI & NLP**: Sentence-Transformers (Sentence-BERT), FAISS (Facebook AI Similarity Search), NetworkX, PyPDF2
- **Database**: SQLite / PostgreSQL (Relational persistence for projects, experiments, proposals, manuscripts)

---

## 📂 Project Structure

```
IntelliResearch/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI Routers (20+ Routers)
│   │   ├── models/               # SQLAlchemy ORM Models (Project, Paper, Experiment, Proposal, Manuscript)
│   │   ├── schemas/              # Pydantic Schemas & DTOs
│   │   ├── services/             # Core Business Logic & AI Engines
│   │   ├── database/             # DB Connection & Session Management
│   │   └── main.py               # FastAPI App Entrypoint
│   └── tests/                    # Comprehensive Pytest Suite (256+ Tests)
├── frontend/
│   ├── src/
│   │   ├── components/           # UI Components (Workspace Editors, Previewers, Modals, Panels)
│   │   ├── pages/                # Views (Dashboard, ResearchProjectDetails, ResearchIntelligence, Projects)
│   │   ├── services/             # Axios API Client
│   │   └── App.jsx               # Main Route Config
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🛡️ Academic Integrity & Safety Rules

1. **Zero Empirical Data Fabrication**: Unrecorded experiment metrics strictly display `"Results not yet recorded."`
2. **No Fake Metadata**: Missing author, year, or DOI metadata is explicitly labeled `"Bibliographic metadata incomplete"` without generating fake citations.
3. **Non-Destructive Editing**: Student edits to draft manuscript or proposal text modify version records only, and **NEVER** alter underlying `ExperimentResult` database records.
4. **Collection-Scoped Novelty Framing**: Avoids absolute terms like *"Proves"*, *"Guaranteed"*, *"Globally novel"*. Enforces cautious phrasing (*"Within the indexed collection..."*, *"Based on the available evidence..."*).

---

## ⚙️ Getting Started

### Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # On Windows
pip install -r requirements.txt
python -m pytest              # Run test suite
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev                   # Start development server
npm run build                 # Compile production build
```

---

## 📜 License
Developed as part of the Advanced IntelliResearch Project Engine. All rights reserved.
