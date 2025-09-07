#!/usr/bin/env python3

"""
Test script for document processing tools.
"""

import sys
import os

# Add tools directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from process_email import process_email
from process_pdf import process_pdf


def test_email_processing():
    """Test email processing functionality."""
    print("=== Testing Email Processing ===")
    
    # Test case 1: Complete email
    email_doc = {
        "subject": "Important Security Alert",
        "sender": "admin@suspicious-bank.com",
        "text": "Dear customer, your account has been compromised. Click here to verify: http://malicious-site.com/verify",
        "urls": ["http://malicious-site.com/verify"],
        "attachments": ["invoice.pdf"]
    }
    
    result = process_email(email_doc)
    print("Test 1 - Complete email:")
    print(result)
    print()
    
    # Test case 2: Minimal email
    minimal_email = {
        "text": "This is a simple email message."
    }
    
    result = process_email(minimal_email)
    print("Test 2 - Minimal email:")
    print(result)
    print()
    
    # Test case 3: Empty email
    empty_email = {}
    
    result = process_email(empty_email)
    print("Test 3 - Empty email:")
    print(result)
    print()


def test_pdf_processing():
    """Test PDF processing functionality."""
    print("=== Testing PDF Processing ===")
    
    # Test case 1: Text as PDF content
    text_content = "This is a sample PDF document with important information about security policies."
    
    result = process_pdf(text_content)
    print("Test 1 - Text content:")
    print(result)
    print()
    
    # Test case 2: Empty content
    result = process_pdf("")
    print("Test 2 - Empty content:")
    print(result)
    print()
    
    # Test case 3: Invalid input
    try:
        result = process_pdf(123)
        print("Test 3 - Invalid input:")
        print(result)
    except Exception as e:
        print("Test 3 - Invalid input (expected error):")
        print(f"Error: {e}")
    print()


def test_selector_integration():
    """Test integration with selector.py logic."""
    print("=== Testing Selector Integration ===")
    
    # Simulate the selector.py logic
    def process_document(document):
        if isinstance(document, dict):
            # Process email
            return [{"server":"data-processor","tool":"process_email", "args":{"document": document}}]
        elif isinstance(document, bytes):
            # Process PDF
            return [{"server":"data-processor","tool":"process_pdf", "args":{"document": document}}]
        else:
            # Unable to process this file type
            return []
    
    # Test with email
    email_doc = {
        "subject": "Test Email",
        "text": "This is a test email for fraud detection."
    }
    
    calls = process_document(email_doc)
    print("Email document call structure:")
    print(calls)
    
    # Simulate calling the tool
    if calls:
        call = calls[0]
        if call["tool"] == "process_email":
            result = process_email(call["args"]["document"])
            print("Email processing result:")
            print(result)
    print()
    
    # Test with PDF (as bytes)
    pdf_content = b"This is simulated PDF content as bytes."
    
    calls = process_document(pdf_content)
    print("PDF document call structure:")
    print(calls)
    
    # Simulate calling the tool
    if calls:
        call = calls[0]
        if call["tool"] == "process_pdf":
            result = process_pdf(call["args"]["document"])
            print("PDF processing result:")
            print(result)
    print()


if __name__ == "__main__":
    test_email_processing()
    test_pdf_processing()
    test_selector_integration()
    print("All tests completed!")
