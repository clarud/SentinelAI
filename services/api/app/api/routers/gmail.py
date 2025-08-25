from fastapi import APIRouter, Request
from app.services.gmail_listener import start_polling
from app.services.firestore_services import store_tokens

router = APIRouter()

@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    # existing token exchange logic...
    # suppose you have user_id from session or request
    user_id = "some_user_id"  # replace with actual logic

    # Store tokens in Firestore
    store_tokens(user_id, credentials)

    # Start polling Gmail for new emails
    start_polling(user_id)

    return {"message": "Gmail connected and listening for new emails"}
