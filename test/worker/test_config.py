"""
Configuration file for assess_document workflow tests.
Defines test scenarios, expected outcomes, and benchmarks.
"""

# Test configuration
TEST_CONFIG = {
    "log_directory": "test/worker",
    "cleanup_after_tests": True,
    "performance_monitoring": True,
    "detailed_logging": True
}

# Test scenarios and their expected outcomes
TEST_SCENARIOS = {
    "high_confidence_scam": {
        "description": "Documents with clear scam indicators that should trigger fast-path detection",
        "expected_outcome": {
            "is_scam": "scam",
            "confidence_level_min": 0.85,
            "scam_probability_min": 0.8,
            "processing_path": "fast_classification",
            "tool_calls_max": 5
        },
        "test_documents": [
            {
                "name": "nigerian_prince_email",
                "content": "Dear friend, I have $10 million inheritance from my late father...",
                "expected_rag_response": {
                    "average_confidence_level": 0.95,
                    "average_scam_probability": 0.89
                }
            },
            {
                "name": "lottery_scam_email", 
                "content": "CONGRATULATIONS! You won $500,000 in our lottery...",
                "expected_rag_response": {
                    "average_confidence_level": 0.92,
                    "average_scam_probability": 0.87
                }
            }
        ]
    },
    
    "high_confidence_legitimate": {
        "description": "Documents with clear legitimate indicators that should trigger fast-path detection",
        "expected_outcome": {
            "is_scam": "not_scam",
            "confidence_level_min": 0.85,
            "scam_probability_max": 0.2,
            "processing_path": "fast_classification",
            "tool_calls_max": 5
        },
        "test_documents": [
            {
                "name": "business_meeting_email",
                "content": "Hi Sarah, let's schedule our quarterly review meeting...",
                "expected_rag_response": {
                    "average_confidence_level": 0.93,
                    "average_scam_probability": 0.11
                }
            },
            {
                "name": "legitimate_invoice",
                "content": "Please find attached your invoice for software licensing...",
                "expected_rag_response": {
                    "average_confidence_level": 0.91,
                    "average_scam_probability": 0.08
                }
            }
        ]
    },
    
    "uncertain_analysis": {
        "description": "Documents requiring full LLM analysis pipeline",
        "expected_outcome": {
            "is_scam_options": ["suspicious", "not_scam", "scam"],
            "confidence_level_range": (0.5, 0.9),
            "scam_probability_range": (0.2, 0.8),
            "processing_path": "full_analysis",
            "tool_calls_min": 3,
            "requires_llm_analysis": True
        },
        "test_documents": [
            {
                "name": "promotional_email",
                "content": "Limited time offer! 70% off everything. Click here now!",
                "expected_rag_response": {
                    "average_confidence_level": 0.65,
                    "average_scam_probability": 0.45
                }
            },
            {
                "name": "tech_support_warning",
                "content": "Your computer may be infected. Download our security tool...",
                "expected_rag_response": {
                    "average_confidence_level": 0.58,
                    "average_scam_probability": 0.62
                }
            }
        ]
    }
}

# Error scenarios for testing robustness
ERROR_SCENARIOS = {
    "rag_service_unavailable": {
        "description": "RAG service is down or unresponsive",
        "mock_behavior": {
            "call_tool": {"rag-tools.call_rag": "ConnectionError: Service unavailable"},
            "expected_fallback": True
        }
    },
    
    "extraction_tool_failure": {
        "description": "Optional extraction tools fail",
        "mock_behavior": {
            "call_tool": {"extraction-tools.extract_link": "ParseError: Invalid format"},
            "expected_fallback": False  # Should continue with other tools
        }
    },
    
    "llm_rate_limit": {
        "description": "LLM service hits rate limits",
        "mock_behavior": {
            "chat_json": "RateLimitError: Too many requests",
            "expected_fallback": True
        }
    },
    
    "invalid_document": {
        "description": "Document processing fails",
        "mock_behavior": {
            "process_document": "ValueError: Invalid document format",
            "expected_fallback": True
        }
    }
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "max_processing_time_fast_path": 5.0,  # seconds for high confidence cases
    "max_processing_time_full_analysis": 30.0,  # seconds for uncertain cases
    "max_tool_calls": 15,
    "min_evidence_items": 1,
    "max_memory_usage": 100,  # MB (if monitoring memory)
    "required_metadata_fields": [
        "workflow_id",
        "total_time", 
        "evidence_gathered",
        "errors_encountered",
        "timestamp"
    ]
}

