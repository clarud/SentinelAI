from typing import Optional, Dict, Any
from google.cloud import firestore

# Relies on GOOGLE_APPLICATION_CREDENTIALS env var for auth
_db = firestore.Client()

COLLECTION = "gmail_tokens"

def store_tokens(user_id: str, tokens: Dict[str, Any]) -> None:
    """
    Store OAuth tokens for a user. Overwrites existing doc for idempotency.
    """
    _db.collection(COLLECTION).document(user_id).set(tokens, merge=True)

def get_tokens(user_id: str) -> Optional[Dict[str, Any]]:
    doc = _db.collection(COLLECTION).document(user_id).get()
    return doc.to_dict() if doc.exists else None

def delete_tokens(user_id: str) -> None:
    _db.collection(COLLECTION).document(user_id).delete()
