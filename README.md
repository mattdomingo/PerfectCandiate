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

---