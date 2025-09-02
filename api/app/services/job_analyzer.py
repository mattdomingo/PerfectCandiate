"""
Job analysis service for processing job descriptions and extracting requirements
"""
import spacy
import trafilatura
import requests
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class JobAnalyzer:
    """Service for analyzing job postings and extracting structured information"""
    
    def __init__(self):
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
            raise
        
        # Common job section patterns
        self.section_patterns = {
            'requirements': [
                r'requirements?',
                r'qualifications?',
                r'must\s+have',
                r'required\s+skills?',
                r'essential\s+skills?',
                r'minimum\s+qualifications?'
            ],
            'preferred': [
                r'preferred\s+qualifications?',
                r'nice\s+to\s+have',
                r'preferred\s+skills?',
                r'bonus\s+points?',
                r'additional\s+qualifications?',
                r'desired\s+qualifications?'
            ],
            'responsibilities': [
                r'responsibilities',
                r'duties',
                r'what\s+you.ll\s+do',
                r'job\s+description',
                r'role\s+responsibilities',
                r'key\s+responsibilities'
            ],
            'benefits': [
                r'benefits?',
                r'what\s+we\s+offer',
                r'perks?',
                r'compensation',
                r'package'
            ]
        }
        
        # Common skill keywords for different categories
        self.skill_categories = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
                'fastapi', 'laravel', 'rails', 'nodejs', 'nextjs', 'gatsby'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'dynamodb', 'cassandra', 'sqlite', 'oracle', 'sql server'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'docker',
                'terraform', 'jenkins', 'gitlab', 'github actions'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'slack', 'figma', 'sketch',
                'photoshop', 'illustrator', 'tableau', 'power bi'
            ]
        }
        
        # Experience level patterns
        self.experience_patterns = [
            (r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', 'years'),
            (r'entry\s+level', '0-1 years'),
            (r'junior', '1-3 years'),
            (r'mid\s*-?\s*level', '3-5 years'),
            (r'senior', '5+ years'),
            (r'lead', '7+ years'),
            (r'principal', '10+ years')
        ]
        
        # Education level patterns
        self.education_patterns = [
            r"bachelor'?s?\s+degree",
            r"master'?s?\s+degree",
            r"phd",
            r"doctorate",
            r"associate'?s?\s+degree",
            r"high\s+school"
        ]
    
    async def analyze_job_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract and analyze job posting from URL
        
        Args:
            url: Job posting URL
            
        Returns:
            Dictionary with analyzed job information
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL provided")
            
            # Extract content from URL
            job_text = await self._extract_content_from_url(url)
            if not job_text:
                raise ValueError("Could not extract content from URL")
            
            # Analyze the extracted text
            analysis_result = await self.analyze_job_text(job_text)
            analysis_result['source_url'] = url
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing job from URL {url}: {e}")
            raise
    
    async def analyze_job_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze job description text and extract structured information
        
        Args:
            text: Job description text
            
        Returns:
            Dictionary with analyzed job information
        """
        try:
            # Clean the text
            cleaned_text = self._clean_job_text(text)
            
            # Split into sections
            sections = self._split_job_into_sections(cleaned_text)
            
            # Extract structured information
            result = {
                'original_text': text,
                'cleaned_text': cleaned_text,
                'sections': sections,
                'requirements': self._extract_requirements(sections),
                'preferred_qualifications': self._extract_preferred_qualifications(sections),
                'responsibilities': self._extract_responsibilities(sections),
                'benefits': self._extract_benefits(sections),
                'skills': self._extract_skills(cleaned_text),
                'experience_level': self._extract_experience_level(cleaned_text),
                'education_requirements': self._extract_education_requirements(cleaned_text),
                'salary_range': self._extract_salary_range(cleaned_text),
                'location': self._extract_location(cleaned_text),
                'company_info': self._extract_company_info(cleaned_text),
                'key_keywords': self._extract_key_keywords(cleaned_text),
                'analysis_confidence': self._calculate_confidence_score(sections)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing job text: {e}")
            raise
    
    async def _extract_content_from_url(self, url: str) -> Optional[str]:
        """Extract text content from job posting URL"""
        try:
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Download the page
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Extract main content using trafilatura
            extracted_text = trafilatura.extract(response.text)
            
            if not extracted_text:
                # Fallback: try to extract from raw HTML
                extracted_text = trafilatura.extract(response.text, include_comments=False, include_tables=True)
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting content from URL: {e}")
            return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if the URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _clean_job_text(self, text: str) -> str:
        """Clean and normalize job description text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
        
        # Remove special characters that don't add value
        text = re.sub(r'[^\w\s\-.,;:()\[\]/$%+&]', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _split_job_into_sections(self, text: str) -> Dict[str, str]:
        """Split job description into sections"""
        sections = {}
        current_section = 'general'
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
    
    def _extract_requirements(self, sections: Dict[str, str]) -> List[str]:
        """Extract required qualifications"""
        requirements_text = sections.get('requirements', '') + '\n' + sections.get('general', '')
        return self._extract_bullet_points(requirements_text)
    
    def _extract_preferred_qualifications(self, sections: Dict[str, str]) -> List[str]:
        """Extract preferred qualifications"""
        preferred_text = sections.get('preferred', '')
        return self._extract_bullet_points(preferred_text)
    
    def _extract_responsibilities(self, sections: Dict[str, str]) -> List[str]:
        """Extract job responsibilities"""
        responsibilities_text = sections.get('responsibilities', '')
        return self._extract_bullet_points(responsibilities_text)
    
    def _extract_benefits(self, sections: Dict[str, str]) -> List[str]:
        """Extract benefits and perks"""
        benefits_text = sections.get('benefits', '')
        return self._extract_bullet_points(benefits_text)
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        if not text:
            return []
        
        # Look for bullet points
        bullet_patterns = [
            r'^[•\-\*\+]\s*(.+)$',
            r'^\d+\.\s*(.+)$',
            r'^[a-zA-Z]\.\s*(.+)$'
        ]
        
        bullet_points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    bullet_points.append(match.group(1).strip())
                    break
            else:
                # If no bullet pattern, but line seems like a requirement/responsibility
                if len(line) > 20 and any(word in line.lower() for word in ['experience', 'knowledge', 'skill', 'ability', 'responsible', 'manage', 'develop']):
                    bullet_points.append(line)
        
        return bullet_points
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract and categorize technical skills"""
        text_lower = text.lower()
        skills = {}
        
        for category, skill_list in self.skill_categories.items():
            found_skills = []
            for skill in skill_list:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
            
            if found_skills:
                skills[category] = found_skills
        
        return skills
    
    def _extract_experience_level(self, text: str) -> Dict[str, Any]:
        """Extract experience level requirements"""
        experience_info = {
            'minimum_years': None,
            'level': None,
            'details': []
        }
        
        for pattern, description in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], str) and matches[0].isdigit():
                    experience_info['minimum_years'] = int(matches[0])
                experience_info['level'] = description
                experience_info['details'].append(f"{matches[0]} years" if isinstance(matches[0], str) and matches[0].isdigit() else description)
        
        return experience_info
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements"""
        education_reqs = []
        
        for pattern in self.education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                education_reqs.extend(matches)
        
        return list(set(education_reqs))  # Remove duplicates
    
    def _extract_salary_range(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract salary information"""
        # Common salary patterns
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[-–]\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $50,000 - $75,000
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+year|annually|/year)',  # $50,000 per year
            r'(\d{1,3}(?:,\d{3})*)\s*[-–]\s*(\d{1,3}(?:,\d{3})*)\s*k',  # 50-75k
        ]
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches[0]) == 2:  # Range
                    return {
                        'min': matches[0][0].replace(',', ''),
                        'max': matches[0][1].replace(',', ''),
                        'type': 'range'
                    }
                else:  # Single value
                    return {
                        'value': matches[0].replace(',', ''),
                        'type': 'fixed'
                    }
        
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract job location"""
        # Use spaCy to find location entities
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity or location
                locations.append(ent.text)
        
        # Look for remote work mentions
        remote_patterns = [
            r'remote',
            r'work\s+from\s+home',
            r'distributed\s+team',
            r'anywhere'
        ]
        
        for pattern in remote_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                locations.append("Remote")
                break
        
        return ', '.join(list(set(locations))) if locations else None
    
    def _extract_company_info(self, text: str) -> Dict[str, Any]:
        """Extract company information"""
        doc = self.nlp(text)
        companies = []
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                companies.append(ent.text)
        
        return {
            'mentioned_companies': list(set(companies)),
            'likely_company': companies[0] if companies else None
        }
    
    def _extract_key_keywords(self, text: str) -> List[str]:
        """Extract important keywords using TF-IDF-like approach"""
        # Simple keyword extraction based on frequency and importance
        doc = self.nlp(text.lower())
        
        # Filter out stop words and get important tokens
        keywords = []
        for token in doc:
            if (token.is_alpha and 
                not token.is_stop and 
                len(token.text) > 2 and
                token.pos_ in ['NOUN', 'ADJ', 'PROPN']):
                keywords.append(token.text)
        
        # Count frequency
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Return top keywords
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, freq in sorted_keywords[:20]]
    
    def _calculate_confidence_score(self, sections: Dict[str, str]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0
        max_score = 5.0
        
        # Check if we found key sections
        if 'requirements' in sections:
            score += 1.5
        if 'responsibilities' in sections:
            score += 1.0
        if 'preferred' in sections:
            score += 0.5
        if 'benefits' in sections:
            score += 0.5
        
        # Check text length (longer usually means more complete)
        total_length = sum(len(section) for section in sections.values())
        if total_length > 1000:
            score += 1.0
        elif total_length > 500:
            score += 0.5
        
        return min(score / max_score, 1.0)
