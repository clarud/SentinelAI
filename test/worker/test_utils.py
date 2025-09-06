"""
Utility functions for testing the assess_document workflow.
Helper functions for mocking, validation, and test setup.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock

def setup_test_environment():
    """Setup test environment and ensure required directories exist."""
    test_dirs = [
        "test/worker",
        "test/worker/logs",
        "test/worker/mock_data"
    ]
    
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return test_dirs

def create_mock_dependencies():
    """Create a comprehensive set of mocked dependencies for testing."""
    mocks = {
        'call_tool': MagicMock(),
        'chat_json': MagicMock(),
        'process_document': MagicMock(),
        'choose_tools': MagicMock(), 
        'not_scam_executer': MagicMock(),
        'scam_executer': MagicMock()
    }
    
    return mocks

def setup_scam_detection_mocks(mocks: Dict[str, MagicMock], scenario: str = "high_confidence_scam"):
    """Setup mocks for scam detection scenarios."""
    if scenario == "high_confidence_scam":
        mocks['process_document'].return_value = [
            {"server": "data-processor", "tool": "extract_text", "args": {}}
        ]
        mocks['choose_tools'].return_value = [
            {"server": "rag-tools", "tool": "call_rag", "args": {}}
        ]
        mocks['call_tool'].side_effect = [
            "Suspicious content with Nigerian prince scam patterns",
            {
                "average_confidence_level": 0.95,
                "average_scam_probability": 0.89,
                "similar_documents": ["scam_1", "scam_2"],
                "similarity_scores": [0.92, 0.88]
            }
        ]
        mocks['scam_executer'].return_value = [
            {"server": "gmail-tools", "tool": "classify_email", "args": {}}
        ]
    
    elif scenario == "high_confidence_legitimate":
        mocks['process_document'].return_value = [
            {"server": "data-processor", "tool": "extract_text", "args": {}}
        ]
        mocks['choose_tools'].return_value = [
            {"server": "rag-tools", "tool": "call_rag", "args": {}}
        ]
        mocks['call_tool'].side_effect = [
            "Legitimate business communication content",
            {
                "average_confidence_level": 0.93,
                "average_scam_probability": 0.11,
                "similar_documents": ["business_1", "business_2"],
                "similarity_scores": [0.90, 0.87]
            }
        ]
        mocks['not_scam_executer'].return_value = [
            {"server": "gmail-tools", "tool": "mark_safe", "args": {}}
        ]
    
    elif scenario == "uncertain_case":
        mocks['process_document'].return_value = [
            {"server": "data-processor", "tool": "extract_text", "args": {}}
        ]
        mocks['choose_tools'].return_value = [
            {"server": "rag-tools", "tool": "call_rag", "args": {}}
        ]
        mocks['call_tool'].side_effect = [
            "Mixed content with both legitimate and suspicious elements",
            {
                "average_confidence_level": 0.65,
                "average_scam_probability": 0.45,
                "similar_documents": ["mixed_1"],
                "similarity_scores": [0.68]
            },
            ["http://suspicious-link.com"],  # extract_link
            ["555-0123", "$1000"]  # extract_number
        ]
        
        # Mock LLM responses for uncertain case
        mocks['chat_json'].side_effect = [
            {  # Planner
                "calls": [
                    {"server": "extraction-tools", "tool": "extract_link", "args": {"text": "test"}},
                    {"server": "extraction-tools", "tool": "extract_number", "args": {"text": "test"}}
                ]
            },
            {  # Analyst
                "is_scam": "suspicious",
                "confidence_level": 0.7,
                "scam_probability": 65.0,
                "explanation": "Mixed indicators detected"
            },
            {  # Supervisor
                "is_scam": "suspicious", 
                "confidence_level": 0.7,
                "scam_probability": 65.0,
                "explanation": "Mixed indicators detected"
            }
        ]

def setup_error_scenario_mocks(mocks: Dict[str, MagicMock], error_type: str = "rag_failure"):
    """Setup mocks to simulate various error scenarios."""
    mocks['process_document'].return_value = [
        {"server": "data-processor", "tool": "extract_text", "args": {}}
    ]
    mocks['choose_tools'].return_value = [
        {"server": "rag-tools", "tool": "call_rag", "args": {}}
    ]
    
    if error_type == "rag_failure":
        mocks['call_tool'].side_effect = [
            "Extracted text content",  # extract_text succeeds
            Exception("RAG service unavailable")  # call_rag fails
        ]
    elif error_type == "extraction_failure":
        mocks['call_tool'].side_effect = [
            "Extracted text content",
            {"average_confidence_level": 0.6, "average_scam_probability": 0.5},
            Exception("Link extraction failed")  # Optional tool fails
        ]
    elif error_type == "llm_failure":
        mocks['call_tool'].side_effect = [
            "Extracted text",
            {"average_confidence_level": 0.6, "average_scam_probability": 0.5}
        ]
        mocks['chat_json'].side_effect = Exception("LLM service unavailable")

def validate_assessment_result(result: Dict[str, Any], expected_type: str = "any") -> List[str]:
    """Validate that an assessment result has the expected structure and values."""
    errors = []
    
    # Required fields
    required_fields = ["is_scam", "confidence_level", "scam_probability", "explanation"]
    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")
    
    # Processing metadata
    if "processing_metadata" not in result:
        errors.append("Missing processing_metadata")
    else:
        metadata = result["processing_metadata"]
        metadata_fields = ["workflow_id", "total_time", "evidence_gathered", "errors_encountered"]
        for field in metadata_fields:
            if field not in metadata:
                errors.append(f"Missing metadata field: {field}")
    
    # Value validations
    if "confidence_level" in result:
        if not isinstance(result["confidence_level"], (int, float)) or not (0 <= result["confidence_level"] <= 1):
            errors.append("confidence_level must be a number between 0 and 1")
    
    if "scam_probability" in result:
        scam_prob = result["scam_probability"]
        if not isinstance(scam_prob, (int, float)) or not (0 <= scam_prob <= 100):
            errors.append("scam_probability must be a number between 0 and 100")
    
    if "is_scam" in result:
        valid_values = ["scam", "not_scam", "suspicious"]
        if result["is_scam"] not in valid_values:
            errors.append(f"is_scam must be one of {valid_values}")
    
    # Type-specific validations
    if expected_type == "high_confidence_scam":
        if result.get("is_scam") != "scam":
            errors.append("Expected is_scam='scam' for high confidence scam")
        if result.get("confidence_level", 0) < 0.85:
            errors.append("Expected high confidence_level (>= 0.85) for high confidence scam")
        if result.get("scam_probability", 0) < 80:
            errors.append("Expected high scam_probability (>= 80) for high confidence scam")
    
    elif expected_type == "high_confidence_legitimate":
        if result.get("is_scam") != "not_scam":
            errors.append("Expected is_scam='not_scam' for high confidence legitimate")
        if result.get("confidence_level", 0) < 0.85:
            errors.append("Expected high confidence_level (>= 0.85) for high confidence legitimate")
        if result.get("scam_probability", 100) > 20:
            errors.append("Expected low scam_probability (<= 20) for high confidence legitimate")
    
    return errors

def check_log_files_created(test_dir: str = "test/worker") -> Dict[str, bool]:
    """Check if log files were created properly."""
    results = {
        "log_file_created": False,
        "json_file_created": False,
        "files_readable": False
    }
    
    try:
        files = os.listdir(test_dir)
        log_files = [f for f in files if f.startswith("assessment_") and f.endswith(".log")]
        json_files = [f for f in files if f.startswith("assessment_") and f.endswith(".json")]
        
        results["log_file_created"] = len(log_files) > 0
        results["json_file_created"] = len(json_files) > 0
        
        # Test if files are readable
        if log_files and json_files:
            try:
                # Read log file
                with open(os.path.join(test_dir, log_files[0]), 'r') as f:
                    log_content = f.read()
                
                # Read JSON file
                with open(os.path.join(test_dir, json_files[0]), 'r') as f:
                    json_content = json.load(f)
                
                results["files_readable"] = len(log_content) > 0 and len(json_content) > 0
            except Exception:
                results["files_readable"] = False
    
    except Exception:
        pass
    
    return results

def measure_performance(func, *args, **kwargs) -> Dict[str, Any]:
    """Measure performance metrics for a function call."""
    start_time = time.time()
    start_memory = 0  # Could implement memory measurement if needed
    
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    end_time = time.time()
    
    performance_data = {
        "execution_time": end_time - start_time,
        "success": success,
        "error": error,
        "result": result
    }
    
    return performance_data

def create_test_document(doc_type: str = "email", content_type: str = "neutral") -> Dict[str, Any]:
    """Create test documents with specific characteristics."""
    base_document = {
        "type": doc_type,
        "timestamp": time.time(),
        "test_scenario": content_type
    }
    
    if content_type == "scam":
        base_document.update({
            "subject": "URGENT: Claim Your Inheritance",
            "from": "prince@fake-domain.com",
            "content": "Dear friend, I have $10 million for you. Send bank details and $500 fee."
        })
    elif content_type == "legitimate":
        base_document.update({
            "subject": "Weekly Team Meeting",
            "from": "manager@company.com",
            "content": "Hi team, our weekly meeting is scheduled for Friday at 2 PM."
        })
    elif content_type == "uncertain":
        base_document.update({
            "subject": "Limited Time Offer!",
            "from": "deals@store.com",
            "content": "Flash sale! 50% off everything. Click here to shop now!"
        })
    else:  # neutral
        base_document.update({
            "subject": "Test Document",
            "from": "test@example.com",
            "content": "This is a test document for assessment."
        })
    
    return base_document

def cleanup_test_files(test_dir: str = "test/worker", pattern: str = "assessment_"):
    """Clean up test files created during testing."""
    try:
        files = os.listdir(test_dir)
        test_files = [f for f in files if f.startswith(pattern)]
        
        for file in test_files:
            file_path = os.path.join(test_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        return len(test_files)
    except Exception:
        return 0
