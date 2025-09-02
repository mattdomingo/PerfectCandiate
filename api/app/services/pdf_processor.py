"""
PDF processing service for text extraction and OCR
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF files and extracting text"""
    
    def __init__(self):
        # Configure pytesseract if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Adjust path as needed
        pass
    
    async def extract_text_from_pdf(self, pdf_data: bytes) -> Dict[str, any]:
        """
        Extract text from PDF using multiple methods
        
        Args:
            pdf_data: PDF file data as bytes
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Open PDF document
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            # Initialize results
            result = {
                "text": "",
                "pages": [],
                "metadata": {
                    "total_pages": len(doc),
                    "has_images": False,
                    "extraction_method": "text",
                    "confidence_score": 1.0
                }
            }
            
            # Extract text page by page
            full_text = []
            has_extractable_text = False
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # First try direct text extraction
                page_text = page.get_text()
                
                if page_text.strip():
                    has_extractable_text = True
                    page_info = {
                        "page_number": page_num + 1,
                        "text": page_text,
                        "method": "direct_extraction"
                    }
                else:
                    # If no text found, try OCR
                    page_info = await self._ocr_page(page, page_num + 1)
                    result["metadata"]["has_images"] = True
                
                result["pages"].append(page_info)
                full_text.append(page_info["text"])
            
            # Combine all text
            result["text"] = "\n\n".join(full_text)
            
            # Update extraction method if OCR was used
            if not has_extractable_text:
                result["metadata"]["extraction_method"] = "ocr"
                result["metadata"]["confidence_score"] = 0.8
            elif result["metadata"]["has_images"]:
                result["metadata"]["extraction_method"] = "hybrid"
                result["metadata"]["confidence_score"] = 0.9
            
            # Clean up text
            result["text"] = self._clean_text(result["text"])
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    async def _ocr_page(self, page, page_number: int) -> Dict[str, any]:
        """
        Perform OCR on a PDF page
        
        Args:
            page: PyMuPDF page object
            page_number: Page number
            
        Returns:
            Dict with page information and OCR text
        """
        try:
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(image, lang='eng')
            
            return {
                "page_number": page_number,
                "text": ocr_text,
                "method": "ocr"
            }
            
        except Exception as e:
            logger.error(f"Error performing OCR on page {page_number}: {e}")
            return {
                "page_number": page_number,
                "text": "",
                "method": "ocr_failed",
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        
        # Remove common PDF artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)  # Control characters
        
        # Fix common OCR issues
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between lowercase and uppercase
        text = re.sub(r'(\w)([.,;:!?])(\w)', r'\1\2 \3', text)  # Add space after punctuation
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    async def extract_metadata(self, pdf_data: bytes) -> Dict[str, any]:
        """
        Extract metadata from PDF
        
        Args:
            pdf_data: PDF file data as bytes
            
        Returns:
            Dict containing PDF metadata
        """
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
                "pages": len(doc),
                "is_encrypted": doc.is_encrypted,
                "is_pdf": doc.is_pdf,
                "page_count": len(doc)
            }
            
            doc.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return {}
    
    async def validate_pdf(self, pdf_data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate if the file is a valid PDF
        
        Args:
            pdf_data: PDF file data as bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            # Basic validation
            if not doc.is_pdf:
                return False, "File is not a valid PDF"
            
            if len(doc) == 0:
                return False, "PDF has no pages"
            
            # Check if PDF is password protected
            if doc.is_encrypted:
                return False, "Password-protected PDFs are not supported"
            
            doc.close()
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            return False, f"Invalid PDF file: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return [".pdf"]
    
    async def estimate_processing_time(self, pdf_data: bytes) -> float:
        """
        Estimate processing time for a PDF
        
        Args:
            pdf_data: PDF file data as bytes
            
        Returns:
            Estimated processing time in seconds
        """
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            page_count = len(doc)
            file_size_mb = len(pdf_data) / (1024 * 1024)
            
            # Basic estimation: 1-2 seconds per page for text extraction
            # Add extra time for OCR if needed
            base_time = page_count * 1.5
            size_factor = file_size_mb * 0.5
            
            estimated_time = base_time + size_factor
            doc.close()
            
            return max(estimated_time, 2.0)  # Minimum 2 seconds
            
        except Exception:
            return 10.0  # Default estimate if calculation fails