# Logging validation criteria
LOGGING_REQUIREMENTS = {
    "log_file_created": True,
    "json_file_created": True,
    "required_log_levels": ["INFO", "DEBUG", "ERROR"],
    "required_log_sections": [
        "WORKFLOW START",
        "Step 1: document_processing",
        "Step 2: rag_analysis",
        "WORKFLOW COMPLETE"
    ],
    "required_json_fields": [
        "workflow_id",
        "start_time",
        "steps",
        "decisions",
        "tool_calls",
        "final_result"
    ]
}

# Mock responses for different tools
TOOL_MOCK_RESPONSES = {
    "data-processor.extract_text": {
        "scam": "Extracted suspicious content with fraud indicators like money transfers and urgent requests",
        "legitimate": "Extracted legitimate business communication about meetings and standard operations", 
        "uncertain": "Extracted promotional content with mixed commercial and potentially suspicious elements"
    },
    
    "rag-tools.call_rag": {
        "high_confidence_scam": {
            "average_confidence_level": 0.95,
            "average_scam_probability": 0.89,
            "similar_documents": ["nigerian_scam_001", "inheritance_fraud_002"],
            "similarity_scores": [0.94, 0.91]
        },
        "high_confidence_legitimate": {
            "average_confidence_level": 0.93,
            "average_scam_probability": 0.11, 
            "similar_documents": ["business_email_001", "meeting_request_002"],
            "similarity_scores": [0.89, 0.86]
        },
        "uncertain": {
            "average_confidence_level": 0.65,
            "average_scam_probability": 0.45,
            "similar_documents": ["promotional_001"],
            "similarity_scores": [0.71]
        }
    },
    
    "extraction-tools.extract_link": {
        "scam": ["http://fake-bank-site.com/claim", "http://suspicious-domain.net"],
        "legitimate": ["https://company.com/portal", "https://legitimate-site.org"],
        "uncertain": ["http://deals-site.com/offer", "http://download-center.net"]
    },
    
    "extraction-tools.extract_number": {
        "scam": ["+234-555-FAKE", "$10,000,000", "$1,500"],
        "legitimate": ["(555) 123-4567", "$299.99", "Room 123"],
        "uncertain": ["1-800-SUPPORT", "70%", "$0"]
    },
    
    "extraction-tools.extract_organisation": {
        "scam": ["Nigerian Prince Foundation", "International Lottery Corp"],
        "legitimate": ["ABC Corporation", "Tech Solutions Inc"],
        "uncertain": ["Deals Online", "Support Center"]
    }
}

# LLM mock responses for uncertain cases
LLM_MOCK_RESPONSES = {
    "planner": {
        "uncertain_case": {
            "calls": [
                {"server": "extraction-tools", "tool": "extract_link", "args": {"text": "content"}},
                {"server": "extraction-tools", "tool": "extract_number", "args": {"text": "content"}},
                {"server": "extraction-tools", "tool": "extract_organisation", "args": {"text": "content"}}
            ]
        },
        "low_budget": {
            "calls": [
                {"server": "extraction-tools", "tool": "extract_link", "args": {"text": "content"}}
            ]
        }
    },
    
    "analyst": {
        "suspicious": {
            "is_scam": "suspicious",
            "confidence_level": 0.7,
            "scam_probability": 65.0,
            "explanation": "Mixed indicators detected with both legitimate and suspicious elements"
        },
        "likely_scam": {
            "is_scam": "scam",
            "confidence_level": 0.8,
            "scam_probability": 85.0,
            "explanation": "Strong scam indicators detected through analysis"
        }
    },
    
    "supervisor": {
        "valid_response": {
            "is_scam": "suspicious",
            "confidence_level": 0.7, 
            "scam_probability": 65.0,
            "explanation": "Supervised assessment with validated indicators"
        },
        "invalid_response": {
            "invalid": "response",
            "missing": "required_fields"
        }
    }
}

# Test validation rules
VALIDATION_RULES = {
    "required_result_fields": [
        "is_scam",
        "confidence_level", 
        "scam_probability",
        "explanation",
        "processing_metadata"
    ],
    
    "valid_is_scam_values": ["scam", "not_scam", "suspicious"],
    
    "confidence_level_range": (0.0, 1.0),
    "scam_probability_range": (0.0, 100.0),
    
    "metadata_validations": {
        "workflow_id": lambda x: isinstance(x, str) and len(x) > 0,
        "total_time": lambda x: isinstance(x, (int, float)) and x >= 0,
        "evidence_gathered": lambda x: isinstance(x, int) and x >= 0,
        "errors_encountered": lambda x: isinstance(x, int) and x >= 0
    }
}
