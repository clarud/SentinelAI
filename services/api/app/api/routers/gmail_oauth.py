import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from app.services.firestore_services import store_tokens, get_tokens, create_credentials_from_dict

router = APIRouter()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_SUCCESS_URL = os.getenv("FRONTEND_SUCCESS_URL", "/")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

client_secret_path = os.getenv('GOOGLE_CLIENT_SECRET_PATH')
_STATE = set()

def _new_flow() -> Flow:
    """Create a Flow from client_secret.json"""
    return Flow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

def get_gmail_service(user_id: str):
    """Return an authenticated Gmail API client for a user"""
    token_data = get_tokens(user_id)
    if not token_data:
        raise HTTPException(status_code=404, detail="User not authenticated")
    
    credentials = create_credentials_from_dict(token_data)
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleRequest())
        # Update stored tokens
        token_data.update({
            'access_token': credentials.token,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        })
        store_tokens(user_id, token_data)
    
    return build("gmail", "v1", credentials=credentials)

@router.get("/connect-gmail")
def connect_gmail():
    """Start Google OAuth flow"""
    flow = _new_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    _STATE.add(state)
    return RedirectResponse(authorization_url, status_code=307)

@router.get("/oauth2callback")
def oauth2callback(request: Request):
    """Handle Google OAuth callback"""
    state = request.query_params.get("state")
    if not state or state not in _STATE:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    _STATE.discard(state)

    flow = _new_flow()
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    oauth2 = build("oauth2", "v2", credentials=credentials)
    userinfo = oauth2.userinfo().get().execute()
    user_email = userinfo.get("email")

    if not user_email:
        raise HTTPException(status_code=400, detail="Unable to determine user email")

    token_data = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "user_email": user_email,
        "provider_user_id": userinfo.get("id"),
    }

    store_tokens(user_email, token_data)

    # Start Gmail watch immediately after authentication
    from app.api.routers.gmail_watch import GmailWatcher
    try:
        watcher = GmailWatcher(user_email)
        topic_name = os.getenv("PUBSUB_TOPIC", "projects/your-project/topics/gmail-notifications")
        watcher.start_watch(topic_name)
        print(f"✅ start_watch successfully called for {user_email}")
    except Exception as e:
        print(f"Failed to start Gmail watch for {user_email}: {e}")

    if FRONTEND_SUCCESS_URL:
        return RedirectResponse(FRONTEND_SUCCESS_URL, status_code=307)

    return JSONResponse({"status": "connected", "email": user_email})