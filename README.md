# Resume Rewriter

An AI-powered web application that helps users optimize their resumes for specific job postings using semantic analysis and intelligent suggestions.

## Features

- **Resume Processing**: Upload PDF resumes and extract structured data
- **Job Analysis**: Extract requirements from job postings via URL or manual input
- **AI-Powered Matching**: Semantic similarity analysis between resumes and job requirements
- **Intelligent Suggestions**: AI-generated recommendations to improve resume alignment
- **Visual Diff**: Monaco Editor-based interface for reviewing and applying changes
- **Export System**: Generate optimized resumes as PDF and DOCX files
- **Version Control**: Maintain edit history and resume versions

## Tech Stack

- **Backend**: FastAPI with Python
- **Frontend**: Next.js with TypeScript
- **Database**: PostgreSQL
- **Storage**: S3-compatible (MinIO for local development)
- **Infrastructure**: Docker Compose

## Key Libraries

- **PDF Processing**: PyMuPDF, pytesseract (OCR)
- **NLP**: spaCy, sentence-transformers
- **Web Scraping**: trafilatura
- **File Generation**: WeasyPrint (PDF), python-docx (DOCX)
- **Frontend**: Monaco Editor for diff visualization

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd perfectCandidate
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001

## Development

### Backend Development
```bash
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
# Database migrations will be handled automatically on startup
# For manual migrations:
cd api
alembic upgrade head
```

## API Endpoints

- `POST /api/resumes/upload` - Upload and process resume
- `POST /api/jobs/analyze` - Analyze job description
- `POST /api/match/compare` - Compare resume with job requirements
- `GET /api/resumes/{id}/export` - Export optimized resume
- `GET /api/health` - Health check

## Environment Variables

Create `.env` files in both `api/` and `frontend/` directories:

### API (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/perfectcandidate
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=resumes
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
perfectCandidate/
├── api/                    # FastAPI backend
│   ├── app/               # Application code
│   ├── tests/             # Test files
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Backend container
├── frontend/              # Next.js frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── utils/           # Utility functions
│   ├── package.json     # Node dependencies
│   └── Dockerfile       # Frontend container
├── docker-compose.yml    # Service orchestration
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
