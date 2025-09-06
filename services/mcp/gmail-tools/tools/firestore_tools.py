from google.cloud import firestore
from typing import Dict

db = firestore.Client()

COLLECTION = "analysed_emails"

def store_analysis_data(data: Dict):
    """
    Store analysis data in Firestore using the 'id' field from the 'email' dictionary as the document key.

    Args:
        data (Dict): The input dictionary containing analysis data.

    Returns:
        str: The document ID of the stored data.
    """
    try:
        # Extract the 'email' dictionary and its 'id' field
        email_data = data.get("email", {})
        document_id = email_data.get("id")

        if not document_id:
            raise ValueError("The 'email' dictionary must contain an 'id' field.")

        # Store the entire input dictionary in Firestore
        db.collection(COLLECTION).document(document_id).set(data)

        return document_id

    except Exception as e:
        raise Exception(f"Failed to store analysis data: {e}")
