import json, uuid, os, sys
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app, engine
from fastapi.testclient import TestClient

client = TestClient(app)

def seed_resume(highlights):
    rid = str(uuid.uuid4())
    doc = {
        "basics": {"email": "jane@smith.dev", "phone": None},
        "skills": [{"name":"General","keywords":[]}],
        "education": [],
        "work": [{"company":"","position":"","start":"","end":"","highlights": highlights}]
    }
    with engine.begin() as c:
        c.exec_driver_sql("insert into resumes(id, s3_key, json_resume) values (%s,%s,%s)",
                          (rid, f"resumes/{rid}.pdf", json.dumps(doc)))
    return rid, doc

def test_apply_patch_happy_path():
    rid, doc = seed_resume(["old bullet A", "old bullet B"])
    patch = [{"op":"replace","path":"/work/0/highlights/1","value":"new bullet B"}]
    r = client.post("/resume/apply-patch", json={"resume_id": rid, "patch": patch})
    assert r.status_code == 200, r.text
    out = r.json()["json_resume"]["work"][0]["highlights"]
    assert out[1] == "new bullet B"
    # verify DB persisted
    with engine.connect() as c:
        row = c.execute(text("select json_resume from resumes where id=:id"), {"id": rid}).first()
    assert row is not None and row[0]["work"][0]["highlights"][1] == "new bullet B"

def test_apply_patch_reject_path():
    rid, _ = seed_resume(["a"])
    bad = [{"op":"replace","path":"/work/0/company","value":"ACME"}]
    r = client.post("/resume/apply-patch", json={"resume_id": rid, "patch": bad})
    assert r.status_code == 400


