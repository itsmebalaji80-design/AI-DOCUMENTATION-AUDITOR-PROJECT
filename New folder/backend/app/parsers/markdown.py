from __future__ import annotations

import re

from ..models import DocSection


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def split_markdown_sections(rel_path: str, text: str) -> list[DocSection]:
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []

    for i, line in enumerate(lines, start=1):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        heading = m.group(2).strip()
        headings.append((i, level, heading))

    if not headings:
        # Single synthetic section when there are no headings.
        content = text.strip()
        if not content:
            return []
        return [
            DocSection(
                doc_id=f"{rel_path}::document",
                file=rel_path,
                heading="(document)",
                level=1,
                start_line=1,
                end_line=max(1, len(lines)),
                text=content,
            )
        ]

    sections: list[DocSection] = []
    for idx, (start_line, level, heading) in enumerate(headings):
        end_line = len(lines)
        for j in range(idx + 1, len(headings)):
            next_start, next_level, _ = headings[j]
            if next_level <= level:
                end_line = next_start - 1
                break

        # Include heading line + its content
        slice_lines = lines[start_line - 1 : end_line]
        section_text = "\n".join(slice_lines).strip()
        if not section_text:
            continue

        doc_id = f"{rel_path}::{heading}::{start_line}"
        sections.append(
            DocSection(
                doc_id=doc_id,
                file=rel_path,
                heading=heading,
                level=level,
                start_line=start_line,
                end_line=end_line,
                text=section_text,
            )
        )

    return sections

