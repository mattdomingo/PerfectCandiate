import json, re
from typing import List, Dict, Any, Tuple

# Whitelist: allow replacing only bullets under work[*].highlights[*]
PATH_ALLOWED_RE = re.compile(r"^/work/\d+/highlights/\d+$")

def validate_ops(ops: List[Dict[str, Any]]) -> Tuple[bool, str]:
    if not isinstance(ops, list) or len(ops) == 0:
        return False, "patch must be a non-empty array"
    for i, op in enumerate(ops):
        if op.get("op") != "replace":
            return False, f"op[{i}] must be 'replace'"
        path = op.get("path")
        if not isinstance(path, str) or not PATH_ALLOWED_RE.match(path):
            return False, f"op[{i}] path not allowed: {path}"
        val = op.get("value")
        if not isinstance(val, str):
            return False, f"op[{i}] value must be string"
        if len(val) > 400:
            return False, f"op[{i}] value too long (>400 chars)"
    return True, ""

def apply_ops(doc: Dict[str, Any], ops: List[Dict[str, Any]]) -> Dict[str, Any]:
    # immutable apply
    out = json.loads(json.dumps(doc))
    for op in ops:
        parts = [p for p in op["path"].split("/") if p]
        cur = out
        for k in parts[:-1]:
            key = int(k) if k.isdigit() else k
            cur = cur[key]
        last = parts[-1]
        last_key = int(last) if last.isdigit() else last
        cur[last_key] = op["value"]
    return out


