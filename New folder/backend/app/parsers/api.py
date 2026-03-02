from __future__ import annotations

import re

from ..models import ApiChunk


_PY_DECORATOR_RE = re.compile(
    r"^\s*@(?P<obj>app|router)\.(?P<method>get|post|put|delete|patch|options|head)\(\s*['\"](?P<route>[^'\"]+)['\"]",
    re.IGNORECASE,
)
_PY_DEF_RE = re.compile(r"^\s*(async\s+def|def)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")


_JS_EXPRESS_RE = re.compile(
    r"(?P<prefix>\bapp|\brouter)\.(?P<method>get|post|put|delete|patch|options|head)\(\s*([`'\"])(?P<route>.+?)\3",
    re.IGNORECASE,
)


_JAVA_MAPPING_RE = re.compile(
    r"^\s*@(?P<ann>GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\((?P<args>.*)\)\s*$"
)


def _python_chunks(rel_path: str, text: str) -> list[ApiChunk]:
    lines = text.splitlines()
    out: list[ApiChunk] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        m = _PY_DECORATOR_RE.match(line)
        if not m:
            i += 1
            continue

        start_line = i + 1
        http_method = m.group("method").lower()
        route = m.group("route").strip()

        # Find the following def line
        j = i + 1
        while j < len(lines) and (lines[j].strip() == "" or lines[j].lstrip().startswith("@")):
            j += 1
        symbol = ""
        def_indent = None
        if j < len(lines):
            md = _PY_DEF_RE.match(lines[j])
            if md:
                symbol = md.group("name")
                def_indent = len(lines[j]) - len(lines[j].lstrip(" "))
                j += 1

        # Walk until indentation drops back
        end_idx = j
        if def_indent is not None:
            k = j
            while k < len(lines):
                l = lines[k]
                if l.strip() == "":
                    k += 1
                    continue
                cur_indent = len(l) - len(l.lstrip(" "))
                if cur_indent <= def_indent and not l.lstrip().startswith((")", "]", "}")):
                    break
                k += 1
            end_idx = k
        else:
            end_idx = min(len(lines), i + 25)

        end_line = max(start_line, end_idx)
        chunk_lines = lines[start_line - 1 : end_line]
        chunk_text = "\n".join(chunk_lines).strip()

        chunk_id = f"{rel_path}::py::{start_line}"
        out.append(
            ApiChunk(
                chunk_id=chunk_id,
                file=rel_path,
                language="python",
                start_line=start_line,
                end_line=end_line,
                symbol=symbol,
                http_method=http_method,
                route=route,
                text=f"HTTP {http_method.upper()} {route}\n{chunk_text}",
            )
        )

        i = end_line

    return out


def _paren_balanced_chunk(lines: list[str], start_idx: int) -> int:
    # Start at first match line and scan until we close the initial call.
    depth = 0
    started = False
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == "(":
                depth += 1
                started = True
            elif ch == ")":
                depth -= 1
        if started and depth <= 0:
            return i
    return min(len(lines) - 1, start_idx + 60)


def _js_chunks(rel_path: str, text: str) -> list[ApiChunk]:
    lines = text.splitlines()
    out: list[ApiChunk] = []

    for i, line in enumerate(lines):
        m = _JS_EXPRESS_RE.search(line)
        if not m:
            continue
        start_line = i + 1
        http_method = m.group("method").lower()
        route = m.group("route").strip()

        end_idx = _paren_balanced_chunk(lines, i)
        end_line = end_idx + 1
        chunk_text = "\n".join(lines[i : end_idx + 1]).strip()

        chunk_id = f"{rel_path}::js::{start_line}"
        out.append(
            ApiChunk(
                chunk_id=chunk_id,
                file=rel_path,
                language="javascript",
                start_line=start_line,
                end_line=end_line,
                symbol="",
                http_method=http_method,
                route=route,
                text=f"HTTP {http_method.upper()} {route}\n{chunk_text}",
            )
        )

    return out


def _brace_balanced_chunk(lines: list[str], start_idx: int) -> int:
    depth = 0
    started = False
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
        if started and depth <= 0 and i > start_idx:
            return i
    return min(len(lines) - 1, start_idx + 120)


def _java_chunks(rel_path: str, text: str) -> list[ApiChunk]:
    lines = text.splitlines()
    out: list[ApiChunk] = []

    i = 0
    while i < len(lines):
        m = _JAVA_MAPPING_RE.match(lines[i])
        if not m:
            i += 1
            continue

        start_idx = i
        start_line = i + 1
        ann = m.group("ann")
        http_method = ann.replace("Mapping", "").lower()
        args = m.group("args")

        route = ""
        m_value = re.search(r'value\s*=\s*"([^"]+)"', args)
        if m_value:
            route = m_value.group(1)
        else:
            m_first = re.search(r'"([^"]+)"', args)
            if m_first:
                route = m_first.group(1)

        # Find method signature line
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith("@"):
            j += 1

        end_idx = _brace_balanced_chunk(lines, j) if j < len(lines) else min(len(lines) - 1, i + 80)
        end_line = end_idx + 1
        chunk_text = "\n".join(lines[start_idx : end_idx + 1]).strip()

        chunk_id = f"{rel_path}::java::{start_line}"
        out.append(
            ApiChunk(
                chunk_id=chunk_id,
                file=rel_path,
                language="java",
                start_line=start_line,
                end_line=end_line,
                symbol="",
                http_method=http_method,
                route=route or None,
                text=f"HTTP {http_method.upper()} {route}".strip() + "\n" + chunk_text,
            )
        )

        i = end_line

    return out


def extract_api_chunks(rel_path: str, ext: str, text: str) -> list[ApiChunk]:
    ext = ext.lower()
    if ext == ".py":
        return _python_chunks(rel_path, text)
    if ext in {".js", ".ts", ".tsx"}:
        return _js_chunks(rel_path, text)
    if ext == ".java":
        return _java_chunks(rel_path, text)
    return []

