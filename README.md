# Resume Rewriter (Weekend MVP – Saturday AM)

## Quick start
1. Copy env: `cp .env.example .env`
2. Bring up the stack:
   ```bash
   docker compose up -d --build
   ```

3. Open:

   * Frontend: [http://localhost:3000](http://localhost:3000)
   * API: [http://localhost:8000/health](http://localhost:8000/health)
   * MinIO Console: [http://localhost:9001](http://localhost:9001) (minioadmin / minioadmin)

## What’s running

* Postgres 16 (user: app / pass: app / db: rr)
* MinIO (S3-compatible) with bucket `resumes`
* FastAPI with `/health` (checks DB + S3)
* Next.js page that pings the API using `NEXT_PUBLIC_API_URL`

## Next steps (Saturday PM / Sunday)

* Add presigned PUT upload + PDF extraction endpoints.
* Wire frontend to upload a PDF and trigger extraction.
* Persist parsed JSON resume in Postgres.

---

## ACCEPTANCE CRITERIA

* `docker compose up -d --build` succeeds with no container crash loops.
* Visiting [http://localhost:3000](http://localhost:3000) shows a button that checks the API; clicking shows “OK (DB: up, S3: resumes)”.
* Visiting [http://localhost:8000/health](http://localhost:8000/health) returns JSON with {"ok": true, "db":"up","s3":"resumes"}.
* MinIO console loads at [http://localhost:9001](http://localhost:9001) and bucket `resumes` exists.
* `make logs`, `make api-logs`, and `make fe-logs` stream logs.
* Code hot-reloads for both API and frontend when editing local files.

IMPORTANT IMPLEMENTATION NOTES

* Use the exact file paths and contents above.
* Do not rename services or containers.
* Assume local dev only; secrets are in `.env` copied from `.env.example`.
* Keep versions as pinned above.
* If any ambiguity arises, ask a single clarifying question, then proceed.

\n## Sunday PM — Hardening & Polish
\n- **One command dev**: `docker compose up -d --build` (or `make dev`)
- **Health**: http://localhost:8000/health should return `{ ok: true, db: "up", s3: "<bucket>" }`
- **Structured errors**: API returns `{error, detail, status, request_id}` on failures
- **Content-Type guard**: `/upload-resume` only presigns `application/pdf`
- **Logging**: per-request logs with `rid`, method, path, status, duration (ms)
- **Tests**: run `make test` (creates in-memory PDFs and validates extraction)
\nTroubleshooting:
- If uploads fail from the browser, verify your bucket CORS allows `PUT` and matches `Content-Type: application/pdf`.
- If using real AWS S3, remove `S3_ENDPOINT` from `.env` and set `AWS_PROFILE` or default creds.