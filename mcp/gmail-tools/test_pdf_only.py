#!/usr/bin/env python3
"""
Simple PDF creation test without Firestore dependencies
"""

import json
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_pdf_from_dict(data_dict, title="Analysis Report"):
    """Create a PDF from a dictionary, formatted like JSON"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='darkblue',
        spaceAfter=30
    )
    
    # Build content
    content = []
    
    # Add title
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 20))
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    content.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
    content.append(Spacer(1, 20))
    
    # Convert dict to formatted JSON string
    json_str = json.dumps(data_dict, indent=2, ensure_ascii=False)
    
    # Add JSON content with monospace font
    json_style = ParagraphStyle(
        'JSONStyle',
        parent=styles['Code'],
        fontSize=10,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20
    )
    
    # Split JSON into chunks to handle long content
    max_lines_per_chunk = 40
    lines = json_str.split('\n')
    
    for i in range(0, len(lines), max_lines_per_chunk):
        chunk_lines = lines[i:i + max_lines_per_chunk]
        chunk_text = '\n'.join(chunk_lines)
        
        # Use Preformatted for better JSON formatting
        content.append(Preformatted(chunk_text, json_style))
        
        # Add page break if there are more chunks
        if i + max_lines_per_chunk < len(lines):
            content.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer

def main():
    print("PDF Creation Test (Standalone)")
    print("=" * 35)
    
    # Sample fraud analysis data
    sample_analysis = {
        "email_analysis": {
            "message_id": "test_message_123",
            "fraud_score": 0.85,
            "risk_level": "HIGH",
            "detected_issues": [
                "Suspicious sender domain",
                "Phishing keywords detected", 
                "Urgent language patterns"
            ],
            "sender_info": {
                "email": "suspicious@fake-bank.com",
                "domain_age": "2 days",
                "reputation": "BLACKLISTED"
            },
            "content_analysis": {
                "suspicious_links": [
                    "http://fake-bank-login.ru/secure",
                    "http://phishing-site.tk/verify"
                ],
                "attachment_analysis": "No attachments",
                "language_analysis": "Urgent, threatening tone detected"
            },
            "recommendation": "BLOCK AND QUARANTINE",
            "confidence": "95%"
        },
        "metadata": {
            "analysis_timestamp": "2025-09-05T10:30:00Z",
            "model_version": "SentinelAI-v2.1", 
            "processing_time_ms": 1250
        }
    }
    
    try:
        # Create PDF
        print("Creating PDF from analysis data...")
        pdf_buffer = create_pdf_from_dict(sample_analysis, "Email Fraud Analysis Report")
        
        # Save to file
        filename = "sample_fraud_analysis.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_buffer.getvalue())
            
        print(f"✅ PDF created successfully: {filename}")
        print(f"File size: {len(pdf_buffer.getvalue())} bytes")
        print("\nYou can open this file to see how the analysis data is formatted in the PDF")
        print("This demonstrates what would be uploaded to Google Drive for each analysis")
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")

if __name__ == "__main__":
    main()
