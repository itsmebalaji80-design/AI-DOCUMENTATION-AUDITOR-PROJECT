from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True)
class FileRecord:
    path: Path
    rel_path: str
    text: str


def _matches_any_glob(rel_path: str, globs: list[str]) -> bool:
    rel_path = rel_path.replace("\\", "/")
    return any(fnmatch(rel_path, g) for g in globs)


def read_text_files(
    root: Path,
    include_globs: list[str],
    exclude_globs: list[str],
    extensions: list[str],
    max_bytes: int = 2_000_000,
) -> list[FileRecord]:
    root = root.resolve()
    out: list[FileRecord] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {e.lower() for e in extensions}:
            continue

        rel = str(p.relative_to(root)).replace("\\", "/")
        if include_globs and not _matches_any_glob(rel, include_globs):
            continue
        if exclude_globs and _matches_any_glob(rel, exclude_globs):
            continue

        try:
            if p.stat().st_size > max_bytes:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        out.append(FileRecord(path=p, rel_path=rel, text=text))

    return out

