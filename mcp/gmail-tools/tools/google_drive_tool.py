import json
import io
import os
from typing import Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.cloud import firestore
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Firestore setup
db = firestore.Client()
COLLECTION = "gmail_tokens"

def get_tokens(user_email: str):
    """Retrieve OAuth token data from Firestore"""
    doc = db.collection(COLLECTION).document(user_email).get()
    if not doc.exists:
        return None
    return doc.to_dict()

def create_credentials_from_dict(token_data):
    """Create Credentials object from stored token data"""
    if not token_data:
        return None
        
    # Convert ISO string back to datetime if needed
    expiry = token_data.get('expiry')
    if expiry and isinstance(expiry, str):
        expiry = datetime.fromisoformat(expiry)
    
    return Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes'),
        expiry=expiry
    )

def store_drive_link(user_email: str, message_id: str, drive_link: str):
    """Store Google Drive link reference in Firestore"""
    try:
        # Store the drive link in the email document
        db.collection(COLLECTION).document(user_email).collection('emails').document(message_id).set({
            'drive_analysis_link': drive_link,
            'drive_upload_timestamp': datetime.now().isoformat()
        }, merge=True)
        return True
    except Exception as e:
        print(f"Error storing drive link: {e}")
        return False

def get_google_drive_service(user_email: str):
    """Get authenticated Google Drive service"""
    token_data = get_tokens(user_email)
    if not token_data:
        raise Exception("No tokens found for user")
        
    credentials = create_credentials_from_dict(token_data)
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleRequest())
    
    return build("drive", "v3", credentials=credentials)

def create_pdf_from_dict(data_dict: Dict[str, Any], title: str = "Email Analysis") -> io.BytesIO:
    """
    Create a PDF from a dictionary, formatted like JSON
    
    Args:
        data_dict: Dictionary to convert to PDF
        title: Title for the PDF document
        
    Returns:
        BytesIO object containing the PDF
    """
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

def upload_to_google_drive(user_email: str, pdf_buffer: io.BytesIO, filename: str) -> str:
    """
    Upload PDF to Google Drive and return shareable link
    
    Args:
        user_email: User's email address
        pdf_buffer: BytesIO object containing PDF
        filename: Name for the file in Google Drive
        
    Returns:
        Shareable Google Drive link
    """
    try:
        service = get_google_drive_service(user_email)
        
        # File metadata
        file_metadata = {
            'name': filename,
            'parents': []  # Upload to root directory, could be modified to use specific folder
        }
        
        # Create media upload
        media = MediaIoBaseUpload(
            pdf_buffer,
            mimetype='application/pdf',
            resumable=True
        )
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        
        # Make file shareable (anyone with link can view)
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        # Get shareable link
        drive_link = f"https://drive.google.com/file/d/{file_id}/view"
        
        return drive_link
        
    except Exception as e:
        raise Exception(f"Failed to upload to Google Drive: {e}")

def create_and_upload_analysis_pdf(user_email: str, message_id: str, analysis_data: Dict[str, Any], 
                                 title: str = "Email Fraud Analysis") -> Dict[str, Any]:
    """
    Main function to create PDF from analysis data and upload to Google Drive
    
    Args:
        user_email: User's email address
        message_id: Gmail message ID for reference
        analysis_data: Dictionary containing analysis results
        title: Title for the PDF document
        
    Returns:
        Dictionary with upload results and drive link
    """
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_analysis_{message_id[:8]}_{timestamp}.pdf"
        
        # Create PDF from dictionary
        pdf_buffer = create_pdf_from_dict(analysis_data, title)
        
        # Upload to Google Drive
        drive_link = upload_to_google_drive(user_email, pdf_buffer, filename)
        
        # Store reference in Firestore
        stored = store_drive_link(user_email, message_id, drive_link)
        
        return {
            "status": "success",
            "drive_link": drive_link,
            "filename": filename,
            "message_id": message_id,
            "stored_in_firestore": stored,
            "upload_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message_id": message_id
        }
