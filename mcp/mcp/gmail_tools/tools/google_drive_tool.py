import io
import logging
from typing import Dict, Any, List, Union, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.cloud import firestore
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ReportLab imports ---
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Flowable,
)
from reportlab.pdfgen.canvas import Canvas
from dotenv import load_dotenv

load_dotenv()

# Firestore setup
db = firestore.Client()
COLLECTION = "gmail_tokens"

def get_tokens(user_email: str):
    """Retrieve OAuth token data from Firestore"""
    logger.info(f"🔑 Getting tokens for user: {user_email}")
    logger.info(f"🔥 Firestore collection: {COLLECTION}")
    
    doc = db.collection(COLLECTION).document(user_email).get()
    if not doc.exists:
        logger.warning(f"⚠️ No token document found for user: {user_email}")
        return None
    
    token_data = doc.to_dict()
    logger.info(f"✅ Tokens retrieved successfully for user: {user_email}")
    logger.info(f"🔍 Token data keys: {list(token_data.keys()) if token_data else 'None'}")
    return token_data

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
    logger.info(f"🔄 Starting store_drive_link for user: {user_email}, message: {message_id}")
    logger.info(f"📎 Drive link to store: {drive_link}")
    
    try:
        logger.info(f"🔥 Attempting to write to Firestore collection: {COLLECTION}")
        logger.info(f"📧 Document path: {COLLECTION}/{user_email}/emails/{message_id}")
        
        # Store the drive link in the email document
        doc_data = {
            'drive_analysis_link': drive_link,
            'drive_upload_timestamp': datetime.now().isoformat()
        }
        logger.info(f"📝 Data to store: {doc_data}")
        
        db.collection(COLLECTION).document(user_email).collection('emails').document(message_id).set(doc_data, merge=True)
        
        logger.info(f"✅ Successfully stored drive link in Firestore for {user_email}/{message_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Error storing drive link: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        logger.error(f"📍 Failed for user: {user_email}, message: {message_id}")
        print(f"Error storing drive link: {e}")
        return False

def get_google_drive_service(user_email: str):
    """Get authenticated Google Drive service"""
    logger.info(f"🔧 Creating Google Drive service for user: {user_email}")
    
    token_data = get_tokens(user_email)
    if not token_data:
        logger.error(f"❌ No tokens found for user: {user_email}")
        raise Exception("No tokens found for user")
    
    logger.info(f"🔄 Creating credentials from token data...")
    credentials = create_credentials_from_dict(token_data)
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        logger.info(f"🔄 Token expired, refreshing...")
        credentials.refresh(GoogleRequest())
        logger.info(f"✅ Token refreshed successfully")
    else:
        logger.info(f"✅ Token is valid, no refresh needed")
    
    logger.info(f"🏗️ Building Google Drive service...")
    service = build("drive", "v3", credentials=credentials)
    logger.info(f"✅ Google Drive service created successfully")
    
    return service


class Badge(Flowable):
    """A rounded capsule badge with text (e.g., 'SCAM')."""
    def __init__(self, text: str, bg=colors.HexColor("#ef4444"), fg=colors.white, padding_h=6, padding_v=2):
        Flowable.__init__(self)
        self.text = text
        self.bg = bg
        self.fg = fg
        self.padding_h = padding_h
        self.padding_v = padding_v
        self.font_name = "Helvetica-Bold"
        self.font_size = 9
        self._w = None
        self._h = None

    def wrap(self, availWidth, availHeight):
        # Rough text width
        from reportlab.pdfbase.pdfmetrics import stringWidth
        text_w = stringWidth(self.text.upper(), self.font_name, self.font_size)
        self._w = text_w + 2 * self.padding_h
        self._h = self.font_size + 2 * self.padding_v
        return self._w, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h
        r = h / 2.0
        c.setFillColor(self.bg)
        c.setStrokeColor(self.bg)
        # Rounded capsule
        c.roundRect(0, 0, w, h, r, fill=1, stroke=0)
        c.setFillColor(self.fg)
        c.setFont(self.font_name, self.font_size)
        c.drawCentredString(w / 2.0, (h - self.font_size) / 2.0 + 1, self.text.upper())


class ProgressBar(Flowable):
    """Horizontal progress bar 0..1 with label."""
    def __init__(self, value: float, width: float = 80, height: float = 8, show_text: str = ""):
        Flowable.__init__(self)
        self.value = max(0.0, min(1.0, float(value)))
        self.width = width
        self.height = height
        self.show_text = show_text

    def wrap(self, availWidth, availHeight):
        return self.width, max(self.height, 10)

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#e5e7eb"))
        c.setFillColor(colors.HexColor("#e5e7eb"))
        c.roundRect(0, 0, self.width, self.height, self.height / 2.0, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#3b82f6"))
        c.roundRect(0, 0, self.width * self.value, self.height, self.height / 2.0, fill=1, stroke=0)

        if self.show_text:
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica", 8)
            c.drawString(self.width + 6, (self.height - 8) / 2.0, self.show_text)


def _kv_table(d: Dict[str, Any], col1="Field", col2="Value"):
    """Key-value table with light styling."""
    rows = [[f"<b>{col1}</b>", f"<b>{col2}</b>"]]
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            v = _pretty_repr(v)
        rows.append([str(k), str(v)])

    tbl = Table(rows, colWidths=[60*mm, 100*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return tbl


def _mono_box(text: str):
    """Monospace boxed paragraph for raw tool output."""
    style = ParagraphStyle(
        name="Mono",
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    # Escape special characters for safety
    import xml.sax.saxutils as su
    safe = su.escape(text).replace("\n", "<br/>")
    box = Table([[Paragraph(safe, style)]], colWidths=[170*mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return box


def _pretty_repr(value: Union[Dict[str, Any], List[Any], Any]) -> str:
    """Readable one-line-ish repr for small dicts/lists."""
    import json
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


def _header_footer(canvas: Canvas, doc):
    # Header
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#111827"))
    canvas.setFont("Helvetica", 9)
    canvas.drawString(20*mm, 287*mm, "Email Scam Analysis Report")
    canvas.setFillColor(colors.HexColor("#9ca3af"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(200*mm, 287*mm, datetime.now().strftime("%Y-%m-%d %H:%M"))
    # Divider
    canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 285*mm, 200*mm, 285*mm)

    # Footer
    canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
    canvas.line(20*mm, 15*mm, 200*mm, 15*mm)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20*mm, 11*mm, "Generated by Scam Analysis Workflow")
    canvas.drawRightString(200*mm, 11*mm, f"Page {doc.page}")

    canvas.restoreState()


def build_scam_report_pdf(
    result: Dict[str, Any],
    user_email: str,
    title: str = "Email Scam Analysis",
) -> io.BytesIO:
    """
    Convert the given result dict and user_email into a styled PDF (BytesIO).
    Returns: io.BytesIO positioned at start.
    """
    from email.utils import parsedate_to_datetime

    def _fmt_date(s: Optional[str]) -> str:
        if not s:
            return "—"
        try:
            dt = parsedate_to_datetime(s)
            # normalize naive/UTC-ish displays
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z") if dt.tzinfo else dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return s

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=30*mm,
        bottomMargin=20*mm,
        title=title,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )
    sub = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=14.5,
        textColor=colors.HexColor("#111827"),
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#374151"),
    )

    # --------- Header block ---------
    story = []
    story.append(Paragraph(title, h1))
    story.append(Paragraph(f"Recipient: <b>{user_email}</b>", sub))

    # Status badge
    is_scam = str(result.get("is_scam", "unknown")).lower()
    if "scam" in is_scam and "not" not in is_scam:
        badge = Badge("Likely Scam", bg=colors.HexColor("#ef4444"))
    elif "not" in is_scam or "safe" in is_scam:
        badge = Badge("Unlikely Scam", bg=colors.HexColor("#10b981"))
    elif "suspicious" in is_scam:
        badge = Badge("Suspicious", bg=colors.HexColor("#f59e0b"))
    else:
        badge = Badge("Unknown", bg=colors.HexColor("#9ca3af"))
    story.append(badge)
    story.append(Spacer(1, 6))

    # --------- Email Overview (NEW) ---------
    email = (result or {}).get("email") or {}
    if email:
        story.append(Paragraph("Email Overview", h2))
        # Top line: subject emphasized if present
        subject = email.get("subject") or "—"
        story.append(Paragraph(f"<b>Subject:</b> {subject}", body))
        # Key value table for common headers
        email_rows = {
            "From": email.get("sender") or "—",
            "To": email.get("to") or "—",
            "Date": _fmt_date(email.get("date")),
            "Message ID": email.get("id") or "—",
            "Thread ID": email.get("threadId") or "—",
            "Account": email.get("email_address") or "—",
        }
        story.append(_kv_table(email_rows, col1="Header", col2="Value"))
        # Snippet preview if present
        snippet = (email.get("snippet") or "").strip()
        if snippet:
            story.append(Spacer(1, 3))
            story.append(Paragraph("<b>Snippet</b>", small))
            story.append(_mono_box(snippet))


        # Original Body / Preview block
        body_preview = (email.get("body_preview") or "").strip()
        full_body = (email.get("body") or "").strip()
        if body_preview or full_body:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Original Email Body", h2))
            # Prefer preview (usually cleaned/plain-text); fall back to full body
            content = body_preview or full_body
            # Keep very large bodies manageable: soft truncate but still allow the rest in a second box
            MAX_CHARS = 8000  # PDF-friendly limit to avoid giant flows
            if len(content) <= MAX_CHARS:
                story.append(_mono_box(content))
            else:
                story.append(_mono_box(content[:MAX_CHARS] + "\n\n[... truncated ...]"))
                # Optionally include a lighter second box for the remainder
                # story.append(_mono_box(content[MAX_CHARS:]))

    # --------- Quick metrics ---------
    explanation = result.get("explanation", "") or ""
    if explanation:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Summary</b>", h2))
        story.append(Paragraph(explanation, body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Key Metrics</b>", h2))

    conf = float(result.get("confidence_level", 0.0))
    scam_p = float(result.get("scam_probability", 0.0)) / 100.0 if result.get("scam_probability") else 0.0
    evidence_count = int(result.get("processing_metadata", {}).get("evidence_gathered", len(result.get("tool_evidence", []))))
    total_time = float(result.get("processing_metadata", {}).get("total_time", 0.0))

    metrics_table = Table(
        [
            [
                Paragraph("<b>Confidence</b>", small),
                ProgressBar(conf, show_text=f"{conf*100:.0f}%"),
                Paragraph("<b>Scam Probability</b>", small),
                ProgressBar(scam_p, show_text=f"{scam_p*100:.0f}%"),
            ],
            [
                Paragraph("<b>Evidence Gathered</b>", small),
                Paragraph(str(evidence_count), body),
                Paragraph("<b>Processing Time (s)</b>", small),
                Paragraph(f"{total_time:.2f}", body),
            ],
        ],
        colWidths=[35*mm, 55*mm, 35*mm, 45*mm],
        spaceBefore=4,
        spaceAfter=6,
        hAlign="LEFT",
    )
    metrics_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(metrics_table)

    # Optional: include legitimacy score if present
    legitimacy_score = None
    for item in result.get("tool_evidence", []):
        if item.get("tool") == "extraction-tools.extract_organisation":
            legitimacy_score = item.get("output", {}).get("legitimacy_score", None)
            break
    if legitimacy_score is not None:
        story.append(Table(
            [[Paragraph("<b>Legitimacy Score (higher is better)</b>", small),
              ProgressBar(min(max(float(legitimacy_score) / 10.0, 0.0), 1.0), show_text=f"{legitimacy_score:.1f}/10")]],
            colWidths=[70*mm, 100*mm]
        ))

    # --------- Tool Evidence ---------
    story.append(Spacer(1, 6))
    story.append(Paragraph("Tool Evidence", h2))

    tools: List[Dict[str, Any]] = result.get("tool_evidence", []) or []
    if not tools:
        story.append(Paragraph("No tool evidence available.", body))
    else:
        for idx, t in enumerate(tools, start=1):
            tool_name = t.get("tool", "unknown")
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<b>{idx}. {tool_name}</b>", body))
            output = t.get("output", "")
            if isinstance(output, dict):
                story.append(_kv_table(output, col1="Key", col2="Value"))
            else:
                story.append(_mono_box(str(output)))


    # --------- Processing Metadata ---------
    pm = result.get("processing_metadata", {}) or {}
    story.append(Spacer(1, 8))
    story.append(Paragraph("Processing Metadata", h2))
    # Transform timestamp if present
    ts = pm.get("timestamp", None)
    if isinstance(ts, (int, float)):
        try:
            pm_display_ts = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            pm_display_ts = str(ts)
    else:
        pm_display_ts = "—"
    meta_rows = {
        "Workflow ID": pm.get("workflow_id", "—"),
        "Total Time (s)": f"{float(pm.get('total_time', 0.0)):.2f}",
        "Evidence Gathered": str(pm.get("evidence_gathered", "—")),
        "Errors Encountered": str(pm.get("errors_encountered", "—")),
        "Timestamp": pm_display_ts,
    }
    story.append(_kv_table(meta_rows, col1="Property", col2="Value"))

    # Finish
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Note: This report is an automated assessment and should be combined with human judgment for final decisions.",
        ParagraphStyle("Note", parent=small, textColor=colors.HexColor("#6b7280"))
    ))

    # Build with header/footer
    def _on_page(canvas, doc_obj):
        # attach current page number to doc for footer
        if not hasattr(doc_obj, "page"):
            doc_obj.page = 1
        else:
            doc_obj.page += 1
        _header_footer(canvas, doc_obj)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
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
    logger.info(f"☁️ Starting Google Drive upload for user: {user_email}")
    logger.info(f"📁 Filename: {filename}")
    logger.info(f"📊 PDF buffer size: {pdf_buffer.getvalue().__len__()} bytes")
    
    try:
        logger.info(f"🔑 Getting Google Drive service...")
        service = get_google_drive_service(user_email)
        logger.info(f"✅ Google Drive service obtained successfully")
        
        # IMPORTANT: Ensure buffer is positioned at the start
        pdf_buffer.seek(0)
        logger.info(f"📍 Buffer position reset to start")
        
        # File metadata
        file_metadata = {
            'name': filename,
            'parents': []  # Upload to root directory, could be modified to use specific folder
        }
        logger.info(f"📋 File metadata: {file_metadata}")
        
        # Create media upload
        logger.info(f"🔄 Creating media upload object...")
        media = MediaIoBaseUpload(
            pdf_buffer,
            mimetype='application/pdf',
            resumable=True
        )
        logger.info(f"✅ Media upload object created")
        
        # Upload file
        logger.info(f"⬆️ Starting file upload to Google Drive...")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        logger.info(f"✅ File uploaded successfully, ID: {file_id}")
        
        # Make file shareable (anyone with link can view)
        logger.info(f"🔓 Setting file permissions...")
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        logger.info(f"✅ File permissions set successfully")
        
        # Get shareable link
        drive_link = f"https://drive.google.com/file/d/{file_id}/view"
        logger.info(f"🔗 Generated shareable link: {drive_link}")
        
        return drive_link
        
    except Exception as e:
        logger.error(f"💥 Google Drive upload failed: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        logger.error(f"📧 Failed for user: {user_email}, filename: {filename}")
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
    logger.info(f"🚀 Starting create_and_upload_analysis_pdf for user: {user_email}")
    logger.info(f"📧 Message ID: {message_id}")
    logger.info(f"📊 Analysis data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
    logger.info(f"📄 PDF title: {title}")
    
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_analysis_{message_id[:8]}_{timestamp}.pdf"
        logger.info(f"📁 Generated filename: {filename}")
        
        # Create PDF from dictionary
        logger.info(f"🔨 Building PDF report...")
        pdf_buffer = build_scam_report_pdf(analysis_data, title)
        logger.info(f"✅ PDF generated successfully, buffer size: {pdf_buffer.getvalue().__len__()} bytes")

        # Upload to Google Drive
        logger.info(f"☁️ Uploading to Google Drive...")
        drive_link = upload_to_google_drive(user_email, pdf_buffer, filename)
        logger.info(f"✅ Upload successful, drive link: {drive_link}")
        
        # Store reference in Firestore
        logger.info(f"💾 Storing drive link in Firestore...")
        stored = store_drive_link(user_email, message_id, drive_link)
        logger.info(f"📝 Firestore storage result: {stored}")
        
        result = {
            "status": "success",
            "drive_link": drive_link,
            "filename": filename,
            "message_id": message_id,
            "stored_in_firestore": stored,
            "upload_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"🎉 create_and_upload_analysis_pdf completed successfully")
        logger.info(f"📋 Final result: {result}")
        
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message_id": message_id
        }
        
        logger.error(f"💥 create_and_upload_analysis_pdf failed: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        logger.error(f"📧 Failed for user: {user_email}, message: {message_id}")
        logger.error(f"❌ Error result: {error_result}")
        
        return error_result
