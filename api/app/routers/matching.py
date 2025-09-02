"""
Resume-job matching router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.database import get_db
from app.models.matching import MatchingResult, Suggestion
from app.models.resume import Resume
from app.models.job import Job
from app.services.matching_engine import MatchingEngine

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchingRequest(BaseModel):
    """Request model for resume-job matching"""
    resume_id: int
    job_id: int


class SuggestionResponse(BaseModel):
    """Response model for suggestion updates"""
    is_accepted: bool
    user_notes: Optional[str] = None


@router.post("/compare")
async def compare_resume_job(
    request: MatchingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compare a resume with a job posting"""
    try:
        # Verify resume exists
        resume_result = await db.execute(select(Resume).where(Resume.id == request.resume_id))
        resume = resume_result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Verify job exists
        job_result = await db.execute(select(Job).where(Job.id == request.job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Prepare data for matching engine
        resume_data = {
            'skills': resume.skills or [],
            'work_experience': resume.work_experience or [],
            'education': resume.education or [],
            'certifications': resume.certifications or [],
            'contact_info': resume.contact_info or {},
            'additional_sections': resume.additional_sections or {}
        }
        
        job_data = {
            'requirements': job.requirements or [],
            'preferred_qualifications': job.preferred_qualifications or [],
            'responsibilities': job.responsibilities or [],
            'skills': {},  # Job skills will be extracted from requirements
            'key_keywords': job.key_keywords or [],
            'education_requirements': []  # Will be extracted from requirements
        }
        
        # Perform AI-powered matching
        matching_engine = MatchingEngine()
        matching_result = await matching_engine.match_resume_to_job(resume_data, job_data)
        
        # Store matching results in database
        db_matching_result = MatchingResult(
            resume_id=request.resume_id,
            job_id=request.job_id,
            overall_match_score=matching_result['overall_match_score'],
            skills_match_score=matching_result['skills_match_score'],
            experience_match_score=matching_result['experience_match_score'],
            education_match_score=matching_result['education_match_score'],
            matching_skills=matching_result['matching_skills'],
            missing_skills=matching_result['missing_skills'],
            gaps_analysis=matching_result['gaps_analysis'],
            strengths_analysis=matching_result['strengths_analysis'],
            requirements_coverage=matching_result['requirements_coverage'],
            keyword_matches=matching_result['keyword_matches']
        )
        
        db.add(db_matching_result)
        await db.commit()
        await db.refresh(db_matching_result)
        
        # Store suggestions
        for suggestion_data in matching_result['suggestions']:
            suggestion = Suggestion(
                matching_result_id=db_matching_result.id,
                suggestion_type=suggestion_data['type'],
                section=suggestion_data['section'],
                priority=suggestion_data['priority'],
                original_content=suggestion_data['original_content'],
                suggested_content=suggestion_data['suggested_content'],
                reasoning=suggestion_data['reasoning'],
                estimated_impact=suggestion_data['estimated_impact'],
                confidence_score=suggestion_data['confidence_score']
            )
            db.add(suggestion)
        
        await db.commit()
        
        return {
            "message": "Resume and job comparison completed successfully",
            "matching_result_id": db_matching_result.id,
            "matching_result_uuid": db_matching_result.uuid,
            "resume_id": request.resume_id,
            "job_id": request.job_id,
            "resume_filename": resume.filename,
            "job_title": job.title,
            "summary": {
                "overall_match_score": matching_result['overall_match_score'],
                "skills_match_score": matching_result['skills_match_score'],
                "experience_match_score": matching_result['experience_match_score'],
                "education_match_score": matching_result['education_match_score'],
                "suggestions_count": len(matching_result['suggestions']),
                "missing_skills_count": len(matching_result['missing_skills']),
                "strengths_found": len(matching_result['strengths_analysis'].get('strong_skill_matches', []))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing resume and job: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare resume and job")


@router.get("/results/{matching_id}")
async def get_matching_result(matching_id: int, db: AsyncSession = Depends(get_db)):
    """Get matching results for a specific comparison"""
    try:
        result = await db.execute(
            select(MatchingResult).where(MatchingResult.id == matching_id)
        )
        matching_result = result.scalar_one_or_none()
        
        if not matching_result:
            raise HTTPException(status_code=404, detail="Matching result not found")
        
        return matching_result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matching result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get matching result")


@router.get("/results/{matching_id}/suggestions")
async def get_suggestions(matching_id: int, db: AsyncSession = Depends(get_db)):
    """Get suggestions for a specific matching result"""
    try:
        result = await db.execute(
            select(Suggestion)
            .where(Suggestion.matching_result_id == matching_id)
            .order_by(Suggestion.priority.desc(), Suggestion.confidence_score.desc())
        )
        suggestions = result.scalars().all()
        
        return [suggestion.to_dict() for suggestion in suggestions]
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.put("/suggestions/{suggestion_id}")
async def update_suggestion(
    suggestion_id: int,
    response: SuggestionResponse,
    db: AsyncSession = Depends(get_db)
):
    """Update a suggestion with user response"""
    try:
        result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        # TODO: Implement suggestion update logic
        # TODO: Apply changes to resume if accepted
        
        return {
            "message": "Suggestion update functionality will be implemented in next phase",
            "suggestion_id": suggestion_id,
            "is_accepted": response.is_accepted,
            "user_notes": response.user_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to update suggestion")
