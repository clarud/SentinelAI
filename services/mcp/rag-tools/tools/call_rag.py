from pinecone import Pinecone
import os
from dotenv import load_dotenv, find_dotenv

# Load .env from parent directories
load_dotenv(find_dotenv())

def call_rag(text: str) -> list:
    """
    Calls Pinecone semantic search and returns top 10 similar texts with selected metadata.
    Only includes results where at least one of the three metadata fields is not None.
    """
    # Load Pinecone credentials from environment or config
    api_key = os.getenv("PINECONE_API_KEY")
    index_host = os.getenv("PINECONE_INDEX_HOST")
    namespace = "fraud-detection-csv"

    pc = Pinecone(api_key=api_key)
    index = pc.Index(host=index_host)

    results = index.search(
        namespace=namespace,
        query={
            "inputs": {"text": text},
            "top_k": 10
        },
        fields=["text", "chunk_risk_level", "confidence_level", "scam_probability"]
    )

    output = []
    for match in results.get("result", {}).get("hits", []):
        metadata = match.get("fields", {})
        # Rename chunk_risk_level to is_scam
        is_scam = metadata.get("chunk_risk_level")
        confidence_level = metadata.get("confidence_level")
        scam_probability = metadata.get("scam_probability")
        # Only include if at least one is not None
        # if any([is_scam, confidence_level, scam_probability]):
        output.append({
            "text": metadata.get("text", ""),
            "is_scam": is_scam,
            "confidence_level": confidence_level,
            "scam_probability": scam_probability
        })
    return output