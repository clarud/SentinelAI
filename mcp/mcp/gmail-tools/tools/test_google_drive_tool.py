from google_drive_tool import create_and_upload_analysis_pdf

# Replace with valid email and message ID
user_email = "sentinelaiginger@gmail.com"
message_id = "19923485ad715358"

# Example analysis data to include in the PDF
analysis_data = {
    "email_subject": "Suspicious Login Attempt",
    "email_sender": "no-reply@example.com",
    "email_recipient": user_email,
    "analysis_results": {
        "is_scam": True,
        "confidence_score": 0.95,
        "detected_keywords": ["login", "attempt", "suspicious"],
        "recommendation": "Mark as SCAM and do not click any links."
    },
    "additional_notes": "This email was flagged due to unusual activity patterns."
}

try:
    # Test the creation and upload of the PDF
    result = create_and_upload_analysis_pdf(user_email, message_id, analysis_data)
    print("Test Result:", result)
except Exception as e:
    print("Error:", e)
