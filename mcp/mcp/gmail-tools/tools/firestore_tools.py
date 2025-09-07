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
        # Extract the 'email' dictionary and its 'id' and 'email_address' fields
        email_data = data.get("email", {})
        document_id = email_data.get("id")
        email_address = email_data.get("email_address")

        if not document_id:
            raise ValueError("The 'email' dictionary must contain an 'id' field.")

        if not email_address:
            raise ValueError("The 'email' dictionary must contain an 'email_address' field.")

        # Store the entire input dictionary in Firestore under the specified structure
        db.collection(COLLECTION).document(email_address).collection("emails").document(document_id).set(data)

        return document_id

    except Exception as e:
        raise Exception(f"Failed to store analysis data: {e}")