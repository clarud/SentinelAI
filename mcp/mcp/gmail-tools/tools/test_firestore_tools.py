from firestore_tools import store_analysis_data

# Dummy payload to test Firestore storage
data = {
    "is_scam": "Scam",
    "confidence_score": 0.85,
    "scam_probability": 0.9,
    "explanation": "Quite obviously a scam",
    "text": "This is a scam email",
    "email": {
        "id": "19923485ad715359",
        "date": "2025-09-07",
        "body": "This is the body of the test email.",
        "subject": "Test Email Subject",
        "sender": "sender@example.com",
        "timestamp": "2025-09-07T12:00:00Z",
        "email_address": "sentinelaiginger@gmail.com",
        "Additional String": "This is the additional String"
    },
    
}

try:
    # Test storing the dummy payload in Firestore
    document_id = store_analysis_data(data)
    print(f"Test successful! Data stored under document ID: {document_id}")
except Exception as e:
    print(f"Error during Firestore test: {e}")
