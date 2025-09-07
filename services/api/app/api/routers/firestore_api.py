from fastapi import APIRouter, HTTPException
from google.cloud import firestore

router = APIRouter()

db = firestore.Client()
COLLECTION = "gmail_tokens"

@router.get("/emails/{email_address}")
def get_message_ids(email_address: str):
    """
    Fetch all message IDs for a given email address.

    Args:
        email_address (str): The email address to query.

    Returns:
        list: A list of message IDs.
    """
    try:
        # Query Firestore for the emails collection under the given email address
        emails_ref = db.collection(COLLECTION).document(email_address).collection("emails")
        docs = emails_ref.stream()

        # Extract message IDs from the documents
        message_ids = [doc.id for doc in docs]
        return message_ids

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message IDs: {e}")

@router.get("/emails/{email_address}/{message_id}")
def get_message_details(email_address: str, message_id: str):
    """
    Fetch the details of a specific message by its ID for a given email address.

    Args:
        email_address (str): The email address to query.
        message_id (str): The message ID to fetch details for.

    Returns:
        dict: The contents of the message.
    """
    try:
        # Query Firestore for the specific message document
        message_ref = db.collection(COLLECTION).document(email_address).collection("emails").document(message_id)
        doc = message_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Message not found")

        return doc.to_dict()

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message details: {e}")