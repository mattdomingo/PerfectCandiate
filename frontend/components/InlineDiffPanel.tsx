"use client";
import React, { useMemo, useState } from "react";
import DiffRow from "./DiffRow";
import { buildPatchFromRewrites, applyPatchLocal } from "../utils/patch";
import { JsonPatchOp, Rewrite } from "../types/jsonPatch";

type Props = Readonly<{
  resumeJson: any;
  rewrites: Rewrite[];
  pendingPatch: JsonPatchOp[];
  onUpdatePatch: (ops: JsonPatchOp[]) => void;
}>;

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
    <section className="inline-diff">
      <div className="inline-diff__header">
        <h3 className="section-title">Experience — inline suggestions</h3>
        <span className="muted">({pendingPatch.length} accepted)</span>
        <div className="spacer" />
        <div className="row gap">
          <button onClick={acceptAll} className="btn btn-primary">Accept all</button>
          <button onClick={resetAll} className="btn">Reset</button>
        </div>
      </div>

      {rewrites.length === 0 && <div className="muted">No suggestions available. Run Compare first.</div>}

      {visible.length === 0 && <div className="muted">All suggestions handled.</div>}
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

      <details className="details">
        <summary>Preview (first job’s highlights after accepted changes)</summary>
        <pre className="pre">
{JSON.stringify(preview?.work?.[0]?.highlights ?? [], null, 2)}
        </pre>
      </details>

      <details className="details">
        <summary>Pending JSON Patch</summary>
        <pre className="pre">{JSON.stringify(pendingPatch, null, 2)}</pre>
      </details>
    </section>
  );
}

// styles in globals.css


