"""
PDF processing tool for extracting and formatting text content.
"""

import base64
import re
from typing import Union


def process_pdf(document: Union[str, bytes]) -> str:
    """
    Extract and process text content from PDF document.
    
    Args:
        document: PDF document as bytes or base64 encoded string
    
    Returns:
        str: Processed PDF text content
    """
    try:
        # Handle different input formats
        if isinstance(document, str):
            # Assume base64 encoded
            try:
                pdf_bytes = base64.b64decode(document)
            except Exception:
                # If not valid base64, treat as text
                return _clean_pdf_text(document)
        elif isinstance(document, bytes):
            pdf_bytes = document
        else:
            raise ValueError("PDF document must be bytes or base64 string")
        
        # Try to extract text using PyPDF2
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text_content = ""
            
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                except Exception:
                    continue
            
            if text_content.strip():
                return _clean_pdf_text(text_content)
            
        except ImportError:
            # PyPDF2 not available, fall back to basic text extraction
            pass
        except Exception:
            # PDF parsing failed, try alternative methods
            pass
        
        # Try to extract text using pdfplumber (fallback)
        try:
            import pdfplumber
            import io
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text_content = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                    except Exception:
                        continue
                
                if text_content.strip():
                    return _clean_pdf_text(text_content)
                    
        except ImportError:
            # pdfplumber not available
            pass
        except Exception:
            # PDF parsing failed
            pass
        
        # Last resort: try to decode as text
        try:
            text_content = pdf_bytes.decode('utf-8', errors='ignore')
            if text_content.strip():
                return _clean_pdf_text(text_content)
        except Exception:
            pass
        
        return "Unable to extract text from PDF document"
        
    except Exception as e:
        return f"Error processing PDF: {str(e)}"


def _clean_pdf_text(text: str) -> str:
    """
    Clean and normalize PDF text content.
    
    Args:
        text: Raw PDF text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove PDF artifacts
    text = re.sub(r'^\s*Page \d+.*$', '', text, flags=re.MULTILINE)  # Remove page numbers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Remove standalone numbers
    
    # Remove common PDF formatting artifacts
    text = re.sub(r'[^\w\s\.,!?;:()-]', ' ', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    
    # Remove very short lines (likely artifacts)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 3:  # Keep lines with more than 3 characters
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Clean up spacing
    text = text.strip()
    
    return text