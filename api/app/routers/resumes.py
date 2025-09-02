"""
Resume management router
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging

from app.database import get_db
from app.models.resume import Resume, ResumeVersion
from app.services.storage import StorageService
from app.services.pdf_processor import PDFProcessor
from app.services.resume_parser import ResumeParser
from app.services.export_service import ExportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a resume"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Validate PDF
        pdf_processor = PDFProcessor()
        is_valid, error_message = await pdf_processor.validate_pdf(file_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Extract text from PDF
        extraction_result = await pdf_processor.extract_text_from_pdf(file_data)
        pdf_metadata = await pdf_processor.extract_metadata(file_data)
        
        # Parse resume content into structured data
        resume_parser = ResumeParser()
        parsed_data = await resume_parser.parse_resume(extraction_result["text"])
        
        # Upload to storage
        storage_service = StorageService()
        object_name = await storage_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            content_type="application/pdf",
            folder="resumes"
        )
        
        # Create resume record in database with parsed data
        resume = Resume(
            filename=file.filename,
            file_path=object_name,
            original_text=extraction_result["text"],
            contact_info=parsed_data["contact_info"],
            work_experience=parsed_data["work_experience"],
            education=parsed_data["education"],
            skills=parsed_data["skills"],
            certifications=parsed_data["certifications"],
            additional_sections=parsed_data["additional_sections"]
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        return {
            "message": "Resume uploaded and processed successfully",
            "resume_id": resume.id,
            "resume_uuid": resume.uuid,
            "filename": file.filename,
            "extraction_metadata": extraction_result["metadata"],
            "pdf_metadata": pdf_metadata,
            "text_length": len(extraction_result["text"]),
            "pages_processed": len(extraction_result["pages"]),
            "parsed_data": {
                "contact_info_found": bool(parsed_data["contact_info"]),
                "work_experiences_count": len(parsed_data["work_experience"]),
                "education_entries_count": len(parsed_data["education"]),
                "skills_count": len(parsed_data["skills"]),
                "certifications_count": len(parsed_data["certifications"]),
                "has_summary": bool(parsed_data.get("summary"))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload resume")


@router.get("/")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    """List all resumes"""
    try:
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()
        return [resume.to_dict() for resume in resumes]
        
    except Exception as e:
        logger.error(f"Error listing resumes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list resumes")


@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific resume"""
    try:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return resume.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to get resume")


@router.get("/{resume_id}/text")
async def get_resume_text(resume_id: int, db: AsyncSession = Depends(get_db)):
    """Get resume as formatted text for editing"""
    try:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Format the resume data as readable text
        text_parts = []
        
        # Header with contact info
        contact = resume.contact_info or {}
        if contact.get('name'):
            text_parts.append(contact['name'])
        
        contact_details = []
        if contact.get('email'):
            contact_details.append(contact['email'])
        if contact.get('phone'):
            contact_details.append(contact['phone'])
        if contact.get('location'):
            contact_details.append(contact['location'])
        
        if contact_details:
            text_parts.append(' | '.join(contact_details))
        
        # Professional Summary
        summary = resume.additional_sections.get('summary') if resume.additional_sections else None
        if summary:
            text_parts.extend(['', 'PROFESSIONAL SUMMARY', summary])
        
        # Work Experience
        if resume.work_experience:
            text_parts.extend(['', 'WORK EXPERIENCE'])
            for exp in resume.work_experience:
                exp_lines = []
                if exp.get('title') and exp.get('company'):
                    exp_lines.append(f"{exp['title']} - {exp['company']}")
                elif exp.get('title'):
                    exp_lines.append(exp['title'])
                
                if exp.get('start_date') or exp.get('end_date'):
                    dates = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
                    exp_lines.append(dates)
                
                if exp.get('responsibilities'):
                    for resp in exp['responsibilities']:
                        exp_lines.append(f"• {resp}")
                
                text_parts.extend(exp_lines)
                text_parts.append('')  # Add spacing between jobs
        
        # Education
        if resume.education:
            text_parts.extend(['', 'EDUCATION'])
            for edu in resume.education:
                edu_line = []
                if edu.get('degree'):
                    edu_line.append(edu['degree'])
                if edu.get('field'):
                    edu_line.append(f"in {edu['field']}")
                if edu.get('school'):
                    edu_line.append(f"- {edu['school']}")
                if edu.get('graduation_date'):
                    edu_line.append(f"({edu['graduation_date']})")
                
                if edu_line:
                    text_parts.append(' '.join(edu_line))
        
        # Skills
        if resume.skills:
            text_parts.extend(['', 'SKILLS'])
            # Group skills into lines for better readability
            skills_text = ', '.join(resume.skills)
            text_parts.append(skills_text)
        
        # Certifications
        if resume.certifications:
            text_parts.extend(['', 'CERTIFICATIONS'])
            for cert in resume.certifications:
                cert_line = cert.get('name', '')
                if cert.get('issuer'):
                    cert_line += f" - {cert['issuer']}"
                if cert.get('date'):
                    cert_line += f" ({cert['date']})"
                text_parts.append(cert_line)
        
        formatted_text = '\n'.join(text_parts)
        
        return {
            "resume_id": resume_id,
            "filename": resume.filename,
            "formatted_text": formatted_text,
            "original_text": resume.original_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume text: {e}")
        raise HTTPException(status_code=500, detail="Failed to get resume text")


@router.get("/{resume_id}/export")
async def export_resume(resume_id: int, format: str = "pdf", db: AsyncSession = Depends(get_db)):
    """Export resume in specified format"""
    if format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")
    
    try:
        # Get resume from database
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Prepare resume data for export
        resume_data = {
            'contact_info': resume.contact_info or {},
            'work_experience': resume.work_experience or [],
            'education': resume.education or [],
            'skills': resume.skills or [],
            'certifications': resume.certifications or [],
            'summary': resume.additional_sections.get('summary', '') if resume.additional_sections else '',
            'projects': resume.additional_sections.get('projects', []) if resume.additional_sections else []
        }
        
        # Export resume
        export_service = ExportService()
        
        if format == "pdf":
            filename, content = await export_service.export_resume_pdf(resume_data)
        else:  # docx
            filename, content = await export_service.export_resume_docx(resume_data)
        
        # Save exported file to storage
        object_name = await export_service.save_exported_resume(
            resume_id=resume_id,
            format_type=format,
            filename=filename,
            content=content
        )
        
        # Generate download URL
        storage_service = StorageService()
        download_url = await storage_service.get_presigned_url(object_name)
        
        return {
            "message": f"Resume exported successfully as {format.upper()}",
            "resume_id": resume_id,
            "format": format,
            "filename": filename,
            "download_url": download_url,
            "file_size": len(content),
            "object_name": object_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to export resume")
