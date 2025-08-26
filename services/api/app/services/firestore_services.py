# app/services/firestore_services.py
from google.cloud import firestore
from google.oauth2.credentials import Credentials
import os
from google.auth.exceptions import DefaultCredentialsError

try:
    # Try to initialize Firestore client
    db = firestore.Client()
except DefaultCredentialsError:
    # Fallback: Create a client without default credentials
    # You'll need to handle this case appropriately
    db = None
    print("Warning: Firestore client not initialized - missing credentials")

def store_tokens(user_id, token_data):
    """Store OAuth token data in Firestore"""
    if db is None:
        print("Error: Firestore client not initialized")
        return False
    
    try:
        db.collection('gmail_tokens').document(user_id).set(token_data, merge=True)
        return True
    except Exception as e:
        print(f"Error storing tokens: {e}")
        return False

def get_tokens(user_id):
    """Retrieve OAuth token data from Firestore"""
    if db is None:
        print("Error: Firestore client not initialized")
        return None
    
    try:
        doc = db.collection('gmail_tokens').document(user_id).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        return Credentials(
            token=data.get('token'),
            refresh_token=data.get('refresh_token'),
            token_uri=data.get('token_uri'),
            client_id=data.get('client_id'),
            client_secret=data.get('client_secret'),
            scopes=data.get('scopes')
        )
    except Exception as e:
        print(f"Error retrieving tokens: {e}")
        return None