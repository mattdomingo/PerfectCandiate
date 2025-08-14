import os, uuid, json, time, logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from urllib.parse import urlparse, urlunparse
from sqlalchemy import text
from db import get_engine, init_db
from extractor.extract import pdf_to_text, extract_fields
from job_parse import extract_job_text, extract_requirements
from compare import coverage_and_suggestions

# -----------------------------------------------------------------------------
# App & Logging
# -----------------------------------------------------------------------------
app = FastAPI(title="Resume Rewriter API")
logger = logging.getLogger("rr.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# DB
engine = get_engine()
init_db(engine)

# S3 / MinIO client
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
AWS_REGION  = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET   = os.getenv("S3_BUCKET")

if S3_ENDPOINT:
    # internal client for server-side S3 operations (reachable within Docker network)
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=AWS_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    # public-facing client for presigning URLs that browser can reach from host
    ep = urlparse(S3_ENDPOINT)
    public_netloc = f"localhost:{ep.port or 9000}"
    public_endpoint = urlunparse((ep.scheme, public_netloc, "", "", "", ""))
    s3_public = boto3.client(
        "s3",
        endpoint_url=public_endpoint,
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=AWS_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
else:
    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE") or None, region_name=AWS_REGION)
    s3 = session.client("s3")
    s3_public = s3

# CORS (idempotent)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Middleware: request-id + access log
# -----------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    start = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        dur_ms = (time.perf_counter() - start) * 1000
        path = request.url.path
        if path != "/health":
            logger.info(
                "rid=%s method=%s path=%s status=%s dur_ms=%.1f",
                rid, request.method, path, getattr(response, "status_code", "?"), dur_ms
            )

# -----------------------------------------------------------------------------
# Error handlers -> structured JSON
# -----------------------------------------------------------------------------
def error_response(status: int, error: str, detail: str, request: Request):
    return JSONResponse(
        status_code=status,
        content={
            "error": error,
            "detail": detail,
            "status": status,
            "request_id": getattr(request.state, "request_id", None),
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail)
    return error_response(exc.status_code, "HTTPException", msg, request)

@app.exception_handler(ClientError)
async def boto_exception_handler(request: Request, exc: ClientError):
    return error_response(502, "S3ClientError", str(exc), request)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("rid=%s unhandled error: %s", getattr(request.state, "request_id", None), exc)
    return error_response(500, "InternalServerError", "Unexpected error", request)

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    with engine.connect() as c:
        c.exec_driver_sql("select 1")
    s3.head_bucket(Bucket=S3_BUCKET)
    return {"ok": True, "db": "up", "s3": S3_BUCKET}

class PresignIn(BaseModel):
    content_type: Optional[str] = "application/pdf"

class ExtractReq(BaseModel):
    resume_id: str
    s3_key: str

@app.post("/upload-resume")
def upload_resume_start(payload: PresignIn):
    # Guard: only allow PDFs
    if payload.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf uploads are supported")
    rid = str(uuid.uuid4())
    key = f"resumes/{rid}.pdf"
    url = s3_public.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": "application/pdf"},
        ExpiresIn=900
    )
    with engine.begin() as c:
        c.exec_driver_sql("insert into resumes(id, s3_key) values (%s,%s)", (rid, key))
    return {"resume_id": rid, "s3_key": key, "put_url": url}

@app.post("/extract")
def extract(req: ExtractReq, request: Request):
    # Fetch object from S3
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=req.s3_key)
    except ClientError as e:
        # NoSuchKey => 404; otherwise bubble to handler
        if e.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            return error_response(404, "NotFound", f"S3 key not found: {req.s3_key}", request)
        raise
    pdf_bytes = obj["Body"].read()
    # parse
    text_val = pdf_to_text(pdf_bytes)
    json_resume = extract_fields(text_val)
    with engine.begin() as c:
        c.exec_driver_sql("update resumes set json_resume=%s where id=%s", (json.dumps(json_resume), req.resume_id))
    # cap raw text in response to avoid huge payloads
    preview = text_val if len(text_val) < 50000 else text_val[:50000]
    return {"resume_id": req.resume_id, "json_resume": json_resume, "raw_text": preview}



# --------------------------- Sunday AM: Job + Compare ---------------------------
class JobIn(BaseModel):
    url: str | None = None
    pasted: str | None = None

@app.post("/job/ingest")
def job_ingest(payload: JobIn):
    txt = extract_job_text(payload.url, payload.pasted)
    if not txt:
        raise HTTPException(400, "No job content found. Provide a URL or pasted text.")
    reqs = extract_requirements(txt)
    jid = str(uuid.uuid4())
    with engine.begin() as c:
        c.exec_driver_sql(
            "insert into job_posts(id, source_url, text_content, extracted) values (%s,%s,%s,%s::jsonb)",
            (jid, payload.url, txt, json.dumps({"requirements": reqs}))
        )
    return {"job_id": jid, "requirements": reqs, "chars": len(txt)}


class CompareIn(BaseModel):
    resume_id: str
    job_id: str

@app.post("/compare")
def compare_resume_job(payload: CompareIn):
    # load resume json and job extracted requirements
    with engine.connect() as c:
        r = c.execute(text("select json_resume from resumes where id=:id"), {"id": payload.resume_id}).first()
        j = c.execute(text("select extracted from job_posts where id=:id"), {"id": payload.job_id}).first()
    if not r or not r[0]:
        raise HTTPException(404, "Resume not found or not extracted yet")
    if not j or not j[0]:
        raise HTTPException(404, "Job not found")
    json_resume = r[0]
    requirements = j[0].get("requirements", [])
    result = coverage_and_suggestions(json_resume, requirements)
    return result


from typing import List, Dict, Any, Optional
from patcher import validate_ops, apply_ops

class ApplyPatchIn(BaseModel):
    resume_id: str
    patch: List[Dict[str, Any]]
    job_id: Optional[str] = None  # if present, we’ll return fresh coverage too

@app.post("/resume/apply-patch")
def resume_apply_patch(payload: ApplyPatchIn):
    # 1) load current resume JSON
    with engine.connect() as c:
        row = c.execute(text("select json_resume from resumes where id=:id"), {"id": payload.resume_id}).first()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Resume not found or not extracted yet")
    json_resume = row[0]

    # 2) validate patch
    ok, msg = validate_ops(payload.patch)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # 3) apply patch (replace-only)
    new_doc = apply_ops(json_resume, payload.patch)

    # 4) persist + version
    vid = str(uuid.uuid4())
    with engine.begin() as c:
        c.exec_driver_sql(
            "update resumes set json_resume=%s where id=%s",
            (json.dumps(new_doc), payload.resume_id)
        )
        c.exec_driver_sql(
            "insert into resume_versions(id, resume_id, json_resume) values (%s,%s,%s)",
            (vid, payload.resume_id, json.dumps(new_doc))
        )

    # 4b) write canonical JSON to S3/MinIO for external access/debugging
    json_key = f"json/{payload.resume_id}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=json_key,
        Body=json.dumps(new_doc).encode("utf-8"),
        ContentType="application/json",
        CacheControl="no-store"
    )

    resp = {"resume_id": payload.resume_id, "json_resume": new_doc, "version_id": vid, "s3_json_key": json_key}

    # 5) optional immediate re-compare
    if payload.job_id:
        with engine.connect() as c:
            j = c.execute(text("select extracted from job_posts where id=:id"), {"id": payload.job_id}).first()
        if j and j[0]:
            requirements = j[0].get("requirements", [])
            comp = coverage_and_suggestions(new_doc, requirements)
            resp["compare"] = comp

    return resp

