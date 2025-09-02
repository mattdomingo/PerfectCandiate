"""
AI-powered matching engine using sentence transformers for semantic similarity
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Tuple, Optional
import logging
import json
import re
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Service for matching resumes with job requirements using AI"""
    
    def __init__(self):
        try:
            # Load pre-trained sentence transformer model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        # Weight factors for different sections
        self.section_weights = {
            'skills': 0.4,
            'experience': 0.3,
            'education': 0.2,
            'certifications': 0.1
        }
        
        # Skill matching thresholds
        self.similarity_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    async def match_resume_to_job(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a resume to a job posting and generate comprehensive analysis
        
        Args:
            resume_data: Structured resume data
            job_data: Structured job data
            
        Returns:
            Dictionary with matching results and suggestions
        """
        try:
            # Calculate individual section scores
            skills_match = await self._match_skills(resume_data, job_data)
            experience_match = await self._match_experience(resume_data, job_data)
            education_match = await self._match_education(resume_data, job_data)
            
            # Calculate overall match score
            overall_score = (
                skills_match['score'] * self.section_weights['skills'] +
                experience_match['score'] * self.section_weights['experience'] +
                education_match['score'] * self.section_weights['education']
            )
            
            # Generate detailed analysis
            gaps_analysis = await self._analyze_gaps(resume_data, job_data, skills_match, experience_match)
            strengths_analysis = await self._analyze_strengths(resume_data, job_data, skills_match, experience_match)
            keyword_matches = await self._analyze_keyword_matches(resume_data, job_data)
            requirements_coverage = await self._analyze_requirements_coverage(resume_data, job_data)
            
            # Generate improvement suggestions
            suggestions = await self._generate_suggestions(
                resume_data, job_data, gaps_analysis, skills_match, experience_match
            )
            
            return {
                'overall_match_score': round(overall_score, 3),
                'skills_match_score': round(skills_match['score'], 3),
                'experience_match_score': round(experience_match['score'], 3),
                'education_match_score': round(education_match['score'], 3),
                'matching_skills': skills_match['matches'],
                'missing_skills': skills_match['missing'],
                'gaps_analysis': gaps_analysis,
                'strengths_analysis': strengths_analysis,
                'requirements_coverage': requirements_coverage,
                'keyword_matches': keyword_matches,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Error in resume-job matching: {e}")
            raise
    
    async def _match_skills(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match skills between resume and job requirements"""
        try:
            resume_skills = self._extract_all_skills(resume_data)
            job_skills = self._extract_job_skills(job_data)
            
            if not resume_skills or not job_skills:
                return {
                    'score': 0.0,
                    'matches': [],
                    'missing': job_skills,
                    'details': 'Insufficient skill data for comparison'
                }
            
            # Encode skills using sentence transformer
            resume_embeddings = self.model.encode(resume_skills)
            job_embeddings = self.model.encode(job_skills)
            
            # Calculate similarity matrix
            similarity_matrix = np.dot(resume_embeddings, job_embeddings.T)
            
            matches = []
            missing = []
            
            for i, job_skill in enumerate(job_skills):
                max_similarity = np.max(similarity_matrix[:, i])
                best_match_idx = np.argmax(similarity_matrix[:, i])
                
                if max_similarity >= self.similarity_thresholds['low']:
                    matches.append({
                        'job_skill': job_skill,
                        'resume_skill': resume_skills[best_match_idx],
                        'similarity': float(max_similarity),
                        'confidence': self._get_confidence_level(max_similarity)
                    })
                else:
                    missing.append({
                        'skill': job_skill,
                        'best_partial_match': resume_skills[best_match_idx] if resume_skills else None,
                        'similarity': float(max_similarity)
                    })
            
            # Calculate overall skills score
            if job_skills:
                score = len(matches) / len(job_skills)
            else:
                score = 0.0
            
            return {
                'score': score,
                'matches': matches,
                'missing': missing,
                'total_job_skills': len(job_skills),
                'matched_skills': len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error matching skills: {e}")
            return {'score': 0.0, 'matches': [], 'missing': [], 'error': str(e)}
    
    async def _match_experience(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match work experience and responsibilities"""
        try:
            resume_experience = self._extract_experience_text(resume_data)
            job_requirements = self._extract_experience_requirements(job_data)
            
            if not resume_experience or not job_requirements:
                return {
                    'score': 0.0,
                    'matches': [],
                    'missing': job_requirements,
                    'details': 'Insufficient experience data for comparison'
                }
            
            # Encode experience descriptions
            resume_embeddings = self.model.encode(resume_experience)
            job_embeddings = self.model.encode(job_requirements)
            
            # Calculate similarities
            similarity_matrix = np.dot(resume_embeddings, job_embeddings.T)
            
            matches = []
            missing = []
            
            for i, job_req in enumerate(job_requirements):
                max_similarity = np.max(similarity_matrix[:, i])
                best_match_idx = np.argmax(similarity_matrix[:, i])
                
                if max_similarity >= self.similarity_thresholds['low']:
                    matches.append({
                        'job_requirement': job_req,
                        'resume_experience': resume_experience[best_match_idx],
                        'similarity': float(max_similarity),
                        'confidence': self._get_confidence_level(max_similarity)
                    })
                else:
                    missing.append({
                        'requirement': job_req,
                        'similarity': float(max_similarity)
                    })
            
            # Calculate experience score
            if job_requirements:
                score = len(matches) / len(job_requirements)
            else:
                score = 0.0
            
            return {
                'score': score,
                'matches': matches,
                'missing': missing,
                'total_requirements': len(job_requirements),
                'matched_requirements': len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error matching experience: {e}")
            return {'score': 0.0, 'matches': [], 'missing': [], 'error': str(e)}
    
    async def _match_education(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match education requirements"""
        try:
            resume_education = resume_data.get('education', [])
            job_education_reqs = job_data.get('education_requirements', [])
            
            if not job_education_reqs:
                return {'score': 1.0, 'matches': [], 'missing': [], 'details': 'No education requirements specified'}
            
            if not resume_education:
                return {
                    'score': 0.0,
                    'matches': [],
                    'missing': job_education_reqs,
                    'details': 'No education information in resume'
                }
            
            # Simple education matching based on degree levels
            education_hierarchy = {
                'high school': 1,
                'associate': 2,
                'bachelor': 3,
                'master': 4,
                'phd': 5,
                'doctorate': 5
            }
            
            # Get highest education level from resume
            max_resume_level = 0
            for edu in resume_education:
                degree = edu.get('degree', '').lower()
                for level_name, level_value in education_hierarchy.items():
                    if level_name in degree:
                        max_resume_level = max(max_resume_level, level_value)
            
            # Check against job requirements
            matches = []
            missing = []
            
            for req in job_education_reqs:
                req_lower = req.lower()
                req_level = 0
                for level_name, level_value in education_hierarchy.items():
                    if level_name in req_lower:
                        req_level = level_value
                        break
                
                if max_resume_level >= req_level:
                    matches.append({
                        'requirement': req,
                        'satisfied': True,
                        'resume_level': max_resume_level,
                        'required_level': req_level
                    })
                else:
                    missing.append({
                        'requirement': req,
                        'resume_level': max_resume_level,
                        'required_level': req_level
                    })
            
            # Calculate education score
            if job_education_reqs:
                score = len(matches) / len(job_education_reqs)
            else:
                score = 1.0
            
            return {
                'score': score,
                'matches': matches,
                'missing': missing,
                'highest_resume_level': max_resume_level
            }
            
        except Exception as e:
            logger.error(f"Error matching education: {e}")
            return {'score': 0.0, 'matches': [], 'missing': [], 'error': str(e)}
    
    async def _analyze_gaps(self, resume_data: Dict[str, Any], job_data: Dict[str, Any], 
                           skills_match: Dict[str, Any], experience_match: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gaps between resume and job requirements"""
        gaps = {
            'critical_missing_skills': [],
            'experience_gaps': [],
            'improvement_areas': [],
            'priority_level': 'medium'
        }
        
        # Identify critical missing skills
        for missing_skill in skills_match.get('missing', []):
            if missing_skill.get('similarity', 0) < self.similarity_thresholds['low']:
                gaps['critical_missing_skills'].append({
                    'skill': missing_skill['skill'],
                    'importance': 'high',
                    'suggestion': f"Consider learning {missing_skill['skill']}"
                })
        
        # Identify experience gaps
        for missing_exp in experience_match.get('missing', []):
            gaps['experience_gaps'].append({
                'requirement': missing_exp['requirement'],
                'suggestion': f"Gain experience in: {missing_exp['requirement']}"
            })
        
        # Determine priority level
        critical_gaps = len(gaps['critical_missing_skills']) + len(gaps['experience_gaps'])
        if critical_gaps > 5:
            gaps['priority_level'] = 'high'
        elif critical_gaps < 2:
            gaps['priority_level'] = 'low'
        
        return gaps
    
    async def _analyze_strengths(self, resume_data: Dict[str, Any], job_data: Dict[str, Any],
                                skills_match: Dict[str, Any], experience_match: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume strengths relative to job requirements"""
        strengths = {
            'strong_skill_matches': [],
            'relevant_experience': [],
            'competitive_advantages': []
        }
        
        # Identify strong skill matches
        for match in skills_match.get('matches', []):
            if match.get('similarity', 0) >= self.similarity_thresholds['high']:
                strengths['strong_skill_matches'].append({
                    'skill': match['job_skill'],
                    'match_quality': 'excellent',
                    'confidence': match.get('confidence', 'high')
                })
        
        # Identify relevant experience
        for match in experience_match.get('matches', []):
            if match.get('similarity', 0) >= self.similarity_thresholds['medium']:
                strengths['relevant_experience'].append({
                    'requirement': match['job_requirement'],
                    'experience': match['resume_experience'],
                    'relevance': 'high'
                })
        
        return strengths
    
    async def _analyze_keyword_matches(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze keyword matches between resume and job"""
        job_keywords = job_data.get('key_keywords', [])
        resume_text = self._get_resume_text(resume_data)
        
        if not job_keywords or not resume_text:
            return {'matches': [], 'coverage': 0.0, 'missing_keywords': job_keywords}
        
        resume_lower = resume_text.lower()
        matches = []
        missing = []
        
        for keyword in job_keywords:
            if keyword.lower() in resume_lower:
                matches.append({
                    'keyword': keyword,
                    'found': True,
                    'context': self._get_keyword_context(resume_text, keyword)
                })
            else:
                missing.append(keyword)
        
        coverage = len(matches) / len(job_keywords) if job_keywords else 0.0
        
        return {
            'matches': matches,
            'missing_keywords': missing,
            'coverage': round(coverage, 3),
            'total_keywords': len(job_keywords)
        }
    
    async def _analyze_requirements_coverage(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well resume covers job requirements"""
        requirements = job_data.get('requirements', [])
        if not requirements:
            return {'coverage': [], 'overall_coverage': 1.0}
        
        resume_text = self._get_resume_text(resume_data)
        if not resume_text:
            return {'coverage': [], 'overall_coverage': 0.0}
        
        # Encode requirements and resume text
        req_embeddings = self.model.encode(requirements)
        resume_embedding = self.model.encode([resume_text])
        
        # Calculate similarities
        similarities = np.dot(req_embeddings, resume_embedding.T).flatten()
        
        coverage = []
        total_coverage = 0
        
        for i, requirement in enumerate(requirements):
            similarity = float(similarities[i])
            coverage_level = self._get_coverage_level(similarity)
            
            coverage.append({
                'requirement': requirement,
                'coverage_score': similarity,
                'coverage_level': coverage_level,
                'recommendation': self._get_coverage_recommendation(requirement, coverage_level)
            })
            
            total_coverage += similarity
        
        overall_coverage = total_coverage / len(requirements) if requirements else 0.0
        
        return {
            'coverage': coverage,
            'overall_coverage': round(overall_coverage, 3)
        }
    
    async def _generate_suggestions(self, resume_data: Dict[str, Any], job_data: Dict[str, Any],
                                  gaps_analysis: Dict[str, Any], skills_match: Dict[str, Any],
                                  experience_match: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered suggestions for resume improvement"""
        suggestions = []
        
        # Skills-based suggestions
        for missing_skill in skills_match.get('missing', [])[:5]:  # Top 5 missing skills
            suggestions.append({
                'type': 'add',
                'section': 'skills',
                'priority': 5 if missing_skill.get('similarity', 0) < 0.3 else 3,
                'original_content': None,
                'suggested_content': missing_skill['skill'],
                'reasoning': f"Add '{missing_skill['skill']}' to better match job requirements",
                'estimated_impact': 0.15,
                'confidence_score': 0.8
            })
        
        # Experience-based suggestions
        for missing_exp in experience_match.get('missing', [])[:3]:  # Top 3 missing experiences
            suggestions.append({
                'type': 'add',
                'section': 'experience',
                'priority': 4,
                'original_content': None,
                'suggested_content': f"Highlight experience related to: {missing_exp['requirement']}",
                'reasoning': f"Emphasize any experience you have with {missing_exp['requirement']}",
                'estimated_impact': 0.2,
                'confidence_score': 0.7
            })
        
        # Keyword optimization suggestions
        job_keywords = job_data.get('key_keywords', [])
        resume_text = self._get_resume_text(resume_data).lower()
        
        for keyword in job_keywords[:3]:  # Top 3 keywords
            if keyword.lower() not in resume_text:
                suggestions.append({
                    'type': 'modify',
                    'section': 'experience',
                    'priority': 2,
                    'original_content': None,
                    'suggested_content': f"Incorporate the keyword '{keyword}' naturally in your experience descriptions",
                    'reasoning': f"Including '{keyword}' will improve ATS compatibility and keyword matching",
                    'estimated_impact': 0.1,
                    'confidence_score': 0.9
                })
        
        # Sort suggestions by priority and impact
        suggestions.sort(key=lambda x: (x['priority'], x['estimated_impact']), reverse=True)
        
        return suggestions
    
    def _extract_all_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        """Extract all skills from resume data"""
        skills = []
        
        # Direct skills
        if resume_data.get('skills'):
            skills.extend(resume_data['skills'])
        
        # Skills from experience descriptions
        for exp in resume_data.get('work_experience', []):
            responsibilities = exp.get('responsibilities', [])
            skills.extend(self._extract_skills_from_text(' '.join(responsibilities)))
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_job_skills(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract skills from job requirements"""
        skills = []
        
        # Skills from structured data
        job_skills = job_data.get('skills', {})
        for category, skill_list in job_skills.items():
            skills.extend(skill_list)
        
        # Skills from requirements
        requirements = job_data.get('requirements', [])
        for req in requirements:
            skills.extend(self._extract_skills_from_text(req))
        
        return list(set(skills))
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from text using simple pattern matching"""
        # This is a simplified implementation - could be enhanced with more sophisticated NLP
        common_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'node.js', 'sql',
            'aws', 'docker', 'kubernetes', 'git', 'api', 'restful', 'agile',
            'machine learning', 'data analysis', 'project management'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience_text(self, resume_data: Dict[str, Any]) -> List[str]:
        """Extract experience descriptions from resume"""
        experience_texts = []
        
        for exp in resume_data.get('work_experience', []):
            # Combine title, company, and responsibilities
            exp_text = f"{exp.get('title', '')} {exp.get('company', '')} "
            exp_text += ' '.join(exp.get('responsibilities', []))
            experience_texts.append(exp_text.strip())
        
        return experience_texts
    
    def _extract_experience_requirements(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract experience requirements from job data"""
        requirements = []
        
        # Requirements section
        requirements.extend(job_data.get('requirements', []))
        
        # Responsibilities (what they'll be doing)
        requirements.extend(job_data.get('responsibilities', []))
        
        return requirements
    
    def _get_resume_text(self, resume_data: Dict[str, Any]) -> str:
        """Get combined text from resume data"""
        text_parts = []
        
        # Add skills
        if resume_data.get('skills'):
            text_parts.append(' '.join(resume_data['skills']))
        
        # Add experience
        for exp in resume_data.get('work_experience', []):
            text_parts.append(f"{exp.get('title', '')} {exp.get('company', '')}")
            text_parts.extend(exp.get('responsibilities', []))
        
        # Add education
        for edu in resume_data.get('education', []):
            text_parts.append(f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('school', '')}")
        
        return ' '.join(text_parts)
    
    def _get_confidence_level(self, similarity: float) -> str:
        """Convert similarity score to confidence level"""
        if similarity >= self.similarity_thresholds['high']:
            return 'high'
        elif similarity >= self.similarity_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _get_coverage_level(self, similarity: float) -> str:
        """Convert similarity score to coverage level"""
        if similarity >= 0.7:
            return 'excellent'
        elif similarity >= 0.5:
            return 'good'
        elif similarity >= 0.3:
            return 'partial'
        else:
            return 'poor'
    
    def _get_coverage_recommendation(self, requirement: str, coverage_level: str) -> str:
        """Generate recommendation based on coverage level"""
        if coverage_level == 'poor':
            return f"Consider adding experience or skills related to: {requirement}"
        elif coverage_level == 'partial':
            return f"Expand on your experience with: {requirement}"
        elif coverage_level == 'good':
            return f"Highlight your experience with: {requirement}"
        else:
            return f"Great match for: {requirement}"
    
    def _get_keyword_context(self, text: str, keyword: str) -> str:
        """Get context around a keyword in text"""
        # Simple context extraction - could be enhanced
        keyword_index = text.lower().find(keyword.lower())
        if keyword_index == -1:
            return ""
        
        start = max(0, keyword_index - 50)
        end = min(len(text), keyword_index + len(keyword) + 50)
        
        return text[start:end].strip()
