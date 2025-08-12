import trafilatura, re

BULLET_RE = re.compile(r"^\s*([\-•\*\u2022])\s+", re.UNICODE)

def extract_job_text(url: str | None, pasted: str | None) -> str:
    if pasted and pasted.strip():
        return pasted.strip()
    if not url:
        return ""
    html = trafilatura.fetch_url(url)
    text = trafilatura.extract(html) or ""
    return text.strip()

def extract_requirements(text: str) -> list[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    bullets = [l for l in lines if BULLET_RE.match(l)]
    longish = [l for l in lines if len(l) >= 40]
    # prefer bullets; fallback to long lines
    reqs = bullets if len(bullets) >= 8 else longish
    # de-dup & cap
    uniq = []
    seen = set()
    for r in reqs:
        if r not in seen:
            uniq.append(r)
            seen.add(r)
        if len(uniq) >= 60:
            break
    return uniq


