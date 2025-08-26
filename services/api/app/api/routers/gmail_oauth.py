import os
from typing import Tuple, Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from app.services.firestore_services import store_tokens

router = APIRouter()

# ---- Configuration from environment ----
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Example: http://localhost:8000/api/oauth2callback  (must match GCP console)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
# Where to send the user after successful connect (your frontend page)
FRONTEND_SUCCESS_URL = os.getenv("FRONTEND_SUCCESS_URL", "/")

# Scopes:
# - gmail.modify if you plan to label/move/mark-as-read (recommended)
# - openid/email/profile to reliably fetch user identity
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile", 
    "openid",
]

# Use bundled client_secret.json instead of env strings (easier dev).
# Place it at services/api/app/config/client_secret.json
client_secret_path = os.getenv('GOOGLE_CLIENT_SECRET_PATH')
if not client_secret_path or not os.path.exists(client_secret_path):
        raise RuntimeError(f"Client secret file not found: {client_secret_path}")

# Simple in-memory state store for dev (replace with Redis if needed)
_STATE = set()


def _new_flow() -> Flow:
    """
    Create a Flow from client_secret.json (recommended for dev).
    """
    flow = Flow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


@router.get("/connect-gmail")
def connect_gmail():
    """
    Starts the Google OAuth flow and redirects the user to consent screen.
    Frontend can simply redirect user to this endpoint (one-button UX).
    """
    flow = _new_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",         # get refresh_token
        include_granted_scopes="true",
        prompt="consent",              # force refresh_token in dev/testing
    )
    _STATE.add(state)
    # We return a 307 Redirect to Google's consent screen
    return RedirectResponse(authorization_url, status_code=307)


@router.get("/oauth2callback")
def oauth2callback(request: Request):
    """
    Handles Google's redirect, exchanges code for tokens,
    fetches user's email, and stores tokens in Firestore.
    """
    # Validate state
    state = request.query_params.get("state")
    if not state or state not in _STATE:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    # Single-use
    _STATE.discard(state)

    flow = _new_flow()
    # Complete token exchange
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials  # google.oauth2.credentials.Credentials

    # Fetch user's email (identity) so we can store tokens under a stable doc id
    # We can use either the id_token (if present) or call the userinfo endpoint.
    # Using Google OAuth2 API:
    oauth2 = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
    userinfo = oauth2.userinfo().get().execute()  # contains 'email', 'id', etc.

    user_email = userinfo.get("email")
    user_id = userinfo.get("id") or user_email
    if not user_email:
        # Fallback: try to refresh/verify again
        credentials.refresh(GoogleRequest())
        userinfo = oauth2.userinfo().get().execute()
        user_email = userinfo.get("email")
        user_id = userinfo.get("id") or user_email

    if not user_email:
        raise HTTPException(status_code=400, detail="Unable to determine user email")

    # Prepare a token payload suitable for reconstructing Credentials later
    token_data = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "user_email": user_email,
        "provider_user_id": user_id,
    }

    # ---- Store tokens in Firestore (this is the part you asked for) ----
    # Use user_email as the doc id (simple & human-readable).
    store_tokens(user_email, token_data)

    # Redirect back to your frontend success page (could include a flag or user email)
    # Example: http://localhost:3001/settings?gmail=connected
    if FRONTEND_SUCCESS_URL:
        return RedirectResponse(FRONTEND_SUCCESS_URL, status_code=307)

    # Fallback: return JSON (useful during dev)
    return JSONResponse({"status": "connected", "email": user_email})
