"use client";
import React, { useMemo, useState } from "react";
import DiffRow from "./DiffRow";
import { buildPatchFromRewrites, applyPatchLocal } from "../utils/patch";
import { JsonPatchOp, Rewrite } from "../types/jsonPatch";

type Props = {
  resumeJson: any;
  rewrites: Rewrite[];
  pendingPatch: JsonPatchOp[];
  onUpdatePatch: (ops: JsonPatchOp[]) => void;
};

export default function InlineDiffPanel({ resumeJson, rewrites, pendingPatch, onUpdatePatch }: Props) {
  // seed default ops from all rewrites (used by Accept All)
  const { patch: fullPatch, mapping } = useMemo(() => buildPatchFromRewrites(rewrites, resumeJson), [rewrites, resumeJson]);

  const acceptedLookup = new Set(pendingPatch.map(p => p.path));
  const [dismissedPaths, setDismissedPaths] = useState<string[]>([]);
  const dismissedLookup = useMemo(() => new Set(dismissedPaths), [dismissedPaths]);

  function acceptOpFor(path: string, value: string) {
    const filtered = pendingPatch.filter(p => p.path !== path);
    onUpdatePatch([...filtered, { op: "replace", path, value }]);
    if (dismissedLookup.has(path)) {
      setDismissedPaths(prev => prev.filter(p => p !== path));
    }
  }

  function rejectOpFor(path: string) {
    onUpdatePatch(pendingPatch.filter(p => p.path !== path));
    if (!dismissedLookup.has(path)) {
      setDismissedPaths(prev => [...prev, path]);
    }
  }

  function acceptAll() {
    onUpdatePatch(fullPatch);
    setDismissedPaths([]);
  }

  function resetAll() {
    onUpdatePatch([]);
    setDismissedPaths([]);
  }

  // Compute a preview resume after current pendingPatch
  const preview = useMemo(() => applyPatchLocal(resumeJson, pendingPatch), [resumeJson, pendingPatch]);

  // Show all suggestions that are neither accepted nor dismissed
  const visible = mapping.filter(m => {
    const path = `/work/${(m as any).workIdx ?? 0}/highlights/${m.idx}`;
    return !acceptedLookup.has(path) && !dismissedLookup.has(path);
  });

  return (
    <section style={{marginTop: 18}}>
      <div style={{display:"flex", alignItems:"center", gap:10, marginBottom: 10}}>
        <h3 style={{fontWeight:700, margin:0}}>Experience — inline suggestions</h3>
        <span style={{fontSize:12, color:"#6b7280"}}>({pendingPatch.length} accepted)</span>
        <div style={{marginLeft:"auto", display:"flex", gap:8}}>
          <button onClick={acceptAll} style={btnPrimary}>Accept all</button>
          <button onClick={resetAll} style={btn}>Reset</button>
        </div>
      </div>

      {rewrites.length === 0 && <div style={{color:"#6b7280"}}>No suggestions available. Run Compare first.</div>}

      {visible.length === 0 && <div style={{color:"#6b7280"}}>All suggestions handled.</div>}
      {visible.map((m) => {
        const path = `/work/${(m as any).workIdx ?? 0}/highlights/${m.idx}`;
        const accepted = acceptedLookup.has(path);
        return (
          <DiffRow
            key={path}
            indexHint={m.idx}
            before={m.before}
            after={m.after}
            accepted={accepted}
            onAccept={() => acceptOpFor(path, m.after)}
            onReject={() => rejectOpFor(path)}
          />
        );
      })}

      <details style={{marginTop:12}}>
        <summary>Preview (first job’s highlights after accepted changes)</summary>
        <pre style={pre}>
{JSON.stringify(preview?.work?.[0]?.highlights ?? [], null, 2)}
        </pre>
      </details>

      <details style={{marginTop:12}}>
        <summary>Pending JSON Patch</summary>
        <pre style={pre}>{JSON.stringify(pendingPatch, null, 2)}</pre>
      </details>
    </section>
  );
}

const btn: React.CSSProperties = { padding:"8px 12px", border:"1px solid #222", borderRadius:8, background:"white" };
const btnPrimary: React.CSSProperties = { padding:"8px 12px", border:"1px solid #2563eb", borderRadius:8, background:"#2563eb", color:"white" };
const pre: React.CSSProperties = { background:"#f6f6f6", padding:12, borderRadius:8, overflow:"auto" };


