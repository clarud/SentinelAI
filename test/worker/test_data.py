"""
Mock data and fixtures for testing the assess_document workflow.
Contains realistic test data for various fraud detection scenarios.
"""
from typing import Dict, Any, List

# Sample scam emails for testing
SCAM_EMAILS = {
    "nigerian_prince": {
        "type": "email",
        "subject": "URGENT: Claim Your Inheritance",
        "from": "prince.nigeria@fake-domain.com", 
        "content": """
        Dear Beneficiary,
        
        I am Prince John from Nigeria. My late father left $10,000,000 USD for you.
        To claim this inheritance, please send:
        - Your full name and address
        - Bank account details
        - Processing fee of $1,500
        
        Reply urgently to: claim.inheritance@fake-bank.com
        
        Best regards,
        Prince John
        Phone: +234-555-FAKE
        """
    },
    
    "lottery_scam": {
        "type": "email",
        "subject": "CONGRATULATIONS! You Won $500,000",
        "from": "lottery-winner@fake-lottery.org",
        "content": """
        CONGRATULATIONS!!!
        
        You have won $500,000 in the International Email Lottery!
        Your winning number is: 123-456-789
        
        To claim your prize:
        1. Click here: http://fake-lottery-site.com/claim
        2. Provide your personal information
        3. Pay $200 processing fee
        
        Act now! Offer expires in 24 hours!
        """
    },
    
    "phishing_bank": {
        "type": "email",
        "subject": "Urgent: Verify Your Account",
        "from": "security@fake-bank-name.com",
        "content": """
        URGENT SECURITY ALERT
        
        Your account has been temporarily suspended due to suspicious activity.
        
        To restore access, please verify your account immediately:
        - Username and password
        - Social security number
        - Account number
        
        Click here to verify: http://fake-bank-verify.com/login
        
        Failure to verify within 24 hours will result in permanent account closure.
        """
    }
}

# Sample legitimate emails
LEGITIMATE_EMAILS = {
    "business_meeting": {
        "type": "email",
        "subject": "Q3 Financial Review Meeting",
        "from": "john.smith@legitimate-company.com",
        "content": """
        Hi Sarah,
        
        I hope this email finds you well. I'd like to schedule our Q3 financial 
        review meeting for next Tuesday at 2 PM in Conference Room A.
        
        Please let me know if this time works for you, or suggest an alternative.
        
        Best regards,
        John Smith
        Senior Financial Analyst
        ABC Corporation
        Phone: (555) 123-4567
        """
    },
    
    "newsletter": {
        "type": "email",
        "subject": "Weekly Tech Newsletter - AI Advances",
        "from": "newsletter@tech-journal.com",
        "content": """
        Weekly Tech Newsletter - Issue #147
        
        This week's highlights:
        - New AI breakthroughs in healthcare
        - Quantum computing developments
        - Cybersecurity best practices
        
        Read more at: https://tech-journal.com/weekly/147
        
        To unsubscribe: https://tech-journal.com/unsubscribe
        
        Tech Journal Team
        """
    },
    
    "invoice": {
        "type": "email",
        "subject": "Invoice #INV-2025-001234",
        "from": "billing@software-vendor.com",
        "content": """
        Dear Customer,
        
        Please find attached your invoice for software licensing:
        
        Invoice #: INV-2025-001234
        Amount: $299.99
        Due Date: September 15, 2025
        
        Payment can be made through our secure portal:
        https://software-vendor.com/billing/pay
        
        Thank you for your business!
        
        Billing Department
        Software Vendor Inc.
        """
    }
}

# Mixed/uncertain emails that require full analysis
UNCERTAIN_EMAILS = {
    "promotional": {
        "type": "email", 
        "subject": "Limited Time Offer - 70% Off!",
        "from": "deals@online-store.net",
        "content": """
        FLASH SALE - 70% OFF EVERYTHING!
        
        Don't miss out on our biggest sale of the year!
        
        Click here to shop now: http://deals-site.com/flash-sale
        Use code: SAVE70
        
        Hurry! Sale ends at midnight!
        
        Note: This is a one-time email. We found your email through our partners.
        """
    },
    
    "tech_support": {
        "type": "email",
        "subject": "Your Computer May Be Infected",
        "from": "support@tech-help-center.org",
        "content": """
        WARNING: Security Scan Complete
        
        Our systems detected potential malware on your computer.
        
        To protect your data:
        1. Download our security tool: http://tech-help-center.org/scanner
        2. Run a full system scan
        3. Call our support line: 1-800-TECH-HELP
        
        Don't ignore this warning - act now to protect your information!
        
        Tech Support Team
        """
    }
}

