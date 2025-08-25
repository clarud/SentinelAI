# from typing import Optional, Dict, Any
# from google.cloud import firestore

# # Relies on GOOGLE_APPLICATION_CREDENTIALS env var for auth
# _db = firestore.Client()

# COLLECTION = "gmail_tokens"

# def store_tokens(user_id: str, tokens: Dict[str, Any]) -> None:
#     """
#     Store OAuth tokens for a user. Overwrites existing doc for idempotency.
#     """
#     _db.collection(COLLECTION).document(user_id).set(tokens, merge=True)

# def get_tokens(user_id: str) -> Optional[Dict[str, Any]]:
#     doc = _db.collection(COLLECTION).document(user_id).get()
#     return doc.to_dict() if doc.exists else None

# def delete_tokens(user_id: str) -> None:
#     _db.collection(COLLECTION).document(user_id).delete()

from google.cloud import firestore
from google.oauth2.credentials import Credentials
import os

# Firestore client
db = firestore.Client()

def store_tokens(user_id, credentials):
    """Store OAuth credentials in Firestore"""
    data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    db.collection('users').document(user_id).set({'credentials': data})

def get_tokens(user_id):
    """Retrieve OAuth credentials from Firestore"""
    doc = db.collection('users').document(user_id).get()
    if not doc.exists:
        return None

    data = doc.to_dict().get('credentials')
    return Credentials(
        token=data['token'],
        refresh_token=data['refresh_token'],
        token_uri=data['token_uri'],
        client_id=data['client_id'],
        client_secret=data['client_secret'],
        scopes=data['scopes']
    )
