"""
Email processing tool for extracting and formatting text content.
"""

import re
from typing import Any, Dict, Union


def process_email(document: Dict[str, Any]) -> str:
    """
    Extract and process text content from email document.
    
    Args:
        document: Email document dict with fields:
            - body: str (main email content)
            - body_preview: str (preview text)
            - date: str (email date)
            - from: str (sender email)
            - id: str (email ID)
            - snippet: str (email snippet)
            - subject: str (email subject)
            - threadId: str (thread ID)
            - to: str (recipient email)
    
    Returns:
        str: Processed email text content
    """
    if not isinstance(document, dict):
        raise ValueError("Email document must be a dictionary")
    
    # Extract key fields with defaults
    subject = document.get("subject", "")
    sender = document.get("from", "")
    recipient = document.get("to", "")
    date = document.get("date", "")
    body = document.get("body", "")
    body_preview = document.get("body_preview", "")
    snippet = document.get("snippet", "")
    
    # Use body as primary content, fallback to body_preview or snippet
    main_content = body or body_preview or snippet
    
    # Clean and normalize text content
    processed_text = _clean_email_text(main_content)
    
    # Build formatted output
    output_parts = []
    
    if sender:
        output_parts.append(f"From: {sender}")
    
    if recipient:
        output_parts.append(f"To: {recipient}")
    
    if date:
        output_parts.append(f"Date: {date}")
    
    if subject:
        output_parts.append(f"Subject: {subject}")
    
    if processed_text:
        output_parts.append(f"Content: {processed_text}")
    
    # Join all parts with newlines
    result = "\n".join(output_parts)
    
    if not result.strip():
        return "Empty email document"
    
    return result


def _clean_email_text(text: str) -> str:
    """
    Clean and normalize email text content.
    
    Args:
        text: Raw email text
        
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
    
    # Remove common email artifacts
    text = re.sub(r'^\s*>.*$', '', text, flags=re.MULTILINE)  # Remove quoted lines
    text = re.sub(r'^\s*On.*wrote:\s*$', '', text, flags=re.MULTILINE)  # Remove reply headers
    
    # Remove HTML tags if present
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    text = re.sub(r'[.]{3,}', '...', text)
    
    # Clean up spacing
    text = text.strip()
    
    return text