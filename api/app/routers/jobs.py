"""
Job analysis router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
from typing import Optional
import logging

from app.database import get_db
from app.models.job import Job
from app.services.job_analyzer import JobAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


class JobAnalysisRequest(BaseModel):
    """Request model for job analysis"""
    job_url: Optional[HttpUrl] = None
    job_text: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None


@router.post("/analyze")
async def analyze_job(
    request: JobAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Analyze a job posting"""
    if not request.job_url and not request.job_text:
        raise HTTPException(
            status_code=400, 
            detail="Either job_url or job_text must be provided"
        )
    
    try:
        job_analyzer = JobAnalyzer()
        
        # Analyze job content
        if request.job_url:
            # Extract and analyze from URL
            analysis_result = await job_analyzer.analyze_job_from_url(str(request.job_url))
        else:
            # Analyze provided text
            analysis_result = await job_analyzer.analyze_job_text(request.job_text)
        
        # Create job record in database
        job = Job(
            title=request.title,
            company=request.company,
            location=request.location or analysis_result.get('location'),
            job_url=str(request.job_url) if request.job_url else None,
            original_text=analysis_result['original_text'],
            description=analysis_result['cleaned_text'],
            requirements=analysis_result['requirements'],
            preferred_qualifications=analysis_result['preferred_qualifications'],
            responsibilities=analysis_result['responsibilities'],
            benefits=analysis_result['benefits'],
            salary_range=analysis_result['salary_range'],
            analysis_confidence=analysis_result['analysis_confidence'],
            key_keywords=analysis_result['key_keywords']
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return {
            "message": "Job analyzed successfully",
            "job_id": job.id,
            "job_uuid": job.uuid,
            "title": request.title,
            "company": request.company,
            "analysis_summary": {
                "requirements_count": len(analysis_result['requirements']),
                "responsibilities_count": len(analysis_result['responsibilities']),
                "preferred_qualifications_count": len(analysis_result['preferred_qualifications']),
                "benefits_count": len(analysis_result['benefits']),
                "skills_found": analysis_result['skills'],
                "experience_level": analysis_result['experience_level'],
                "education_requirements": analysis_result['education_requirements'],
                "confidence_score": analysis_result['analysis_confidence']
            }
        }
        
    except ValueError as e:
        logger.error(f"Invalid input for job analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing job: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze job")


@router.get("/")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    """List all analyzed jobs"""
    try:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        return [job.to_dict() for job in jobs]
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific job"""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")
