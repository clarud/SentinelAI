# 1. List of similar documents
# 2. Risk score and whether is scam
# 3. Pass it on {isScam, confidence_score, risk_score}

from typing import Dict, Any, List

def process_document(document: Any) -> Dict[str, Any]:
    if isinstance(document, dict):
        # Process email
        return [{"server":"data-processor","tool":"process_email", "args":{"document": document}}]
    elif isinstance(document, bytes):
        # Process PDF
        return [{"server":"data-processor","tool":"process_pdf", "args":{"document": document}}]
    else:
        # Unable to process this file type
        # Implement some error handling
        return {"error": "unsupported document type"}

def choose_tools(document: str) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    
    # Step 1. Perform RAG using text to retrieve list of 10 or less similar documents from database.
    steps.append({"server":"rag-tools","tool":"call_rag", "args":{"document": document}})

    return steps

def not_scam_executer(final_result=None) -> List[Dict[str, Any]]:
    """Execute actions for legitimate (not scam) documents."""
    steps: List[Dict[str, Any]] = []
    
    # Store in RAG database for future reference
    steps.append({"server": "rag-tools", "tool": "store_rag", "args": {"output": final_result}})
    
    return steps

def scam_executer(document: Any, final_result=None) -> List[Dict[str, Any]]:
    """Execute actions for scam documents."""
    steps: List[Dict[str, Any]] = []
    
    # Classify the email for further processing
    steps.append({"server": "gmail-tools", "tool": "classify_email", "args": {"document": document}})
    
    # Send report to drive
    steps.append({"server": "gmail-tools", "tool": "send_report_to_drive", "args": {"output": final_result}})
    
    # Store in RAG database for future reference
    steps.append({"server": "rag-tools", "tool": "store_rag", "args": {"output": final_result}})

    return steps