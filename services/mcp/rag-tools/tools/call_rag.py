from pinecone import Pinecone
import os
from dotenv import load_dotenv, find_dotenv
import Dict, Any

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
    rag_results = calculate_average_scores(output)
    return rag_results


def calculate_average_scores(rag_results: list) -> dict:
    """
    Calculate average confidence_level and scam_probability from call_rag results.
    
    Args:
        rag_results: List of dictionaries from call_rag output
        
    Returns:
        dict: Contains average_confidence_level, average_scam_probability, and count
    """
    if not rag_results:
        return {
            "average_confidence_level": 0.0,
            "average_scam_probability": 0.0
        }
    
    confidence_values = []
    probability_values = []
    
    for doc in rag_results:
        confidence_level = doc.get("confidence_level")
        scam_probability = doc.get("scam_probability")
        
        # Only include non-None numeric values
        if confidence_level is not None and isinstance(confidence_level, (int, float)):
            confidence_values.append(float(confidence_level))
            
        if scam_probability is not None and isinstance(scam_probability, (int, float)):
            probability_values.append(float(scam_probability))
    
    # Calculate averages
    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    avg_probability = sum(probability_values) / len(probability_values) if probability_values else 0.0
    
    return {
        "average_confidence_level": round(avg_confidence, 3),
        "average_scam_probability": round(avg_probability, 3)
    }