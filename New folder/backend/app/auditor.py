from __future__ import annotations

from pathlib import Path

import numpy as np

from .embeddings import EmbeddingModel, cosine_sim_matrix
from .models import ApiChunk, AuditConfig, AuditResult, AuditSummary, ChunkMatch, DocSection
from .parsers.api import extract_api_chunks
from .parsers.fs import read_text_files
from .parsers.markdown import split_markdown_sections


def _excerpt(text: str, max_chars: int = 400) -> str:
    t = " ".join(text.strip().split())
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1] + "…"


def run_audit(config: AuditConfig) -> AuditResult:
    root = Path(config.root_path).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Path is not a directory: {config.root_path}")

    code_files = read_text_files(
        root=root,
        include_globs=config.include_globs,
        exclude_globs=config.exclude_globs,
        extensions=config.code_extensions,
    )
    doc_files = read_text_files(
        root=root,
        include_globs=config.include_globs,
        exclude_globs=config.exclude_globs,
        extensions=config.doc_extensions,
    )

    api_chunks: list[ApiChunk] = []
    for f in code_files:
        api_chunks.extend(extract_api_chunks(f.rel_path, f.path.suffix, f.text))

    doc_sections: list[DocSection] = []
    for f in doc_files:
        doc_sections.extend(split_markdown_sections(f.rel_path, f.text))

    if not api_chunks and not doc_sections:
        summary = AuditSummary(
            api_chunks_total=0,
            doc_sections_total=0,
            covered_chunks=0,
            uncovered_chunks=0,
            stale_doc_sections=0,
        )
        return AuditResult(
            config=config,
            summary=summary,
            api_chunks=[],
            doc_sections=[],
            matches=[],
            missing_docs=[],
            stale_docs=[],
        )

    # Build TF-IDF embeddings in a shared space by fitting on combined corpus.
    embedder = EmbeddingModel()
    doc_texts = [f"{d.heading}\n{d.text}" for d in doc_sections]
    chunk_texts = [
        "\n".join(
            [
                c.text,
                f"file: {c.file}",
                f"symbol: {c.symbol}" if c.symbol else "",
                f"route: {c.route}" if c.route else "",
                f"method: {c.http_method}" if c.http_method else "",
            ]
        ).strip()
        for c in api_chunks
    ]
    corpus = doc_texts + chunk_texts
    X = embedder.fit_transform(corpus)
    D = X[: len(doc_texts)]
    C = X[len(doc_texts) :]

    sims = cosine_sim_matrix(C, D) if (len(api_chunks) and len(doc_sections)) else np.zeros((len(api_chunks), len(doc_sections)), dtype=np.float32)

    matches: list[ChunkMatch] = []
    missing_docs: list[dict] = []

    for i, chunk in enumerate(api_chunks):
        if len(doc_sections) == 0:
            best_doc = None
            best_score = 0.0
            top = []
        else:
            row = sims[i]
            best_idx = int(np.argmax(row))
            best_score = float(row[best_idx])
            best_doc = doc_sections[best_idx].doc_id

            top_indices = np.argsort(-row)[: max(1, config.top_k)]
            top = []
            for di in top_indices:
                d = doc_sections[int(di)]
                top.append(
                    {
                        "doc_id": d.doc_id,
                        "score": float(row[int(di)]),
                        "citation": {
                            "file": d.file,
                            "start_line": d.start_line,
                            "end_line": d.end_line,
                            "excerpt": _excerpt(d.text),
                        },
                        "heading": d.heading,
                    }
                )

        matches.append(
            ChunkMatch(
                chunk_id=chunk.chunk_id,
                best_doc_id=best_doc,
                best_score=best_score,
                top_k=top,
            )
        )

        if best_score < config.similarity_threshold:
            missing_docs.append(
                {
                    "chunk": chunk.model_dump(),
                    "reason": "No documentation section exceeded similarity threshold",
                    "best_match": top[0] if top else None,
                    "threshold": config.similarity_threshold,
                    "citation": {
                        "file": chunk.file,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "excerpt": _excerpt(chunk.text),
                    },
                }
            )

    # Stale docs: doc sections that don't match any chunk above threshold.
    stale_docs: list[dict] = []
    if len(doc_sections) and len(api_chunks):
        col_max = sims.max(axis=0) if sims.size else np.zeros((len(doc_sections),), dtype=np.float32)
        for j, doc in enumerate(doc_sections):
            best = float(col_max[j])
            if best < config.similarity_threshold:
                stale_docs.append(
                    {
                        "doc": doc.model_dump(),
                        "reason": "No API chunk exceeded similarity threshold for this doc topic",
                        "best_score": best,
                        "threshold": config.similarity_threshold,
                        "citation": {
                            "file": doc.file,
                            "start_line": doc.start_line,
                            "end_line": doc.end_line,
                            "excerpt": _excerpt(doc.text),
                        },
                    }
                )
    elif len(doc_sections) and not len(api_chunks):
        for doc in doc_sections:
            stale_docs.append(
                {
                    "doc": doc.model_dump(),
                    "reason": "No API chunks were found in the codebase",
                    "best_score": 0.0,
                    "threshold": config.similarity_threshold,
                    "citation": {
                        "file": doc.file,
                        "start_line": doc.start_line,
                        "end_line": doc.end_line,
                        "excerpt": _excerpt(doc.text),
                    },
                }
            )

    covered_chunks = len(api_chunks) - len(missing_docs)
    summary = AuditSummary(
        api_chunks_total=len(api_chunks),
        doc_sections_total=len(doc_sections),
        covered_chunks=covered_chunks,
        uncovered_chunks=len(missing_docs),
        stale_doc_sections=len(stale_docs),
    )

    return AuditResult(
        config=config,
        summary=summary,
        api_chunks=api_chunks,
        doc_sections=doc_sections,
        matches=matches,
        missing_docs=missing_docs,
        stale_docs=stale_docs,
    )

