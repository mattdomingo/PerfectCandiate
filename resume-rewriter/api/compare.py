from typing import Dict, Any
from sentence_transformers import SentenceTransformer, util
import difflib, numpy as np

# small, fast model
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def coverage_and_suggestions(json_resume: Dict[str, Any], requirements: list[str]):
    bullets = []
    for w in json_resume.get("work", []):
        bullets += w.get("highlights", [])
    bullets = [b.strip() for b in bullets if b.strip()]
    if not bullets or not requirements:
        return {"coverage": [], "missing": [], "rewrites": [], "original_text": "", "suggested_text": "", "patch": ""}

    # embeddings
    emb_reqs = _model.encode(requirements, convert_to_tensor=True, normalize_embeddings=True)
    emb_bul  = _model.encode(bullets,      convert_to_tensor=True, normalize_embeddings=True)
    sims = util.cos_sim(emb_reqs, emb_bul).cpu().numpy()

    # coverage: max score per requirement (0..1)
    cov = []
    for i, req in enumerate(requirements):
        j = int(np.argmax(sims[i]))
        cov.append({"requirement": req, "best_bullet": bullets[j], "score": float(sims[i, j])})
    cov.sort(key=lambda x: x["score"], reverse=True)

    # missing = low-sim requirements
    missing = [c for c in cov if c["score"] < 0.45][:10]

    # naive rewrites: nudge top-N missing into the closest bullet
    modified = bullets[:]
    rewrites = []
    for m in missing[:6]:
        before = m["best_bullet"]
        # find index of that bullet in the current list (first occurrence)
        try:
            idx = modified.index(before)
        except ValueError:
            continue
        after = before
        # append a short, plain-language alignment tag
        after = f"{before} — emphasizes: {m['requirement'][:160]}"
        modified[idx] = after
        rewrites.append({"before": before, "after": after, "reason": "Aligns with job requirement"})

    original_text = "\n".join(bullets)
    suggested_text = "\n".join(modified)
    patch = "\n".join(difflib.unified_diff(
        original_text.splitlines(), suggested_text.splitlines(),
        fromfile="resume", tofile="resume_suggested", lineterm=""
    ))
    return {
        "coverage": cov[:50],          # top 50 rows
        "missing": [m["requirement"] for m in missing],
        "rewrites": rewrites,
        "original_text": original_text,
        "suggested_text": suggested_text,
        "patch": patch
    }


