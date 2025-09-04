#!/usr/bin/env python3
"""
Quick test runner for assess_document workflow.
Run this script to test the fraud detection system.

Usage: python quick_test.py
"""
import sys
import os
import time

# Ensure test directory exists
os.makedirs("test/worker", exist_ok=True)

def test_logging_system():
    """Test just the logging system without external dependencies."""
    print("🧪 Testing Logging System")
    print("-" * 40)
    
    try:
        # Add the services/worker path to sys.path
        sys.path.insert(0, '/Users/chenxiangrui/Projects/SentinelAI/services/worker')
        
        # Import and test the assessment logger
        from worker.agents.assessment_logger import get_assessment_logger, reset_assessment_logger
        
        # Reset and get a new logger
        logger = reset_assessment_logger("test/worker")
        
        print("✅ Assessment logger imported successfully")
        print(f"   Workflow ID: {logger.workflow_id}")
        print(f"   Log directory: {logger.log_dir}")
        
        # Test workflow start
        test_document = {"type": "email", "content": "Test email content"}
        logger.log_workflow_start(test_document)
        print("✅ Workflow start logged")
        
        # Test step logging
        step1 = logger.log_step_start("test_step", "Testing step logging functionality")
        time.sleep(0.1)  # Simulate some processing time
        logger.log_step_end(step1, {"test_data": "success"})
        print("✅ Step logging completed")
        
        # Test decision point logging
        logger.log_decision_point("test_decision", "confidence > 0.8", True, {"route": "test_route"})
        print("✅ Decision point logged")
        
        # Test tool call logging
        logger.log_tool_call("test-server", "test-tool", {"arg1": "value1"}, output="test output")
        print("✅ Tool call logged")
        
        # Test performance metric
        logger.log_performance_metric("test_metric", 1.23, "seconds")
        print("✅ Performance metric logged")
        
        # Test workflow completion
        mock_result = {
            "is_scam": "not_scam",
            "confidence_level": 0.9,
            "scam_probability": 15.0,
            "explanation": "Test assessment result"
        }
        
        workflow_data = logger.complete_workflow(
            document_id="test_doc_001",
            final_result=mock_result,
            total_processing_time=2.5,
            evidence_count=3,
            error_count=0
        )
        print("✅ Workflow completion logged")
        
        # Check if files were created
        if os.path.exists(logger.log_file):
            print(f"✅ Log file created: {logger.log_file}")
            
            # Show a few lines from the log file
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                print("   Sample log entries:")
                for line in lines[:5]:
                    print(f"     {line.strip()}")
        else:
            print("❌ Log file not created")
        
        if os.path.exists(logger.json_file):
            print(f"✅ JSON file created: {logger.json_file}")
            
            # Check JSON structure
            import json
            with open(logger.json_file, 'r') as f:
                data = json.load(f)
                print(f"   JSON contains {len(data.get('steps', []))} steps")
                print(f"   JSON contains {len(data.get('tool_calls', []))} tool calls")
        else:
            print("❌ JSON file not created")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Error testing logging system: {e}")
        return False

def test_orchestrator_structure():
    """Test that orchestrator can be imported and has expected structure."""
    print("\n🧪 Testing Orchestrator Structure")
    print("-" * 40)
    
    try:
        # Import orchestrator
        from worker.agents.orchestrator import assess_document
        print("✅ Orchestrator imported successfully")
        
        # Check function signature
        import inspect
        sig = inspect.signature(assess_document)
        print(f"✅ assess_document signature: {sig}")
        
        # Check docstring
        if assess_document.__doc__:
            print("✅ Function has documentation")
            print(f"   Doc: {assess_document.__doc__[:100]}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import orchestrator: {e}")
        print("   This is expected if dependencies are not available")
        return False
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        return False

