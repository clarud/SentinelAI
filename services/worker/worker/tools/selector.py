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
    elif hasattr(document, 'read'):
        # Process file-like object (BufferedReader, etc.)
        pdf_bytes = document.read()
        document.seek(0)  # Reset file pointer
        return [{"server":"data-processor","tool":"process_pdf", "args":{"document": pdf_bytes}}]
    elif isinstance(document, str):
        # Process plain text
        return []
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
    
    if isinstance(document, dict) and final_result:
        # Extract email information if available
        user_email = document.get("email_address", "user@example.com")  # Fallback if no 'to' field
        message_id = document.get("id", "unknown")   # Gmail message ID if available
        
        # Mark email as scam in Gmail (if we have message_id)
        if message_id != "unknown":
            steps.append({
                "server": "gmail-tools", 
                "tool": "mark_as_scam", 
                "args": {
                    "user_email": user_email,
                    "message_id": message_id
                }
            })
        
        # Create analysis PDF and upload to Google Drive
        steps.append({
            "server": "gmail-tools", 
            "tool": "create_analysis_pdf", 
            "args": {
                "user_email": user_email,
                "message_id": message_id,
                "analysis_data": final_result,
                "title": f"Fraud Analysis - {document.get('subject', 'Unknown Email')}"
            }
        })
        
         # Store analysis data in Gmail tools
        steps.append({
            "server": "gmail-tools",
            "tool": "store_analysis_data",
            "args": {
                "data": final_result
            }
        })
        
    # Store in RAG database for future reference
    steps.append({"server": "rag-tools", "tool": "store_rag", "args": {"output": final_result}})

    return steps