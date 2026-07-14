# IntelliResearch

**IntelliResearch** is a production-quality Full-Stack AI application designed for AI-Based Research Gap Discovery and Research Recommendation.

This repository contains **Milestone 1**: The foundational framework that handles multi-document uploads, PyMuPDF text/metadata parsing (extracting titles and abstracts using layout heuristics), structured disk and SQL database storage, and a responsive glassmorphic dashboard interface.

---

## Technical Stack

* **Frontend**: React.js (Vite), Tailwind CSS v4 (native compiler), React Router, Axios
* **Backend**: Python 3.13, FastAPI, SQLAlchemy ORM, Pydantic v2, PyMuPDF (fitz), Uvicorn
* **Database**: PostgreSQL (Primary) / SQLite (Development Fallback)

---

## Directory Structure

```
IntelliResearch/
├── backend/
│   ├── app/
│   │   ├── api/            # Route controllers (upload, paper CRUD)
│   │   ├── config/         # Pydantic env config loader
│   │   ├── database/       # Engine connection & session generators
│   │   ├── models/         # SQLAlchemy paper schema
│   │   ├── schemas/        # Pydantic input/output schemas
│   │   ├── services/       # fitz PDF parsing & heuristic processors
│   │   ├── uploads/        # Local disk storage directories
│   │   │   ├── original_papers/ # Uploaded raw PDF copies
│   │   │   ├── extracted_text/  # Extracted text outputs (.txt)
│   │   │   └── embeddings/      # (Placeholder for Milestone 2)
│   │   ├── utils/          # System logging & utilities
│   │   └── main.py         # App routers & CORS configurations
│   ├── .env                # App environmental secrets
│   ├── requirements.txt    # Python library requirements
│   └── run.py              # Backend entry runner
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/     # Header, DragDropUpload, PaperCard, ViewerModal, SearchBar
│   │   ├── pages/          # Home, Dashboard
│   │   ├── services/       # Axios API client handlers
│   │   ├── App.jsx         # Routes definition
│   │   ├── index.css       # Tailwind CSS directives & theme config
│   │   └── main.jsx
│   ├── index.html          # Web entry and SEO meta tags
│   ├── vite.config.js      # Vite compilation configurations
│   └── package.json        # Frontend scripts & dependencies
└── README.md               # User guide documentation
```

---

## Running the Application

### 1. Backend Service Setup

To run the backend, open your terminal (PowerShell or Command Prompt) and run:

```powershell
# Navigate to the backend directory
cd "IntelliResearch/backend"

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Run the backend server
python run.py
```

* The backend service will start on **`http://127.0.0.1:8000`**.
* Open **`http://127.0.0.1:8000/docs`** in your browser to view the interactive FastAPI Swagger UI.

#### Database Configurations (`.env`)
By default, the backend has been configured to use **SQLite** (`DATABASE_URL=sqlite:///./intelliresearch.db`) for immediate local runnability.
To switch to **PostgreSQL**:
1. Open `backend/.env`.
2. Comment out the SQLite URL and uncomment the PostgreSQL URL:
   ```ini
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/intelliresearch
   ```
3. Make sure your PostgreSQL server is active, and the database `intelliresearch` is created. Tables are automatically generated on application startup.

---

### 2. Frontend Dashboard Setup

Open a new terminal window and run:

```bash
# Navigate to the frontend directory
cd "IntelliResearch/frontend"

# Start the Vite development server
npm run dev
```

* Vite will spin up the interface. If port `5173` is occupied, it will automatically select **`http://localhost:5174`**.
* Open the local URL in your browser to interact with the application.

---

## Verifying the Flow (Self-Testing)

We have created an automated verification script that compiles a test PDF, uploads it, validates text extraction fields (asserting abstract extraction and title parsing heuristics), checks file storage on disk, and runs deletion cleanups.

To run it:
```powershell
# In the backend directory with active virtual environment:
python "../.agents/scratch/verify_backend.py"
```
*(Wait, if running from the workspace, the scratch script path is located at `<AppData>/.gemini/antigravity-ide/brain/.../scratch/verify_backend.py`).*

Alternatively, you can test it manually:
1. Load **`http://localhost:5174`** in your browser.
2. Drag and drop any PDF paper (under 50 MB) into the drop zone.
3. Click **Upload to Database**. Once successful, a checkmark and the parsed title appear in the file list.
4. Go to **Dashboard** in the header to search, delete, or view full text with the built-in search matching inside the modal window.