def test_mock_assessment():
    """Test a mock assessment without external dependencies."""
    print("\n🧪 Testing Mock Assessment")
    print("-" * 40)
    
    try:
        # Mock a complete assessment result structure
        mock_assessment_result = {
            "is_scam": "not_scam",
            "confidence_level": 0.9,
            "scam_probability": 15.0,
            "explanation": "Mock assessment - legitimate business email detected",
            "tool_evidence": [
                {
                    "tool": "data-processor.extract_text",
                    "output": "Extracted: Hi team, let's schedule our meeting for Friday..."
                },
                {
                    "tool": "rag-tools.call_rag", 
                    "output": {
                        "average_confidence_level": 0.9,
                        "average_scam_probability": 0.15,
                        "similar_documents": ["business_email_001"],
                        "similarity_scores": [0.88]
                    }
                }
            ],
            "processing_metadata": {
                "workflow_id": "mock_test_123",
                "total_time": 1.25,
                "evidence_gathered": 2,
                "errors_encountered": 0,
                "timestamp": time.time()
            }
        }
        
        # Validate the structure
        required_fields = ["is_scam", "confidence_level", "scam_probability", "explanation", "processing_metadata"]
        for field in required_fields:
            if field in mock_assessment_result:
                print(f"✅ Required field present: {field}")
            else:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate metadata
        metadata = mock_assessment_result["processing_metadata"]
        metadata_fields = ["workflow_id", "total_time", "evidence_gathered", "errors_encountered"]
        for field in metadata_fields:
            if field in metadata:
                print(f"✅ Metadata field present: {field}")
            else:
                print(f"❌ Missing metadata field: {field}")
                return False
        
        # Validate value ranges
        confidence = mock_assessment_result["confidence_level"]
        if 0 <= confidence <= 1:
            print(f"✅ Confidence level in valid range: {confidence}")
        else:
            print(f"❌ Invalid confidence level: {confidence}")
            return False
        
        scam_prob = mock_assessment_result["scam_probability"] 
        if 0 <= scam_prob <= 100:
            print(f"✅ Scam probability in valid range: {scam_prob}")
        else:
            print(f"❌ Invalid scam probability: {scam_prob}")
            return False
        
        is_scam = mock_assessment_result["is_scam"]
        valid_values = ["scam", "not_scam", "suspicious"]
        if is_scam in valid_values:
            print(f"✅ Valid is_scam value: {is_scam}")
        else:
            print(f"❌ Invalid is_scam value: {is_scam}")
            return False
        
        print("✅ Mock assessment structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error in mock assessment test: {e}")
        return False

def test_file_permissions():
    """Test that we can create files in the test directory."""
    print("\n🧪 Testing File Permissions")
    print("-" * 40)
    
    try:
        test_dir = "test/worker"
        test_file = os.path.join(test_dir, "permission_test.txt")
        
        # Try to write a test file
        with open(test_file, 'w') as f:
            f.write("Permission test successful\n")
        print(f"✅ Can write to test directory: {test_dir}")
        
        # Try to read the file
        with open(test_file, 'r') as f:
            content = f.read()
        print("✅ Can read from test directory")
        
        # Clean up
        os.remove(test_file)
        print("✅ Can delete from test directory")
        
        return True
        
    except Exception as e:
        print(f"❌ File permission error: {e}")
        return False

def main():
    """Run all quick tests."""
    print("🚀 Quick Test Suite for assess_document Workflow")
    print("=" * 60)
    print(f"Test directory: test/worker")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("File Permissions", test_file_permissions),
        ("Logging System", test_logging_system),
        ("Orchestrator Structure", test_orchestrator_structure), 
        ("Mock Assessment", test_mock_assessment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("QUICK TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")
    
    if passed == total:
        print("\n🎉 All quick tests passed!")
        print("\nNext steps:")
        print("1. Run full test suite: python test/worker/run_tests.py")
        print("2. Test with real documents")
        print("3. Monitor log files in test/worker/")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Check the error messages above for details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
