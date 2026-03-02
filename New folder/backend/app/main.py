from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auditor import run_audit
from .models import AuditConfig, AuditRequest


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
SAMPLE_DIR = ROOT_DIR / "sample_project"


app = FastAPI(title="AI Code Documentation Auditor", version="1.0.0")


@app.get("/api/sample-default")
def sample_default() -> dict:
    return {"sample_root_path": str(SAMPLE_DIR)}


@app.post("/api/audit")
def audit(req: AuditRequest) -> dict:
    root = Path(req.root_path).expanduser()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid root_path directory: {req.root_path}")

    cfg = AuditConfig(root_path=str(root.resolve()))
    if req.similarity_threshold is not None:
        cfg.similarity_threshold = float(req.similarity_threshold)
    if req.top_k is not None:
        cfg.top_k = int(req.top_k)

    try:
        result = run_audit(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {e}") from e

    return result.model_dump()


@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Frontend not found")
    return FileResponse(index_path)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

