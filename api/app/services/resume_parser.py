"""
Resume parsing service using spaCy for structured data extraction
"""
import spacy
import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing resume text into structured data"""
    
    def __init__(self):
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
            raise
        
        # Define patterns for different sections
        self.section_patterns = {
            'contact': [
                r'contact\s+information?',
                r'personal\s+details?',
                r'contact\s+details?'
            ],
            'experience': [
                r'work\s+experience',
                r'professional\s+experience',
                r'employment\s+history',
                r'career\s+history',
                r'experience',
                r'work\s+history'
            ],
            'education': [
                r'education',
                r'academic\s+background',
                r'qualifications?',
                r'degrees?'
            ],
            'skills': [
                r'skills?',
                r'technical\s+skills?',
                r'core\s+competencies',
                r'areas\s+of\s+expertise',
                r'technologies?'
            ],
            'certifications': [
                r'certifications?',
                r'certificates?',
                r'professional\s+certifications?',
                r'licenses?'
            ],
            'projects': [
                r'projects?',
                r'key\s+projects?',
                r'notable\s+projects?'
            ],
            'summary': [
                r'summary',
                r'profile',
                r'objective',
                r'professional\s+summary',
                r'career\s+objective'
            ]
        }
        
        # Email pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone pattern
        self.phone_pattern = re.compile(r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})'),  # MM/DD/YYYY
            re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})'),  # YYYY-MM-DD
            re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', re.IGNORECASE),  # Mon YYYY
            re.compile(r'(\d{4})\s*-\s*(\d{4})'),  # YYYY - YYYY
            re.compile(r'(\d{4})\s*-\s*Present', re.IGNORECASE),  # YYYY - Present
        ]
    
    async def parse_resume(self, text: str) -> Dict[str, Any]:
        """
        Parse resume text into structured data
        
        Args:
            text: Resume text content
            
        Returns:
            Dictionary with structured resume data
        """
        try:
            # Split text into sections
            sections = self._split_into_sections(text)
            
            # Extract structured data
            result = {
                'contact_info': self._extract_contact_info(text, sections),
                'work_experience': self._extract_work_experience(sections.get('experience', '')),
                'education': self._extract_education(sections.get('education', '')),
                'skills': self._extract_skills(sections.get('skills', '')),
                'certifications': self._extract_certifications(sections.get('certifications', '')),
                'summary': self._extract_summary(sections.get('summary', '')),
                'projects': self._extract_projects(sections.get('projects', '')),
                'additional_sections': {
                    section: content for section, content in sections.items()
                    if section not in ['contact', 'experience', 'education', 'skills', 'certifications', 'summary', 'projects']
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            raise
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume text into sections based on headers"""
        sections = {}
        current_section = 'unknown'
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                current_content.append('')
                continue
            
            # Check if this line is a section header
            section_found = None
            for section_name, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line_clean, re.IGNORECASE):
                        section_found = section_name
                        break
                if section_found:
                    break
            
            if section_found:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_found
                current_content = []
            else:
                current_content.append(line_clean)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_contact_info(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract contact information"""
        contact_info = {}
        
        # Look for contact info in the beginning of the document or contact section
        search_text = text[:1000]  # First 1000 characters
        if 'contact' in sections:
            search_text += ' ' + sections['contact']
        
        # Extract email
        email_matches = self.email_pattern.findall(search_text)
        if email_matches:
            contact_info['email'] = email_matches[0]
        
        # Extract phone
        phone_matches = self.phone_pattern.findall(search_text)
        if phone_matches:
            # Format phone number
            phone = phone_matches[0]
            formatted_phone = f"({phone[1]}) {phone[2]}-{phone[3]}"
            contact_info['phone'] = formatted_phone
        
        # Extract name (usually first non-empty line)
        lines = text.split('\n')
        for line in lines:
            line_clean = line.strip()
            if line_clean and len(line_clean.split()) <= 4:  # Assume name is 1-4 words
                # Use spaCy to check if it contains person names
                doc = self.nlp(line_clean)
                if any(ent.label_ == "PERSON" for ent in doc.ents):
                    contact_info['name'] = line_clean
                    break
        
        # Extract location (look for city, state patterns)
        location_patterns = [
            re.compile(r'([A-Za-z\s]+),\s*([A-Z]{2})\s*\d{5}'),  # City, ST ZIP
            re.compile(r'([A-Za-z\s]+),\s*([A-Z]{2})'),  # City, ST
        ]
        
        for pattern in location_patterns:
            matches = pattern.findall(search_text)
            if matches:
                city, state = matches[0]
                contact_info['location'] = f"{city.strip()}, {state}"
                break
        
        return contact_info
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience entries"""
        if not text:
            return []
        
        experiences = []
        
        # Split by common job separators
        job_blocks = re.split(r'\n\s*\n', text)
        
        for block in job_blocks:
            if not block.strip():
                continue
            
            experience = self._parse_job_entry(block)
            if experience:
                experiences.append(experience)
        
        return experiences
    
    def _parse_job_entry(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single job entry"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            return None
        
        experience = {
            'title': '',
            'company': '',
            'location': '',
            'start_date': '',
            'end_date': '',
            'description': '',
            'responsibilities': []
        }
        
        # First line often contains title and/or company
        first_line = lines[0]
        
        # Look for title patterns (often in caps or followed by "at")
        title_match = re.search(r'^([^,|]+?)(?:\s+at\s+|\s+[-|]\s+|,\s*)(.+)', first_line, re.IGNORECASE)
        if title_match:
            experience['title'] = title_match.group(1).strip()
            experience['company'] = title_match.group(2).strip()
        else:
            experience['title'] = first_line
        
        # Look for dates in the block
        date_info = self._extract_dates_from_text(' '.join(lines))
        if date_info:
            experience.update(date_info)
        
        # Extract responsibilities (lines starting with bullet points or action verbs)
        responsibilities = []
        for line in lines[1:]:
            if re.match(r'^[•\-\*\+]\s*', line) or self._starts_with_action_verb(line):
                responsibilities.append(line.strip('•-*+ ').strip())
        
        experience['responsibilities'] = responsibilities
        experience['description'] = '\n'.join(lines[1:])
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education entries"""
        if not text:
            return []
        
        education_entries = []
        
        # Split by degree/school separators
        edu_blocks = re.split(r'\n\s*\n', text)
        
        for block in edu_blocks:
            if not block.strip():
                continue
            
            education = self._parse_education_entry(block)
            if education:
                education_entries.append(education)
        
        return education_entries
    
    def _parse_education_entry(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single education entry"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            return None
        
        education = {
            'degree': '',
            'field': '',
            'school': '',
            'location': '',
            'graduation_date': '',
            'gpa': ''
        }
        
        text_block = ' '.join(lines)
        
        # Look for degree patterns
        degree_patterns = [
            r'(Bachelor|Master|PhD|B\.A\.|B\.S\.|M\.A\.|M\.S\.|MBA|Ph\.D\.)\s*(of\s*|in\s*)?([^,\n]+)',
            r'(Associate|Diploma|Certificate)\s*(of\s*|in\s*)?([^,\n]+)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, text_block, re.IGNORECASE)
            if match:
                education['degree'] = match.group(1)
                education['field'] = match.group(3).strip() if match.group(3) else ''
                break
        
        # Look for school names (often capitalized)
        doc = self.nlp(text_block)
        for ent in doc.ents:
            if ent.label_ == "ORG" and any(word in ent.text.lower() for word in ['university', 'college', 'institute', 'school']):
                education['school'] = ent.text
                break
        
        # Extract dates
        date_info = self._extract_dates_from_text(text_block)
        if date_info and date_info.get('end_date'):
            education['graduation_date'] = date_info['end_date']
        
        # Look for GPA
        gpa_match = re.search(r'GPA[:\s]*([0-9\.]+)', text_block, re.IGNORECASE)
        if gpa_match:
            education['gpa'] = gpa_match.group(1)
        
        return education
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from skills section"""
        if not text:
            return []
        
        # Split by common separators
        skills = re.split(r'[,;|\n•\-\*\+]', text)
        
        # Clean and filter skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            if skill and len(skill) > 1 and len(skill) < 50:  # Reasonable skill length
                cleaned_skills.append(skill)
        
        return cleaned_skills
    
    def _extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract certifications"""
        if not text:
            return []
        
        certifications = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            cert = {
                'name': line,
                'issuer': '',
                'date': ''
            }
            
            # Look for issuer patterns
            issuer_match = re.search(r'from\s+([^,\n]+)', line, re.IGNORECASE)
            if issuer_match:
                cert['issuer'] = issuer_match.group(1).strip()
            
            # Extract dates
            date_info = self._extract_dates_from_text(line)
            if date_info and date_info.get('end_date'):
                cert['date'] = date_info['end_date']
            
            certifications.append(cert)
        
        return certifications
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary"""
        return text.strip() if text else ''
    
    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract project information"""
        if not text:
            return []
        
        projects = []
        project_blocks = re.split(r'\n\s*\n', text)
        
        for block in project_blocks:
            if not block.strip():
                continue
            
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if not lines:
                continue
            
            project = {
                'name': lines[0],
                'description': '\n'.join(lines[1:]) if len(lines) > 1 else '',
                'technologies': []
            }
            
            projects.append(project)
        
        return projects
    
    def _extract_dates_from_text(self, text: str) -> Optional[Dict[str, str]]:
        """Extract start and end dates from text"""
        for pattern in self.date_patterns:
            matches = pattern.findall(text)
            if matches:
                if len(matches) >= 2:
                    return {
                        'start_date': str(matches[0]),
                        'end_date': str(matches[1])
                    }
                elif len(matches) == 1:
                    # Check if it's a range or single date
                    match_text = str(matches[0])
                    if 'present' in match_text.lower():
                        return {
                            'start_date': match_text.replace(' - Present', '').replace(' - present', ''),
                            'end_date': 'Present'
                        }
                    else:
                        return {
                            'start_date': '',
                            'end_date': match_text
                        }
        
        return None
    
    def _starts_with_action_verb(self, text: str) -> bool:
        """Check if text starts with an action verb"""
        action_verbs = [
            'developed', 'managed', 'led', 'created', 'implemented', 'designed',
            'improved', 'increased', 'reduced', 'achieved', 'established',
            'coordinated', 'supervised', 'maintained', 'analyzed', 'optimized'
        ]
        
        first_word = text.split()[0].lower() if text.split() else ''
        return first_word in action_verbs
