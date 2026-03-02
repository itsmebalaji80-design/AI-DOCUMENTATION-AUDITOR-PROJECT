from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int
    excerpt: str


class DocSection(BaseModel):
    doc_id: str
    file: str
    heading: str
    level: int
    start_line: int
    end_line: int
    text: str


class ApiChunk(BaseModel):
    chunk_id: str
    file: str
    language: str
    start_line: int
    end_line: int
    symbol: str = ""
    http_method: str | None = None
    route: str | None = None
    text: str


class ChunkMatch(BaseModel):
    chunk_id: str
    best_doc_id: str | None
    best_score: float
    top_k: list[dict] = Field(default_factory=list)


class AuditConfig(BaseModel):
    root_path: str
    include_globs: list[str] = Field(default_factory=lambda: ["**/*"])
    exclude_globs: list[str] = Field(
        default_factory=lambda: [
            "**/.venv/**",
            "**/venv/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
        ]
    )
    code_extensions: list[str] = Field(default_factory=lambda: [".py", ".js", ".ts", ".tsx", ".java"])
    doc_extensions: list[str] = Field(default_factory=lambda: [".md", ".mdx"])
    similarity_threshold: float = 0.45
    top_k: int = 3


class AuditRequest(BaseModel):
    root_path: str
    similarity_threshold: float | None = None
    top_k: int | None = None


class AuditSummary(BaseModel):
    api_chunks_total: int
    doc_sections_total: int
    covered_chunks: int
    uncovered_chunks: int
    stale_doc_sections: int


class AuditResult(BaseModel):
    config: AuditConfig
    summary: AuditSummary
    api_chunks: list[ApiChunk]
    doc_sections: list[DocSection]
    matches: list[ChunkMatch]
    missing_docs: list[dict]
    stale_docs: list[dict]

