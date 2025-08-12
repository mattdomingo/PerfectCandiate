import { JsonPatchOp, Rewrite } from "../types/jsonPatch";

// Find a bullet location for "before" across all work[].highlights,
// avoiding locations already used. Returns { workIdx, idx } or null.
export function locateBullet(
  before: string,
  work: Array<{ highlights?: string[] }>,
  used: Set<string>
): { workIdx: number; idx: number } | null {
  const needle = before.trim();
  // exact match pass
  for (let w = 0; w < (work?.length || 0); w++) {
    const highlights = work?.[w]?.highlights || [];
    for (let i = 0; i < highlights.length; i++) {
      const key = `${w}:${i}`;
      if (used.has(key)) continue;
      if ((highlights[i] ?? "").trim() === needle) {
        return { workIdx: w, idx: i };
      }
    }
  }
  // fuzzy contains fallback (first 20 chars)
  const fragment = before.slice(0, Math.min(20, before.length));
  for (let w = 0; w < (work?.length || 0); w++) {
    const highlights = work?.[w]?.highlights || [];
    for (let i = 0; i < highlights.length; i++) {
      const key = `${w}:${i}`;
      if (used.has(key)) continue;
      if ((highlights[i] ?? "").includes(fragment)) {
        return { workIdx: w, idx: i };
      }
    }
  }
  return null;
}

export function buildPatchFromRewrites(
  rewrites: Rewrite[],
  resumeJson: any
): { patch: JsonPatchOp[]; mapping: { workIdx: number; idx: number; before: string; after: string }[] } {
  const work = Array.isArray(resumeJson?.work) ? resumeJson.work : [];
  const used = new Set<string>();
  const patch: JsonPatchOp[] = [];
  const mapping: { workIdx: number; idx: number; before: string; after: string }[] = [];

  for (const r of rewrites) {
    const loc = locateBullet(r.before, work, used);
    if (loc) {
      const key = `${loc.workIdx}:${loc.idx}`;
      used.add(key);
      const path = `/work/${loc.workIdx}/highlights/${loc.idx}`;
      patch.push({ op: "replace", path, value: r.after });
      mapping.push({ workIdx: loc.workIdx, idx: loc.idx, before: r.before, after: r.after });
    }
  }
  return { patch, mapping };
}

// Apply replace-only JSON Patch locally (immutable).
export function applyPatchLocal(resumeJson: any, patch: JsonPatchOp[]) {
  const clone = JSON.parse(JSON.stringify(resumeJson));
  for (const op of patch) {
    if (op.op !== "replace") continue;
    const parts = op.path.split("/").filter(Boolean); // ["work","0","highlights","3"]
    let cursor: any = clone;
    for (let i = 0; i < parts.length - 1; i++) {
      const key = isFinite(Number(parts[i])) ? Number(parts[i]) : parts[i];
      cursor = cursor[key];
      if (cursor === undefined) break;
    }
    const lastKeyRaw = parts[parts.length - 1];
    const lastKey = isFinite(Number(lastKeyRaw)) ? Number(lastKeyRaw) : lastKeyRaw;
    if (cursor && lastKey in cursor) {
      cursor[lastKey] = op.value;
    }
  }
  return clone;
}


