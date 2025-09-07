#!/usr/bin/env python3

"""
Test script for the calculate_average_scores function.
"""

import sys
import os

# Add tools directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from call_rag import calculate_average_scores


def test_calculate_average_scores():
    """Test the calculate_average_scores function with sample data."""
    print("=== Testing calculate_average_scores function ===")
    
    # Test case 1: Complete data
    sample_data = [
        {
            "text": "Sample fraud email 1",
            "is_scam": "scam",
            "confidence_level": 0.8,
            "scam_probability": 0.75
        },
        {
            "text": "Sample fraud email 2", 
            "is_scam": "scam",
            "confidence_level": 0.9,
            "scam_probability": 0.85
        },
        {
            "text": "Sample legitimate email",
            "is_scam": "not_scam",
            "confidence_level": 0.6,
            "scam_probability": 0.2
        }
    ]
    
    result = calculate_average_scores(sample_data)
    print("Test 1 - Complete data:")
    print(f"  Average confidence level: {result['average_confidence_level']}")
    print(f"  Average scam probability: {result['average_scam_probability']}")
    print(f"  Confidence count: {result['confidence_count']}")
    print(f"  Probability count: {result['probability_count']}")
    print(f"  Total documents: {result['total_documents']}")
    print()
    
    # Test case 2: Missing values
    sample_data_with_nulls = [
        {
            "text": "Sample email 1",
            "is_scam": "scam", 
            "confidence_level": 0.7,
            "scam_probability": None
        },
        {
            "text": "Sample email 2",
            "is_scam": "scam",
            "confidence_level": None,
            "scam_probability": 0.8
        },
        {
            "text": "Sample email 3",
            "is_scam": "not_scam",
            "confidence_level": 0.5,
            "scam_probability": 0.3
        }
    ]
    
    result = calculate_average_scores(sample_data_with_nulls)
    print("Test 2 - Data with missing values:")
    print(f"  Average confidence level: {result['average_confidence_level']}")
    print(f"  Average scam probability: {result['average_scam_probability']}")
    print(f"  Confidence count: {result['confidence_count']}")
    print(f"  Probability count: {result['probability_count']}")
    print(f"  Total documents: {result['total_documents']}")
    print()
    
    # Test case 3: Empty list
    result = calculate_average_scores([])
    print("Test 3 - Empty list:")
    print(f"  Average confidence level: {result['average_confidence_level']}")
    print(f"  Average scam probability: {result['average_scam_probability']}")
    print(f"  Total documents: {result['total_documents']}")
    print()
    
    # Test case 4: All None values
    sample_data_all_none = [
        {
            "text": "Sample email 1",
            "is_scam": "scam",
            "confidence_level": None,
            "scam_probability": None
        },
        {
            "text": "Sample email 2", 
            "is_scam": "not_scam",
            "confidence_level": None,
            "scam_probability": None
        }
    ]
    
    result = calculate_average_scores(sample_data_all_none)
    print("Test 4 - All None values:")
    print(f"  Average confidence level: {result['average_confidence_level']}")
    print(f"  Average scam probability: {result['average_scam_probability']}")
    print(f"  Confidence count: {result['confidence_count']}")
    print(f"  Probability count: {result['probability_count']}")
    print(f"  Total documents: {result['total_documents']}")
    print()


def test_integration_example():
    """Show how to use this with call_rag results."""
    print("=== Integration Example ===")
    
    # Simulate what you would do after calling call_rag
    print("# After calling call_rag:")
    print("rag_results = call_rag('suspicious email text')")
    print("averages = calculate_average_scores(rag_results)")
    print("")
    print("# Use the averages in your orchestrator:")
    print("processed_document_with_averages = {")
    print("    'text': processed_document,")
    print("    'average_confidence': averages['average_confidence_level'],")
    print("    'average_scam_probability': averages['average_scam_probability'],")
    print("    'similar_documents_count': averages['total_documents']")
    print("}")
    print()


if __name__ == "__main__":
    test_calculate_average_scores()
    test_integration_example()
    print("All tests completed!")
