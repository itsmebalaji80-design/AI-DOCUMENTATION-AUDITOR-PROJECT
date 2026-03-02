const els = {
  rootPath: document.getElementById("rootPath"),
  threshold: document.getElementById("threshold"),
  thresholdOut: document.getElementById("thresholdOut"),
  topK: document.getElementById("topK"),
  runBtn: document.getElementById("runBtn"),
  useSampleBtn: document.getElementById("useSampleBtn"),
  exportBtn: document.getElementById("exportBtn"),
  status: document.getElementById("status"),
  sApi: document.getElementById("sApi"),
  sDocs: document.getElementById("sDocs"),
  sCovered: document.getElementById("sCovered"),
  sMissing: document.getElementById("sMissing"),
  sStale: document.getElementById("sStale"),
  missingBody: document.getElementById("missingBody"),
  staleBody: document.getElementById("staleBody"),
};

let lastResult = null;

function setStatus(msg) {
  els.status.textContent = msg || "";
}

function esc(s) {
  return (s ?? "").toString().replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function citationText(c) {
  if (!c) return "—";
  return `${c.file}:${c.start_line}-${c.end_line}`;
}

function downloadJson(obj, filename) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function renderSummary(summary) {
  els.sApi.textContent = summary?.api_chunks_total ?? "0";
  els.sDocs.textContent = summary?.doc_sections_total ?? "0";
  els.sCovered.textContent = summary?.covered_chunks ?? "0";
  els.sMissing.textContent = summary?.uncovered_chunks ?? "0";
  els.sStale.textContent = summary?.stale_doc_sections ?? "0";
}

function renderMissing(missingDocs) {
  els.missingBody.innerHTML = "";
  if (!missingDocs?.length) {
    els.missingBody.innerHTML = `<tr><td colspan="3" class="mono">No missing documentation detected.</td></tr>`;
    return;
  }

  for (const item of missingDocs) {
    const ch = item.chunk;
    const best = item.best_match;
    const route = ch?.route ? `<span class="badge">${esc(ch.http_method?.toUpperCase() || "")}</span><span class="mono">${esc(ch.route)}</span>` : `<span class="mono">${esc(ch.chunk_id)}</span>`;
    const chunkCit = item.citation;
    const bestScore = best ? Number(best.score).toFixed(3) : "0.000";
    const bestLabel = best ? `<div><span class="mono">${esc(best.heading || best.doc_id)}</span></div>` : `<span class="mono">—</span>`;
    const bestCit = best?.citation;

    els.missingBody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td>
          <div>${route}</div>
          <div class="hint mono">${esc(citationText(chunkCit))}</div>
          <div class="hint">${esc(chunkCit?.excerpt || "")}</div>
        </td>
        <td>
          <div>${bestLabel}</div>
          <div class="hint mono">score=${esc(bestScore)}</div>
          <div class="hint mono">${esc(citationText(bestCit))}</div>
          <div class="hint">${esc(bestCit?.excerpt || "")}</div>
        </td>
        <td class="mono">${esc(citationText(chunkCit))}</td>
      </tr>`
    );
  }
}

function renderStale(staleDocs) {
  els.staleBody.innerHTML = "";
  if (!staleDocs?.length) {
    els.staleBody.innerHTML = `<tr><td colspan="3" class="mono">No stale documentation detected.</td></tr>`;
    return;
  }

  for (const item of staleDocs) {
    const d = item.doc;
    const cit = item.citation;
    els.staleBody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td>
          <div class="mono">${esc(d.heading || d.doc_id)}</div>
          <div class="hint mono">${esc(citationText(cit))}</div>
          <div class="hint">${esc(cit?.excerpt || "")}</div>
        </td>
        <td class="mono">${esc(Number(item.best_score ?? 0).toFixed(3))}</td>
        <td class="mono">${esc(citationText(cit))}</td>
      </tr>`
    );
  }
}

async function fetchSamplePath() {
  const r = await fetch("/api/sample-default");
  if (!r.ok) throw new Error(await r.text());
  const j = await r.json();
  return j.sample_root_path;
}

async function runAudit() {
  const rootPath = els.rootPath.value.trim();
  const similarity_threshold = Number(els.threshold.value);
  const top_k = Number(els.topK.value);

  if (!rootPath) {
    setStatus("Root path is required.");
    return;
  }

  els.runBtn.disabled = true;
  els.exportBtn.disabled = true;
  setStatus("Running audit…");

  try {
    const r = await fetch("/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ root_path: rootPath, similarity_threshold, top_k }),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok) {
      throw new Error(j?.detail || "Audit failed");
    }

    lastResult = j;
    renderSummary(j.summary);
    renderMissing(j.missing_docs);
    renderStale(j.stale_docs);
    setStatus(`Done. Missing docs: ${j.summary.uncovered_chunks}, stale topics: ${j.summary.stale_doc_sections}.`);
    els.exportBtn.disabled = false;
  } catch (e) {
    setStatus(String(e?.message || e));
  } finally {
    els.runBtn.disabled = false;
  }
}

els.threshold.addEventListener("input", () => {
  els.thresholdOut.textContent = Number(els.threshold.value).toFixed(2);
});

els.runBtn.addEventListener("click", runAudit);

els.useSampleBtn.addEventListener("click", async () => {
  try {
    setStatus("Loading sample path…");
    const p = await fetchSamplePath();
    els.rootPath.value = p;
    setStatus("Sample path loaded. Click “Run audit”.");
  } catch (e) {
    setStatus(String(e?.message || e));
  }
});

els.exportBtn.addEventListener("click", () => {
  if (!lastResult) return;
  downloadJson(lastResult, "audit-gap-report.json");
});

(async () => {
  els.thresholdOut.textContent = Number(els.threshold.value).toFixed(2);
  try {
    const p = await fetchSamplePath();
    els.rootPath.value = p;
    setStatus("Ready. Sample path auto-filled — click “Run audit”.");
  } catch {
    setStatus("Ready. Enter a root path and click “Run audit”.");
  }
})();

