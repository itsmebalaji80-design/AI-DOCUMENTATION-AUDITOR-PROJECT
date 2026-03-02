## AI Code Documentation Auditor (RAG + Coverage Analysis)

Detect missing documentation for API methods by mapping **code chunks** (API endpoints) to **documentation topics** (Markdown sections) using embeddings and similarity coverage checks. Includes a local website with a gap report and citations.

### What you get (matches R1–R5)

- **R1 Code chunk embedding**: Extract API methods/endpoints from code, chunk them, embed them.
- **R2 Coverage check**: Compare each API chunk to all doc sections via cosine similarity; mark covered/uncovered.
- **R3 Missing topic detection**:
  - API endpoints missing documentation (low similarity to any doc section).
  - Documentation sections with no matching API endpoint (potentially stale).
- **R4 Citation output**: Every match/gap includes code and doc citations (file + line range + excerpt).
- **R5 Gap report**: Web UI shows summary + tables + exportable JSON gap report.

---

### Quick start (Windows PowerShell)

Install Python (3.10+) first if you don’t have it:

- Download from [python.org](https://www.python.org/downloads/)
- During install, check **“Add Python to PATH”**

Create a virtualenv and install dependencies:

```powershell
cd "C:\Users\BALAJI\Desktop\New folder"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
```

Run the server:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open the website:

- `http://127.0.0.1:8000`

---

### Using the website

You can audit:

- **Sample project** (works immediately)
- **Any local folder path** on your machine (the server reads the files locally)

Recommended structure (not required):

- Code: anything under your folder (Python/JS/TS/Java supported heuristically)
- Docs: Markdown files anywhere in the folder (or in `docs/`)

---

### Notes

- Embeddings use **TF‑IDF** (fast, local, no API keys).
- The audit is **local-only**: the server reads your selected folder from disk.

