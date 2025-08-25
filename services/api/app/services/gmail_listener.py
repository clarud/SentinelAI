import base64
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.services.firestore_services import get_tokens  # You'll implement this
import threading

def fetch_and_process_emails(user_id):
    """Fetch unread emails for a user and send to AI stub"""
    creds = get_tokens(user_id)  # Retrieve stored OAuth tokens from Firestore
    if not creds:
        print(f"No credentials for user {user_id}")
        return

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])

    if not messages:
        print(f"No new messages for user {user_id}")
        return

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_detail.get('snippet', '')

        # Simulate passing to AI model
        ai_stub_process_email(user_id, snippet)

        # Mark message as read to avoid processing again
        service.users().messages().modify(
            userId='me', id=msg['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

def ai_stub_process_email(user_id, email_content):
    """Stub: Replace with your AI model call later"""
    print(f"[AI STUB] User {user_id} - Processing email: {email_content[:50]}...")

def start_polling(user_id, interval=60):
    """Start a background thread that polls Gmail every X seconds"""
    def poll():
        while True:
            fetch_and_process_emails(user_id)
            time.sleep(interval)

    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    print(f"Started polling Gmail for user {user_id}")
