import io, re, unicodedata
import fitz
import pytesseract
from PIL import Image
import spacy

_NLP = None
def _get_nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
URL_RE = re.compile(r"(https?://[^\s]+|[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\s]*)")
MONTH_RE = re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b", re.I)
DATE_LINE_RE = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\w\s\-–—,]*(\d{4})\b|\b\d{4}\b")
DATE_RANGE_RE = re.compile(r"(?P<start>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s\u00A0]+\d{4})\s*[\-–—]\s*(?P<end>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s\u00A0]+\d{4}|Present)\b", re.I)
BULLET_MARKERS = {"●", "•", "-", "*", "◦", "▪", "·", "‣"}


def _normalize_text(text: str) -> str:
    # Remove zero-width and special spaces, normalize dashes, collapse spaces
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = text.replace("\u00A0", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[\t\r]+", " ", text)
    return text


HEADER_TOKENS = (
    "EXPERIENCE", "PROFESSIONAL EXPERIENCE", "WORK EXPERIENCE",
    "PROJECTS", "EDUCATION", "TECHNICAL TOOLKIT", "SKILLS",
    "LEADERSHIP", "INVOLVEMENT"
)

def _trim_header_suffix(s: str) -> str:
    up = unicodedata.normalize("NFKD", s).upper()
    for token in HEADER_TOKENS:
        pos = up.find(token)
        if pos > 0:
            return s[:pos].rstrip(" -;|,")
    return s

def _sanitize_highlights(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for b in items:
        s = b.strip()
        # strip leading bullet markers (with or without a following space)
        s = re.sub(r"^[\u2022\u25CF\*\-•●]+\s*", "", s)
        s = _trim_header_suffix(s)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def pdf_to_text(pdf_bytes: bytes) -> str:
    doc = fitz.open("pdf", pdf_bytes)
    pages = [p.get_text("text").strip() for p in doc]
    txt = "\n".join(p for p in pages if p)
    txt = _normalize_text(txt)
    if len(txt) >= 200:
        return txt
    # OCR fallback for image-only PDFs
    ocr_pages = []
    for p in doc:
        pix = p.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_pages.append(pytesseract.image_to_string(img))
    return _normalize_text("\n".join(ocr_pages))


def _coalesce_bare_bullets(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s in BULLET_MARKERS:
            # find next non-empty non-marker line and join as one bullet
            j = i + 1
            parts: list[str] = []
            while j < len(lines):
                t = lines[j].strip()
                if not t:
                    j += 1
                    continue
                if t[0] in BULLET_MARKERS:
                    break
                parts.append(t)
                # include up to two following non-marker lines for wrap
                k = j + 1
                while k < len(lines):
                    u = lines[k].strip()
                    if not u or u[0] in BULLET_MARKERS:
                        break
                    parts.append(u)
                    k += 1
                    break
                break
            if parts:
                out.append("• " + " ".join(parts))
                i = max(j, i + 1)
                continue
        out.append(lines[i])
        i += 1
    return out


def _split_lines(text: str) -> list[str]:
    raw = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    raw = [l for l in raw if l]
    return _coalesce_bare_bullets(raw)


def _detect_sections(lines: list[str]) -> dict:
    headers_map = {
        "EDUCATION": "education",
        "EXPERIENCE": "experience",
        "WORK EXPERIENCE": "experience",
        "PROFESSIONAL EXPERIENCE": "experience",
        "PROJECTS": "projects",
        "LEADERSHIP & INVOLVEMENT": "leadership",
        "LEADERSHIP": "leadership",
        "INVOLVEMENT": "leadership",
        "TECHNICAL TOOLKIT": "skills",
        "SKILLS": "skills",
        "CERTIFICATIONS": "skills",
        "CERTIFICATIONS, AWARDS & SKILLS": "skills",
    }
    idxs = []
    for i, l in enumerate(lines):
        up = unicodedata.normalize("NFKD", l).upper()
        for h, key in headers_map.items():
            if up.startswith(h):
                idxs.append((i, key))
                break
    idxs.sort()
    segments: dict[str, list[str]] = {}
    for k in range(len(idxs)):
        i, key = idxs[k]
        j = idxs[k + 1][0] if k + 1 < len(idxs) else len(lines)
        segments.setdefault(key, [])
        segments[key] = lines[i + 1 : j]
    return segments


_ROLE_HINTS = re.compile(r"\b(Intern|Analyst|Associate|Engineer|Developer|Manager|Lead|Coach|Secretary|Member|Marketing|Guest Services|Consultant|Assistant|Research|Fellow|President|Founder|Director)\b", re.I)

def _is_location_line(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z .'-]+,\s*[A-Z]{2}", s))

def _is_header_line(s: str) -> bool:
    up = unicodedata.normalize("NFKD", s).upper()
    return up.startswith(("EXPERIENCE", "PROFESSIONAL EXPERIENCE", "PROJECTS", "EDUCATION", "TECHNICAL TOOLKIT", "SKILLS", "LEADERSHIP", "INVOLVEMENT"))


ROLE_TITLE_RE = re.compile(r"\b(Intern|Analyst|Associate|Engineer|Developer|Manager|Lead|Coach|Secretary|Member|Marketing|Consultant|Assistant|Research|Fellow|President|Founder|Director|Advisor|Teacher)\b", re.I)

def _is_role_line(s: str) -> bool:
    if not s:
        return False
    if DATE_LINE_RE.search(s) and len(s) <= 64:
        return False
    return bool(ROLE_TITLE_RE.search(s))

COMPANY_SUFFIX_RE = re.compile(r"\b(Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?|Company|University|College|Golf Course|Club|State|Council|Committee|Ministry|Agency)\b")

def _is_company_line_fast(s: str) -> bool:
    if not s:
        return False
    if _is_header_line(s) or _is_location_line(s) or (DATE_LINE_RE.search(s) and len(s) <= 64):
        return False
    if "|" in s:
        return True
    if COMPANY_SUFFIX_RE.search(s):
        return True
    # Title-style capitalization heuristic
    words = [w for w in s.split() if w.isalpha()]
    caps = sum(w[:1].isupper() for w in words)
    if len(words) >= 2 and caps >= 2 and not ROLE_TITLE_RE.search(s):
        return True
    return False

def _looks_like_new_job_header(lines: list[str], idx: int) -> bool:
    s = lines[idx].strip()
    if _is_company_line_fast(s):
        return True
    # Company line followed by a location or role/date line
    if idx + 1 < len(lines):
        n1 = lines[idx + 1].strip()
        if _is_location_line(n1):
            return True
        if _is_role_line(n1):
            return True
        if DATE_LINE_RE.search(n1) and len(n1) <= 64:
            return True
    return False

def _extract_basics(lines: list[str], raw_text: str) -> tuple[dict, int]:
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    email = email_match.group(0) if email_match else None
    phone = phone_match.group(0) if phone_match else None

    # contact line index and text
    contact_idx = None
    for i, l in enumerate(lines):
        if (email and email in l) or (phone and phone in l):
            contact_idx = i
            break

    # name: first non-empty line above contact that looks like a name
    name = None
    if contact_idx is not None:
        for i in range(contact_idx - 1, -1, -1):
            cand = lines[i]
            if "|" in cand or EMAIL_RE.search(cand) or PHONE_RE.search(cand):
                continue
            words = [w for w in re.split(r"\s+", cand) if w.isalpha()]
            if len(words) >= 2 and sum(w[:1].isupper() for w in words[:2]) >= 2:
                name = cand
                break
    if not name:
        # fallback to first line
        for cand in lines:
            if cand and not (EMAIL_RE.search(cand) or PHONE_RE.search(cand)):
                name = cand
                break

    # location and links from contact line or neighbors
    location = None
    links: list[str] = []
    neigh = []
    if contact_idx is not None:
        neigh.extend([lines[contact_idx]])
        if contact_idx + 1 < len(lines):
            neigh.append(lines[contact_idx + 1])
        if contact_idx - 1 >= 0:
            neigh.append(lines[contact_idx - 1])
    for s in neigh:
        # location as first segment before '|'
        if "|" in s and not location:
            left = s.split("|")[0].strip()
            # heuristic: contains comma and state abbreviation
            if re.search(r",\s*[A-Z]{2}\b", left):
                location = left
        for m in URL_RE.findall(s):
            if "@" in m:
                continue
            links.append(m)
    # dedupe links and prefer canonical linkedin/github
    uniq = []
    for u in links:
        u = u.rstrip('.,;')
        if u not in uniq:
            uniq.append(u)

    # Remove duplicates and email-domains accidentally matched as links
    email_domain = None
    if email and "@" in email:
        email_domain = email.split("@", 1)[1]
    filtered: list[str] = []
    for u in uniq:
        if email_domain and email_domain in u and u.count(".") == 1:
            continue
        filtered.append(u)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "links": filtered,
    }, (contact_idx or 0)


def _parse_education(lines: list[str]) -> list[dict]:
    edu = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if re.search(r"(University|College|Institute)\b", l):
            entry = {"institution": l, "degree": None, "date": None, "location": None}
            # lookahead few lines
            j = i + 1
            window = []
            while j < len(lines) and j <= i + 6:
                window.append(lines[j])
                j += 1
            # degree
            for s in window:
                if re.search(r"(Bachelor|Master|B\.?S\.?|BSc|M\.?S\.?|MSc|PhD|Doctor)", s, re.I):
                    # strip trailing date portion from degree line
                    m = DATE_LINE_RE.search(s)
                    degree = s
                    if m:
                        degree = s[:m.start()].rstrip(" -,")
                        if not entry["date"]:
                            entry["date"] = s[m.start():].strip()
                    entry["degree"] = degree
                    break
            # date
            for s in window:
                if DATE_LINE_RE.search(s):
                    entry["date"] = s.strip()
                    break
            # location
            for s in window:
                if re.search(r",\s*[A-Z]{2}\b", s):
                    entry["location"] = s.strip()
                    break
            edu.append(entry)
            i = j
            continue
        i += 1
    return edu


def _collect_bullets(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    bullets: list[str] = []
    k = start_idx
    while k < len(lines):
        s = lines[k].strip()
        if not s:
            # blank lines: if we've started bullets, end; else skip
            if bullets:
                break
            k += 1
            continue
        up = unicodedata.normalize("NFKD", s).upper()
        # stop at next header or job header (role | company)
        if _looks_like_new_job_header(lines, k):
            break
        if up.startswith(("EXPERIENCE", "PROJECTS", "EDUCATION", "TECHNICAL TOOLKIT", "SKILLS", "LEADERSHIP")):
            break

        # marker + text on same line
        if s[0] in BULLET_MARKERS and (len(s) == 1 or s[1] == " "):
            if len(s) > 2:
                bullets.append(s[2:].strip())
                k += 1
                # absorb wrap lines until next marker/header
                while k < len(lines):
                    nxt = lines[k].strip()
                    if not nxt or nxt[0] in BULLET_MARKERS:
                        break
                    upn = unicodedata.normalize("NFKD", nxt).upper()
                    if _looks_like_new_job_header(lines, k):
                        break
                    if len(nxt) <= 240:
                        bullets[-1] += " " + nxt
                        k += 1
                    else:
                        break
                continue
            else:
                # bare marker: take following lines as bullet text
                k += 1
                parts: list[str] = []
                while k < len(lines):
                    nxt = lines[k].strip()
                    if not nxt:
                        if parts:
                            k += 1
                            break
                        k += 1
                        continue
                    if nxt[0] in BULLET_MARKERS or _looks_like_new_job_header(lines, k):
                        break
                    upn = unicodedata.normalize("NFKD", nxt).upper()
                    if upn.startswith(("EXPERIENCE", "PROJECTS", "EDUCATION", "TECHNICAL TOOLKIT", "SKILLS")) or "|" in nxt:
                        break
                    parts.append(nxt)
                    k += 1
                    if sum(len(p) for p in parts) > 500:
                        break
                if parts:
                    bullets.append(" ".join(parts))
                continue

        # treat pre-bullet summary line as a first highlight if meaningful
        if not bullets and len(s) >= 20 and s[0] not in BULLET_MARKERS and not DATE_LINE_RE.search(s) and not re.fullmatch(r"[A-Za-z .]+,\s*[A-Z]{2}", s) and not _looks_like_new_job_header(lines, k):
            bullets.append(s)
            k += 1
            continue

        # continuity lines for last bullet
        if bullets and len(s) <= 180 and s[0] not in BULLET_MARKERS and not DATE_LINE_RE.search(s) and not _looks_like_new_job_header(lines, k):
            bullets[-1] += " " + s
            k += 1
            continue

        # anything else ends bullet collection
        break
    return bullets, k


def _parse_experience_or_projects(lines: list[str]) -> list[dict]:
    work = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if "|" in l:
            # format: Role | Company
            role, company = [p.strip() for p in l.split("|", 1)]
            location = None
            start = end = ""
            j = i + 1
            # scan a small window for location and date lines
            scan_limit = min(len(lines), j + 6)
            summary = None
            while j < scan_limit:
                s = lines[j].strip()
                if not s:
                    j += 1
                    continue
                if not location and re.search(r",\s*[A-Z]{2}\b", s):
                    location = s
                    j += 1
                    continue
                if DATE_LINE_RE.search(s):
                    # Try to isolate date range substring from the line
                    mrange = DATE_RANGE_RE.search(s)
                    if mrange:
                        start, end = mrange.group("start"), mrange.group("end")
                        # capture any summary text before the date range on the same line
                        prefix = s[: mrange.start()].strip()
                        if prefix and prefix[0] not in {"●", "•", "-", "*"}:
                            summary = prefix
                    else:
                        # fallback: use the part of the line that looks closest to dates
                        # extract all month/year tokens and join
                        months = MONTH_RE.findall(s)
                        years = re.findall(r"\b\d{4}\b", s)
                        if years:
                            start = (months[0] + " " + years[0]) if months else years[0]
                            end = (months[-1] + " " + years[-1]) if len(years) > 1 and months else (years[-1] if len(years) > 1 else "")
                            # prefix before the first year as summary, if present
                            first_year_pos = s.find(years[0])
                            prefix = s[:first_year_pos].strip()
                            if prefix and prefix[0] not in {"●", "•", "-", "*"}:
                                summary = prefix
                        else:
                            start = s.strip()
                    j += 1
                    break
                # treat a non-marker, non-date line before bullets as a summary
                if s and s[0] not in {"●", "•", "-", "*"} and not summary:
                    summary = s
                    j += 1
                    continue
                j += 1
            bullets, k = _collect_bullets(lines, j)
            # Fallback: if no bullets found, consume descriptive lines until the next role/company or header
            if not bullets:
                k2 = j
                bullets2: list[str] = []
                while k2 < len(lines):
                    s2 = lines[k2].strip()
                    if not s2:
                        k2 += 1
                        if bullets2:
                            break
                        continue
                    up = unicodedata.normalize("NFKD", s2).upper()
                    if ("|" in s2 and k2 > j + 1) or up.startswith(("EXPERIENCE", "PROJECTS", "EDUCATION", "TECHNICAL TOOLKIT", "SKILLS")):
                        break
                    if s2 in BULLET_MARKERS:
                        # bare marker: gather the subsequent line(s) as a bullet
                        k2 += 1
                        parts = []
                        while k2 < len(lines):
                            nxt = lines[k2].strip()
                            if not nxt:
                                k2 += 1
                                if parts:
                                    break
                                else:
                                    continue
                            if nxt[0] in BULLET_MARKERS:
                                break
                            parts.append(nxt)
                            k2 += 1
                        if parts:
                            bullets2.append(" ".join(parts))
                        continue
                    if DATE_LINE_RE.search(s2):
                        k2 += 1
                        continue
                    # skip pure location lines
                    if re.fullmatch(r"[A-Za-z .]+,\s*[A-Z]{2}", s2):
                        k2 += 1
                        continue
                    bullets2.append(s2)
                    k2 += 1
                    if len(bullets2) >= 12:
                        break
                if bullets2:
                    bullets = bullets2
                    k = k2
            if summary:
                bullets = [summary] + bullets
            work.append({
                "company": company,
                "position": role,
                "start": start,
                "end": end,
                "location": location,
                "highlights": _sanitize_highlights(bullets)[:12] if bullets else []
            })
            i = k if (k > i) else i + 1
            continue
        i += 1
    return work


def _parse_experience_or_projects_general(lines: list[str]) -> list[dict]:
    work: list[dict] = []
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if not s or _is_header_line(s):
            i += 1
            continue
        # candidate company line; avoid pure location/date
        if _is_location_line(s) or (DATE_LINE_RE.search(s) and len(s) <= 64):
            i += 1
            continue

        # determine company line using heuristics and NLP
        company = ""
        if "|" in s:
            # e.g., Role | Company (rare in this path)
            parts = [p.strip() for p in s.split("|", 1)]
            if len(parts) == 2:
                role, company = parts[0], parts[1]
        if not company:
            company = s
        location = None
        role = ""
        start = end = ""

        j = i + 1
        # optional location line
        if j < n and _is_location_line(lines[j].strip()):
            location = lines[j].strip()
            j += 1

        # role may be on this line; may contain date range too
        if j < n:
            srole = lines[j].strip()
            if srole and not _is_header_line(srole) and not _is_location_line(srole):
                # Extract date range if present on same line
                mrange = DATE_RANGE_RE.search(srole)
                if mrange:
                    role = srole[: mrange.start()].strip()
                    start, end = mrange.group("start"), mrange.group("end")
                    j += 1
                else:
                    # accept as role if it looks like a title or lacks clear date pattern
                    if not (DATE_LINE_RE.search(srole) and len(srole) <= 64):
                        role = srole
                        j += 1

        # separate date line
        if j < n and not (start or end):
            sdate = lines[j].strip()
            if DATE_LINE_RE.search(sdate):
                mrange2 = DATE_RANGE_RE.search(sdate)
                if mrange2:
                    start, end = mrange2.group("start"), mrange2.group("end")
                else:
                    years = re.findall(r"\b\d{4}\b", sdate)
                    months = MONTH_RE.findall(sdate)
                    if years:
                        start = (months[0] + " " + years[0]) if months else years[0]
                        if len(years) > 1:
                            end = (months[-1] + " " + years[-1]) if months else years[-1]
                j += 1

        # bullets
        bullets, k = _collect_bullets(lines, j)
        # Guard: stop bullets if we accidentally crossed into next job header
        if k < len(lines) and _looks_like_new_job_header(lines, k):
            pass
        # If role is empty but we have a hint at the line before bullets, set it
        if not role and j - 1 >= 0:
            prev = lines[j - 1].strip()
            if prev and prev[0] not in BULLET_MARKERS and not DATE_LINE_RE.search(prev) and not _is_location_line(prev):
                role = prev

        # If everything looks valid (company or role present), record entry
        if company or role or bullets:
            work.append({
                "company": company,
                "position": role,
                "start": start,
                "end": end,
                "location": location,
                "highlights": _sanitize_highlights(bullets)[:12] if bullets else []
            })
            i = k if k > i else j if j > i else i + 1
        else:
            i += 1
    return work


def _parse_skills(lines: list[str]) -> list[dict]:
    skills = []
    for l in lines:
        if ":" in l:
            name, rest = l.split(":", 1)
            name = name.strip()
            # split primarily on commas/semicolons, not on slashes to preserve terms like CI/CD
            raw = [s.strip() for s in re.split(r",|;", rest) if s.strip()]
            keywords: list[str] = []
            for tok in raw:
                # expand some common language combos
                if tok.lower() in {"typescript/javascript", "typescript / javascript"}:
                    keywords.extend(["TypeScript", "JavaScript"])
                elif tok.lower() in {"c/c++", "c / c++"}:
                    keywords.extend(["C", "C++"])
                else:
                    keywords.append(tok)
            if keywords:
                skills.append({"name": name, "keywords": keywords})
    # fallback: collapse all into General
    if not skills and lines:
        words = [w.strip() for w in ", ".join(lines).split(",")]
        words = [w for w in words if w]
        if words:
            skills.append({"name": "General", "keywords": words})
    return skills


def _parse_inline_skills_anywhere(lines: list[str]) -> list[dict]:
    found: list[dict] = []
    for l in lines:
        up = unicodedata.normalize("NFKD", l).upper()
        if ":" in l and ("SKILL" in up or "CERTIFICATION" in up or "AWARD" in up):
            name, rest = l.split(":", 1)
            name = name.strip()
            raw = [s.strip() for s in re.split(r",|;", rest) if s.strip()]
            if raw:
                found.append({"name": name.title(), "keywords": raw})
    return found
def extract_fields(raw_text: str) -> dict:
    text = _normalize_text(raw_text)
    lines = _split_lines(text)

    basics, _ = _extract_basics(lines, text)
    sections = _detect_sections(lines)

    education = _parse_education(sections.get("education", []))
    # Try strict role|company first, then fallback to general pattern if sparse
    exp_lines = sections.get("experience", [])
    prj_lines = sections.get("projects", [])
    experience = _parse_experience_or_projects(exp_lines)
    if not experience:
        experience = _parse_experience_or_projects_general(exp_lines)
    projects = _parse_experience_or_projects(prj_lines)
    if not projects:
        projects = _parse_experience_or_projects_general(prj_lines)
    skills = _parse_skills(sections.get("skills", []))
    if not skills:
        # search entire document for inline skills/certs lines
        skills = _parse_inline_skills_anywhere(lines)

    # merge projects into work with a flag
    for p in projects:
        if p.get("company") and p.get("position"):
            p["company"] = f"{p['company']} (Project)"
        else:
            p["company"] = (p.get("company") or "Project") + " (Project)"
    work = experience + projects

    # Post-process work entries to merge duplicates (same company, position, dates)
    merged: list[dict] = []
    sig_to_idx: dict[tuple[str, str, str, str], int] = {}
    for w in work:
        sig = (
            (w.get("company") or "").strip().lower(),
            (w.get("position") or "").strip().lower(),
            (w.get("start") or "").strip().lower(),
            (w.get("end") or "").strip().lower(),
        )
        if sig in sig_to_idx:
            idx = sig_to_idx[sig]
            # merge highlights
            merged[idx]["highlights"] = _sanitize_highlights(merged[idx].get("highlights", []) + (w.get("highlights") or []))[:12]
        else:
            w = {**w}
            w["highlights"] = _sanitize_highlights(w.get("highlights", []))[:12]
            sig_to_idx[sig] = len(merged)
            merged.append(w)
    work = merged

    # Fallback highlights if nothing parsed
    if not work:
        # Collect top bullets from entire doc as highlights
        bullets = [l for l in lines if l[:1] in {"-", "•", "●"}]
        work = [{"company": "", "position": "", "start": "", "end": "", "highlights": [b.lstrip("-•● ") for b in bullets[:8]]}]

    # NLP-assisted enrichment/fallback
    try:
        nlp = _get_nlp()
        doc = nlp(text)
        # Guess name if missing
        if not basics.get("name"):
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                basics["name"] = persons[0]
        # If work is sparse or has empty company/position, try to infer ORG and role words near bullets
        if work and (not work[0].get("company") or not work[0].get("position")):
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs and not work[0].get("company"):
                work[0]["company"] = orgs[0]
            # simple role guess from frequent title-like tokens
            title_candidates = re.findall(r"\b(Intern|Analyst|Associate|Engineer|Developer|Manager|Lead|Coach|Secretary|Member|Marketing|Consultant)\b", text, re.I)
            if title_candidates and not work[0].get("position"):
                work[0]["position"] = title_candidates[0]
    except Exception:
        pass

    return {
        "basics": basics,
        "skills": skills or [{"name": "General", "keywords": []}],
        "education": education,
        "work": work,
        "_meta": {"line_count": len(lines)}
    }