# Mock responses for different tools
MOCK_TOOL_RESPONSES = {
    "data-processor.extract_text": {
        "scam": "Extracted text contains Nigerian prince inheritance scam content with suspicious money transfer requests.",
        "legitimate": "Extracted legitimate business communication about quarterly meeting scheduling.",
        "uncertain": "Extracted promotional content with mixed legitimate and suspicious elements."
    },
    
    "rag-tools.call_rag": {
        "high_confidence_scam": {
            "average_confidence_level": 0.95,
            "average_scam_probability": 0.89,
            "similar_documents": ["nigerian_scam_001", "inheritance_fraud_002", "money_transfer_scam_003"],
            "similarity_scores": [0.94, 0.91, 0.87]
        },
        "high_confidence_legitimate": {
            "average_confidence_level": 0.93,
            "average_scam_probability": 0.12,
            "similar_documents": ["business_email_001", "meeting_request_002", "corporate_comm_003"],
            "similarity_scores": [0.89, 0.86, 0.82]
        },
        "uncertain": {
            "average_confidence_level": 0.65,
            "average_scam_probability": 0.45,
            "similar_documents": ["promotional_email_001", "sales_offer_002"],
            "similarity_scores": [0.71, 0.68]
        }
    },
    
    "extraction-tools.extract_link": {
        "scam": ["http://fake-bank-site.com/claim", "http://suspicious-domain.net/verify"],
        "legitimate": ["https://legitimate-company.com/portal", "https://software-vendor.com/billing"],
        "uncertain": ["http://deals-site.com/flash-sale", "http://tech-help-center.org/scanner"]
    },
    
    "extraction-tools.extract_number": {
        "scam": ["+234-555-FAKE", "$10,000,000", "$1,500"],
        "legitimate": ["(555) 123-4567", "$299.99", "Issue #147"],
        "uncertain": ["1-800-TECH-HELP", "70%", "$0"]
    },
    
    "extraction-tools.extract_organisation": {
        "scam": ["Nigerian Prince Foundation", "International Email Lottery", "Fake Bank Security"],
        "legitimate": ["ABC Corporation", "Tech Journal", "Software Vendor Inc."],
        "uncertain": ["Online Store Net", "Tech Help Center"]
    },
    
    "gmail-tools.classify_email": {
        "scam": {"classification": "SPAM", "confidence": 0.92},
        "legitimate": {"classification": "SAFE", "confidence": 0.88},
        "uncertain": {"classification": "SUSPICIOUS", "confidence": 0.67}
    }
}

# Expected assessment results for test validation
EXPECTED_RESULTS = {
    "high_confidence_scam": {
        "is_scam": "scam",
        "confidence_level_min": 0.85,
        "scam_probability_min": 0.8,
        "explanation_contains": ["High confidence", "fraud", "scam"]
    },
    "high_confidence_legitimate": {
        "is_scam": "not_scam", 
        "confidence_level_min": 0.85,
        "scam_probability_max": 0.2,
        "explanation_contains": ["High confidence", "legitimate"]
    },
    "uncertain_analysis": {
        "is_scam_options": ["suspicious", "not_scam", "scam"],
        "confidence_level_range": (0.5, 0.9),
        "scam_probability_range": (0.2, 0.8)
    }
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "max_processing_time": 30.0,  # seconds
    "max_tool_calls": 15,
    "min_evidence_items": 1,
    "required_metadata_fields": ["workflow_id", "total_time", "evidence_gathered", "errors_encountered"]
}

# Error simulation data
ERROR_SCENARIOS = {
    "rag_service_down": {
        "tool": "rag-tools.call_rag",
        "error": "Connection timeout: RAG service unavailable"
    },
    "extraction_failure": {
        "tool": "extraction-tools.extract_link",
        "error": "Text parsing failed: Invalid format"
    },
    "llm_rate_limit": {
        "error": "Rate limit exceeded: Too many requests"
    },
    "invalid_json": {
        "response": '{"invalid": json response}'
    }
}