# (optional) quick fetch endpoint
@app.get("/resume/{resume_id}")
def resume_get(resume_id: str):
    with engine.connect() as c:
        row = c.execute(text("select json_resume from resumes where id=:id"), {"id": resume_id}).first()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"resume_id": resume_id, "json_resume": row[0]}

from pydantic import BaseModel
from render import render_pdf, render_docx, filename_for

class RenderIn(BaseModel):
  resume_id: str
  fmt: str = "pdf"  # "pdf" | "docx"

@app.post("/render")
def render_resume(payload: RenderIn):
    # 1) fetch canonical JSON
    with engine.connect() as c:
        row = c.execute(text("select json_resume from resumes where id=:id"), {"id": payload.resume_id}).first()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Resume not found or not extracted yet")
    json_resume = row[0]

    # 2) render
    fmt = (payload.fmt or "pdf").lower()
    if fmt not in {"pdf","docx"}:
        raise HTTPException(status_code=400, detail="fmt must be 'pdf' or 'docx'")
    if fmt == "pdf":
        blob = render_pdf(json_resume)
        content_type = "application/pdf"
        ext = "pdf"
    else:
        blob = render_docx(json_resume)
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"

    # 3) upload to S3
    fname = filename_for(json_resume, ext)
    key = f"renders/{payload.resume_id}/{fname}"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=blob,
        ContentType=content_type,
        ContentDisposition=f'attachment; filename="{fname}"',
        CacheControl="no-store"
    )

    # 4) presign GET
    # Use the public-facing S3 client for presign so the browser can access localhost:9000
    url = s3_public.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=600
    )
    return {"download_url": url, "key": key, "content_type": content_type, "filename": fname}
