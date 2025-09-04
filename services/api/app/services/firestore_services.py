from google.cloud import firestore
from google.oauth2.credentials import Credentials
from datetime import datetime
from app.schema import email
import time

# Firestore client
db = firestore.Client()
COLLECTION = "gmail_tokens"

def store_tokens(user_id, token_data):
    """Store OAuth token data in Firestore"""
    db.collection(COLLECTION).document(user_id).set(token_data, merge=True)

def get_tokens(user_id):
    """Retrieve OAuth token data from Firestore"""
    doc = db.collection(COLLECTION).document(user_id).get()
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

def update_watch_expiration(user_id: str, expiration: int):
    """Update watch expiration timestamp in Firestore"""
    db.collection(COLLECTION).document(user_id).set({
        'watch_expiration': expiration
    }, merge=True)

def get_watch_expiration(user_id: str) -> int:
    """Get watch expiration timestamp from Firestore"""
    doc = db.collection(COLLECTION).document(user_id).get()
    if doc.exists:
        return doc.to_dict().get('watch_expiration', 0)
    return 0

def delete_tokens(user_id: str):
    """Delete OAuth tokens from Firestore"""
    db.collection(COLLECTION).document(user_id).delete()

def update_start_history_id(user_id: str, history_id: str):
    """Update the startHistoryId in Firestore for a user"""
    db.collection(COLLECTION).document(user_id).set({
        'start_history_id': history_id
    }, merge=True)

def get_start_history_id(user_id: str) -> str:
    """Get the startHistoryId from Firestore for a user"""
    doc = db.collection(COLLECTION).document(user_id).get()
    if doc.exists:
        return doc.to_dict().get('start_history_id')
    return None

def store_email(user_id: str, email_data: email.EmailData):
    """Store an email in Firestore under a subcollection 'emails'"""
    db.collection(COLLECTION).document(user_id).collection('emails').document(email_data.id).set(email_data.model_dump())
    
def get_all_watching_users() -> list:
    """Get all users who have active Gmail watches"""
    users = []
    now = int(time.time())
    docs = db.collection(COLLECTION).stream()
    
    for doc in docs:
        data = doc.to_dict()
        # If watch_expiration exists and is in the future
        if data.get('watch_expiration', 0) > now:
            users.append(doc.id)
    
    return users

