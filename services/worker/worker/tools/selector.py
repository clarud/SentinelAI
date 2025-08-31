# 1. List of similar documents
# 2. Risk score and whether is scam
# 3. Pass it on {isScam, confidence_score, risk_score}

from typing import Dict, Any, List

def choose_tools(text: str) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    
    # Step 1. Perform RAG using text to retrieve list of 10 or less similar documents from database.
    steps.append({"server":"rag-tools","tool":"call_rag", "args":{"text": text}})
    
    return steps
