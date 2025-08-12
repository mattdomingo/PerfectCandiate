"use client";
import { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import InlineDiffPanel from "../../components/InlineDiffPanel";
import { JsonPatchOp, Rewrite } from "../../types/jsonPatch";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type CoverageRow = { requirement: string; best_bullet: string; score: number; };

export default function AppPage() {
  const [resumeId, setResumeId] = useState<string>("");
  const [s3key, setS3key] = useState<string>("");
  const [jsonResume, setJsonResume] = useState<any>(null);
  const [rawText, setRawText] = useState<string>("");

  const [jobUrl, setJobUrl] = useState<string>("");
  const [jobPaste, setJobPaste] = useState<string>("");
  const [jobId, setJobId] = useState<string>("");

  const [coverage, setCoverage] = useState<CoverageRow[]>([]);
  const [originalText, setOriginalText] = useState<string>("");
  const [suggestedText, setSuggestedText] = useState<string>("");
  const [rewrites, setRewrites] = useState<Rewrite[]>([]);

  const [busy, setBusy] = useState<boolean>(false);
  const [notice, setNotice] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  function toast(type: "success" | "error" | "info", message: string) {
    setNotice({ type, message });
    window.clearTimeout((toast as any)._t);
    (toast as any)._t = window.setTimeout(() => setNotice(null), 3200);
  }

  const [pendingPatch, setPendingPatch] = useState<JsonPatchOp[]>([]);

  async function startUpload() {
    const file = (document.getElementById("file") as HTMLInputElement).files?.[0];
    if (!file) return toast("info", "Choose a PDF first");
    if (file.type !== "application/pdf") return toast("error", "File must be a PDF");
    setBusy(true);
    try {
      const init = await fetch(`${API}/upload-resume`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ content_type: "application/pdf" })
      }).then(r=>r.json());
      setResumeId(init.resume_id); setS3key(init.s3_key);
      await fetch(init.put_url, { method: "PUT", headers: {"Content-Type":"application/pdf"}, body: file });
      toast("success", "Uploaded. Now click Extract.");
    } finally { setBusy(false); }
  }

  async function extract() {
    if (!s3key || !resumeId) return toast("info", "Upload first");
    setBusy(true);
    try {
      const r = await fetch(`${API}/extract`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ resume_id: resumeId, s3_key: s3key })
      }).then(r=>r.json());
      setJsonResume(r.json_resume); setRawText(r.raw_text);
      setPendingPatch([]);
    } finally { setBusy(false); }
  }

  async function ingestJob() {
    if (!jobUrl && !jobPaste.trim()) return toast("info", "Enter a job URL or paste text");
    setBusy(true);
    try {
      const r = await fetch(`${API}/job/ingest`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ url: jobUrl || null, pasted: jobPaste || null })
      }).then(r=>r.json());
      setJobId(r.job_id);
    } finally { setBusy(false); }
  }

  async function compare() {
    if (!resumeId || !jobId) return toast("info", "Extract resume and ingest job first");
    setBusy(true);
    try {
      const r = await fetch(`${API}/compare`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ resume_id: resumeId, job_id: jobId })
      }).then(r=>r.json());
      setCoverage(r.coverage || []);
      setOriginalText(r.original_text || "");
      setSuggestedText(r.suggested_text || "");
      setRewrites(r.rewrites || []);
      setPendingPatch([]);
    } finally { setBusy(false); }
  }

  async function saveChanges() {
    if (!resumeId || pendingPatch.length === 0) return;
    setBusy(true);
    try {
      const body = { resume_id: resumeId, patch: pendingPatch, job_id: jobId || null };
      const r = await fetch(`${API}/resume/apply-patch`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(body)
      }).then(r=>r.json());
      setJsonResume(r.json_resume);
      setPendingPatch([]);
      if (r.compare) {
        setCoverage(r.compare.coverage || []);
        setOriginalText(r.compare.original_text || "");
        setSuggestedText(r.compare.suggested_text || "");
        setRewrites(r.compare.rewrites || []);
      } else if (jobId) {
        await compare();
      }
      toast("success", "Changes saved");
    } catch (e:any) {
      toast("error", `Save failed: ${e.message || e.toString()}`);
    } finally {
      setBusy(false);
    }
  }

  async function download(fmt: "pdf"|"docx") {
    if (!resumeId) return toast("info", "No resume loaded");
    const r = await fetch(`${API}/render`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ resume_id: resumeId, fmt })
    }).then(r=>r.json());
    if (!r.download_url) { toast("error", "Download failed"); return; }
    const a = document.createElement("a");
    a.href = r.download_url;
    a.download = r.filename || "";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  let step2State: string = "";
  if (jobId) step2State = "done";
  else if (resumeId) step2State = "active";

  const hasResults = (coverage.length > 0) || (rewrites.length > 0);
  let step3State: string = "";
  if (hasResults) step3State = "done";
  else if (jobId) step3State = "active";

  return (
    <main className="container" aria-busy={busy}>
      {busy && <div className="progress" />}
      <header className="app-header">
        <div className="brand">
          <div className="logo" aria-hidden />
          <div>
            <div className="title">Perfect Candidate</div>
            <div className="subtitle">Resume Rewriter</div>
          </div>
        </div>
        <nav className="actions">
          {jsonResume && (
            <div className="export">
              <button className="btn" onClick={()=>download("pdf")}>
                Export PDF
              </button>
              <button className="btn" onClick={()=>download("docx")}>
                Export DOCX
              </button>
            </div>
          )}
        </nav>
      </header>

      <ol className="stepper">
        <li className={`step ${resumeId ? "done" : "active"}`}>
          <div className="step-header">
            <div className="step-index">1</div>
            <div>
              <div className="step-title">Upload and extract your resume</div>
              <div className="step-help">Upload a PDF, then extract structured data</div>
            </div>
          </div>
          <div className="card">
            <div className="row gap">
              <input id="file" type="file" accept="application/pdf" className="input-file" />
              <button onClick={startUpload} disabled={busy} className="btn">Upload PDF</button>
              <button onClick={extract} disabled={busy || !s3key} className="btn btn-primary">Extract</button>
            </div>
            {jsonResume && (
              <details className="details">
                <summary>Show parsed JSON and raw text</summary>
                <pre className="pre">{JSON.stringify(jsonResume, null, 2)}</pre>
                <pre className="pre" style={{maxHeight:220}}>{rawText}</pre>
              </details>
            )}
          </div>
        </li>

        <li className={`step ${step2State}`}>
          <div className="step-header">
            <div className="step-index">2</div>
            <div>
              <div className="step-title">Add the job description</div>
              <div className="step-help">Paste a URL or the full text</div>
            </div>
          </div>
          <div className="card">
            <div className="row gap">
              <input
                type="url"
                placeholder="Job URL (optional)"
                value={jobUrl}
                onChange={e=>setJobUrl(e.target.value)}
                className="input"
              />
              <button onClick={ingestJob} disabled={busy || (!jobUrl && !jobPaste.trim())} className="btn btn-primary">Use URL / Text</button>
            </div>
            <textarea
              placeholder="...or paste the job description here"
              value={jobPaste}
              onChange={e=>setJobPaste(e.target.value)}
              className="textarea"
            />
          </div>
        </li>

        <li className={`step ${step3State}`}>
          <div className="step-header">
            <div className="step-index">3</div>
            <div>
              <div className="step-title">Compare and apply improvements</div>
              <div className="step-help">See coverage and accept suggested rewrites</div>
            </div>
            <div className="ml-auto">
              <button onClick={compare} disabled={busy || !resumeId || !jobId} className="btn">Compare</button>
            </div>
          </div>
          <div className="card">
            {!!coverage.length && (
              <div>
                <div className="section-title">Top Matches</div>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Requirement</th>
                        <th>Closest Resume Bullet</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {coverage.slice(0,12).map((c) => (
                        <tr key={`${c.requirement}-${c.score.toFixed(2)}`}>
                          <td>{c.requirement}</td>
                          <td>{c.best_bullet}</td>
                          <td>{c.score.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {jsonResume && rewrites && rewrites.length > 0 && (
              <InlineDiffPanel
                resumeJson={jsonResume}
                rewrites={rewrites}
                pendingPatch={pendingPatch}
                onUpdatePatch={setPendingPatch}
              />
            )}

            {(originalText || suggestedText) && (
              <details className="details">
                <summary>Full inline Monaco diff</summary>
                <div className="mt-8">
                  <DiffEditor
                    original={originalText || ""}
                    modified={suggestedText || ""}
                    language="markdown"
                    theme="vs-dark"
                    options={{ renderSideBySide: false, readOnly: true, minimap: { enabled: false } }}
                    height="400px"
                  />
                </div>
              </details>
            )}

            {pendingPatch.length > 0 && (
              <div className="save-bar">
                <div>{pendingPatch.length} change(s) ready</div>
                <button onClick={saveChanges} disabled={busy || !resumeId} className="btn btn-success">Save changes</button>
              </div>
            )}
          </div>
        </li>
      </ol>
      {notice && (
        <output className={`toast ${notice.type}`} aria-live="polite">{notice.message}</output>
      )}
    </main>
  );
}


