from pinecone import Pinecone
import os
import uuid
from dotenv import load_dotenv, find_dotenv

# Load .env from parent directories
load_dotenv(find_dotenv())

def store_rag(output: dict, similarity_threshold: float = 0.85):
    """
    Stores or updates a single output dict in Pinecone.
    - If a similar record (score > threshold) exists, update it.
    - Otherwise, insert as a new record.
    """
    api_key = os.getenv("PINECONE_API_KEY")
    index_host = os.getenv("PINECONE_INDEX_HOST")
    namespace = "fraud-detection-csv"

    pc = Pinecone(api_key=api_key)
    index = pc.Index(host=index_host)

    # Search for similar record
    search_results = index.search(
        namespace=namespace,
        query={
            "inputs": {"text": output["text"]},
            "top_k": 1
        },
        fields=["text", "chunk_risk_level", "confidence_level", "scam_probability"]
    )

    # Default to new record
    record_id = str(uuid.uuid4())
    # If a similar record is found above threshold, use its _id
    matches = search_results.get("matches", [])
    if matches and matches[0].get("score", 0) > similarity_threshold:
        record_id = matches[0]["_id"]

    record = {
        "_id": record_id,
        "text": output["text"],
        "chunk_risk_level": output.get("is_scam"),
        "confidence_level": output.get("confidence_level"),
        "scam_probability": output.get("scam_probability"),
    }

    index.upsert_records(namespace, [record])