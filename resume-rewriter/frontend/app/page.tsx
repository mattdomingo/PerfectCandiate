"use client";
import { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import InlineDiffPanel from "../components/InlineDiffPanel";
import { JsonPatchOp, Rewrite } from "../types/jsonPatch";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type CoverageRow = { requirement: string; best_bullet: string; score: number; };

export default function Home() {
  // Saturday/Sunday AM state
  const [resumeId, setResumeId] = useState<string>("");
  const [s3key, setS3key] = useState<string>("");
  const [jsonResume, setJsonResume] = useState<any>(null);
  const [rawText, setRawText] = useState<string>("");

  const [jobUrl, setJobUrl] = useState<string>("");
  const [jobPaste, setJobPaste] = useState<string>("");
  const [jobId, setJobId] = useState<string>("");
  const [requirements, setRequirements] = useState<string[]>([]);

  const [coverage, setCoverage] = useState<CoverageRow[]>([]);
  const [originalText, setOriginalText] = useState<string>("");
  const [suggestedText, setSuggestedText] = useState<string>("");
  const [rewrites, setRewrites] = useState<Rewrite[]>([]);

  const [busy, setBusy] = useState<boolean>(false);

  // NEW: client-side JSON Patch for Saturday AM (preview only)
  const [pendingPatch, setPendingPatch] = useState<JsonPatchOp[]>([]);

  async function startUpload() {
    const file = (document.getElementById("file") as HTMLInputElement).files?.[0];
    if (!file) return alert("Choose a PDF first");
    if (file.type !== "application/pdf") return alert("File must be a PDF");
    setBusy(true);
    try {
      const init = await fetch(`${API}/upload-resume`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ content_type: "application/pdf" })
      }).then(r=>r.json());
      setResumeId(init.resume_id); setS3key(init.s3_key);
      await fetch(init.put_url, { method: "PUT", headers: {"Content-Type":"application/pdf"}, body: file });
      alert("Uploaded. Now click Extract.");
    } finally { setBusy(false); }
  }

  async function extract() {
    if (!s3key || !resumeId) return alert("Upload first");
    setBusy(true);
    try {
      const r = await fetch(`${API}/extract`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ resume_id: resumeId, s3_key: s3key })
      }).then(r=>r.json());
      setJsonResume(r.json_resume); setRawText(r.raw_text);
      setPendingPatch([]); // reset any client patch
    } finally { setBusy(false); }
  }

  async function ingestJob() {
    if (!jobUrl && !jobPaste.trim()) return alert("Enter a job URL or paste text");
    setBusy(true);
    try {
      const r = await fetch(`${API}/job/ingest`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ url: jobUrl || null, pasted: jobPaste || null })
      }).then(r=>r.json());
      setJobId(r.job_id); setRequirements(r.requirements || []);
    } finally { setBusy(false); }
  }

  async function compare() {
    if (!resumeId || !jobId) return alert("Extract resume and ingest job first");
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
      // reset local patch any time we re-compare
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
      // update local resume with server truth
      setJsonResume(r.json_resume);
      setPendingPatch([]);
      // if compare results came back, refresh UI
      if (r.compare) {
        setCoverage(r.compare.coverage || []);
        setOriginalText(r.compare.original_text || "");
        setSuggestedText(r.compare.suggested_text || "");
        setRewrites(r.compare.rewrites || []);
      } else if (jobId) {
        // fallback: re-run compare to refresh suggested text
        await compare();
      }
      alert("Changes saved.");
    } catch (e:any) {
      alert(`Save failed: ${e.message || e.toString()}`);
    } finally {
      setBusy(false);
    }
  }

  async function download(fmt: "pdf"|"docx") {
    if (!resumeId) return alert("No resume loaded");
    const r = await fetch(`${API}/render`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ resume_id: resumeId, fmt })
    }).then(r=>r.json());
    if (!r.download_url) { alert("Download failed"); return; }
    const a = document.createElement("a");
    a.href = r.download_url;
    a.download = r.filename || ""; // server sets Content-Disposition too
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  return (
    <main style={{padding:24, maxWidth:1100, margin:"0 auto"}}>
      <h1 style={{fontSize:24, fontWeight:700}}>Resume Rewriter — Weekend 2 · Saturday AM</h1>

      {/* 1) Upload & Extract */}
      <section style={{marginTop:16}}>
        <h2 style={{fontWeight:600}}>1) Resume</h2>
        <div style={{display:"flex", gap:12, alignItems:"center"}}>
          <input id="file" type="file" accept="application/pdf" />
          <button onClick={startUpload} disabled={busy} style={btn}>Upload PDF</button>
          <button onClick={extract} disabled={busy || !s3key} style={btn}>Extract</button>
        </div>
        {jsonResume && (
          <details style={{marginTop:8}}>
            <summary>Show parsed JSON + raw text preview</summary>
            <pre style={pre}>{JSON.stringify(jsonResume, null, 2)}</pre>
            <pre style={{...pre, maxHeight:220}}>{rawText}</pre>
          </details>
        )}
      </section>

      {/* 2) Job ingest */}
      <section style={{marginTop:24}}>
        <h2 style={{fontWeight:600}}>2) Job posting</h2>
        <div style={{display:"flex", gap:12}}>
          <input
            type="url" placeholder="Job URL (optional)"
            value={jobUrl} onChange={e=>setJobUrl(e.target.value)}
            style={{flex:1, padding:"8px 10px", border:"1px solid #ccc", borderRadius:8}}
          />
          <button onClick={ingestJob} disabled={busy} style={btn}>Fetch / Use Text</button>
        </div>
        <textarea
          placeholder="...or paste the job description here"
          value={jobPaste} onChange={e=>setJobPaste(e.target.value)}
          style={{marginTop:8, width:"100%", height:120, padding:12, border:"1px solid #ccc", borderRadius:8}}
        />
      </section>

      {/* 3) Compare */}
      <section style={{marginTop:24}}>
        <h2 style={{fontWeight:600}}>3) Coverage & Diff</h2>
        <button onClick={compare} disabled={busy || !resumeId || !jobId} style={btn}>Compare</button>

        {/* coverage table */}
        {!!coverage.length && (
          <div style={{marginTop:12}}>
            <h3 style={{fontWeight:600}}>Top Matches (score 0..1)</h3>
            <div style={{overflowX:"auto"}}>
              <table style={{borderCollapse:"collapse", width:"100%"}}>
                <thead>
                  <tr>
                    <th style={th}>Requirement</th>
                    <th style={th}>Closest Resume Bullet</th>
                    <th style={th}>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {coverage.slice(0,12).map((c, i) => (
                    <tr key={i}>
                      <td style={td}>{c.requirement}</td>
                      <td style={td}>{c.best_bullet}</td>
                      <td style={td}>{c.score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* NEW: pretty, section-aware inline diff with Accept/Reject */}
        {jsonResume && rewrites && rewrites.length > 0 && (
          <InlineDiffPanel
            resumeJson={jsonResume}
            rewrites={rewrites}
            pendingPatch={pendingPatch}
            onUpdatePatch={setPendingPatch}
          />
        )}

        {/* optional: show full inline Monaco diff (collapsed by default) */}
        {(originalText || suggestedText) && (
          <details style={{marginTop:16}}>
            <summary>Full inline Monaco diff</summary>
            <div style={{marginTop:8}}>
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

        {/* Save changes */}
        {pendingPatch.length > 0 && (
          <div style={{marginTop:12, display:"flex", gap:8}}>
            <button
              onClick={saveChanges}
              disabled={busy || !resumeId}
              style={{padding:"8px 12px", border:"1px solid #16a34a", borderRadius:8, background:"#16a34a", color:"white"}}
            >
              Save changes
            </button>
            <span style={{fontSize:12, color:"#6b7280"}}>{pendingPatch.length} change(s) ready</span>
          </div>
        )}
      </section>

      {/* Debug helper */}
      {pendingPatch.length > 0 && (
        <div style={{marginTop:16, color:"#16a34a"}}>Ready to save: {pendingPatch.length} changes</div>
      )}

      {/* 4) Download */}
      {jsonResume && (
        <section style={{marginTop:24}}>
          <h2 style={{fontWeight:600}}>4) Export</h2>
          <div style={{display:"flex", gap:12}}>
            <button onClick={()=>download("pdf")}  style={btn}>Download PDF</button>
            <button onClick={()=>download("docx")} style={btn}>Download DOCX</button>
          </div>
          <p style={{fontSize:12, color:"#6b7280", marginTop:6}}>
            Downloads reflect your latest accepted changes.
          </p>
        </section>
      )}
    </main>
  );
}

const btn: React.CSSProperties = { padding:"8px 12px", border:"1px solid #222", borderRadius:8, background:"white" };
const pre: React.CSSProperties = { background:"#f6f6f6", padding:12, borderRadius:8, overflow:"auto" };
const th: React.CSSProperties = { textAlign:"left", borderBottom:"1px solid #ddd", padding:"6px 8px", fontWeight:600 };
const td: React.CSSProperties = { borderBottom:"1px solid #eee", padding:"6px 8px", verticalAlign:"top" };



